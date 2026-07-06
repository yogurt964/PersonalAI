from pathlib import Path

from core.file_path_extraction import extract_single_file_path_from_text
from core.tool_adapter import ToolAdapter, ToolResult
from core.vision_router import (
    VISION_BACKEND_LOCAL,
    VISION_BACKEND_OPENAI,
    choose_vision_backend,
    should_escalate_after_local_result,
)


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")

DEFAULT_VISION_PROMPT = (
    "この画像に写っているものを、日本語で詳しく説明してください。"
    "文字が写っている場合はその内容も書き出してください。"
    "分からない・確信が持てない部分は、断定せずその旨を伝えてください。"
)


def extract_image_path_from_text(text):
    """テキストから、ユーザーが指定した単一の画像ファイルパスを取り出します。

    ディレクトリ全体やワイルドカードは対象にせず、拡張子で終わる1つのパスだけを拾います。
    スペースを含むファイル名にも対応します。
    """
    return extract_single_file_path_from_text(text, IMAGE_EXTENSIONS)


class ImageReaderAdapter(ToolAdapter):
    """最小実用版のImage Reader Adapterです。

    ユーザーが明示した単一の画像ファイルだけを、確認後にローカルvisionモデルで解析します。
    ディレクトリ探索、ワイルドカード、書き込み、実行は一切行いません。
    現時点ではローカルvisionモデルのみ対応し、OpenAI visionは未接続です
    （vision_router.choose_vision_backend()が将来の切り替え口です）。
    """

    def __init__(
        self,
        max_file_bytes=20 * 1024 * 1024,
        max_text_chars=8000,
        model_name="qwen2.5vl:7b",
        vision_describer=None,
        openai_client_factory=None,
    ):
        super().__init__(
            name="image_reader",
            description="Describe a single local image file specified by the user using a local vision model.",
        )
        self.max_file_bytes = max_file_bytes
        self.max_text_chars = max_text_chars
        self.model_name = model_name
        # 自動checkでfakeのvision解析に差し替えられるようにします。
        self._vision_describer = vision_describer
        # 自動checkで、実際のOpenAI呼び出しをせずOpenAI分岐のロジックだけを検証できるようにします。
        self._openai_client_factory = openai_client_factory

    def is_available(self):
        return True

    def execute(self, request):
        """ToolRequestを受け取り、画像の説明文をToolResultとして返します。"""
        path_text = self._get_path_from_request(request)

        if not path_text:
            return ToolResult(
                success=False,
                message="読み取る画像ファイルパスが見つからないため、Image Readerは実行していません。",
                data=None,
                error="missing_path",
                executed=False,
            )

        path = Path(path_text)

        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            return ToolResult(
                success=False,
                message=(
                    "対応していない拡張子のため、Image Readerは実行していません。"
                    f"（対応拡張子: {', '.join(IMAGE_EXTENSIONS)}）"
                ),
                data={"path": path_text},
                error="unsupported_extension",
                executed=False,
            )

        if not path.exists():
            return ToolResult(
                success=False,
                message="指定されたファイルが見つからないため、Image Readerは実行していません。",
                data={"path": path_text},
                error="file_not_found",
                executed=False,
            )

        if not path.is_file():
            return ToolResult(
                success=False,
                message="指定されたパスはファイルではないため、Image Readerは実行していません。",
                data={"path": path_text},
                error="not_a_file",
                executed=False,
            )

        try:
            size_bytes = path.stat().st_size
        except OSError as error:
            return ToolResult(
                success=False,
                message="ファイル情報の取得に失敗しました。読めたふりはしません。",
                data={"path": path_text},
                error=str(error),
                executed=True,
            )

        if size_bytes > self.max_file_bytes:
            return ToolResult(
                success=False,
                message=(
                    "ファイルサイズが上限を超えているため、Image Readerは実行していません。"
                    f"（上限: {self.max_file_bytes}バイト）"
                ),
                data={"path": path_text, "size_bytes": size_bytes},
                error="file_too_large",
                executed=False,
            )

        original_input = self._get_original_input_from_request(request)
        initial_backend = choose_vision_backend(image_path=path_text, user_request_text=original_input)

        try:
            text, backend = self._describe_image(path, original_input, initial_backend)
        except Exception as error:
            return ToolResult(
                success=False,
                message="画像の解析に失敗しました。読めたふりはしません。（破損・非対応形式の可能性があります）",
                data={"path": path_text, "backend": initial_backend},
                error=str(error),
                executed=True,
            )

        truncated_text = len(text) > self.max_text_chars
        limited_text = text[: self.max_text_chars]

        if not limited_text.strip():
            return ToolResult(
                success=False,
                message="画像は開けましたが、説明を生成できませんでした。",
                data={"path": path_text, "size_bytes": size_bytes, "backend": backend},
                error="empty_text",
                executed=True,
            )

        return ToolResult(
            success=True,
            message="Image Readerで画像を解析しました。",
            data={
                "path": path_text,
                "resolved_path": str(path.resolve()),
                "file_name": path.name,
                "text": limited_text,
                "text_preview": limited_text[:500],
                "size_bytes": size_bytes,
                "backend": backend,
                "truncated": truncated_text,
            },
            error=None,
            executed=True,
        )

    def _describe_image(self, path, original_input, backend):
        """画像を解析し、(説明文, 実際に使ったバックエンド) を返します。

        backendが"local"の場合、まずローカルモデルで解析し、その結果が低信頼そうなら
        （ユーザーとの合意に基づき）PersonalAIの判断で自動的にOpenAIへ再解析を試みます。
        OpenAI側が予算超過・キー未設定などで使えない場合は、ローカルの結果をそのまま
        正直に返します（silent fallback）。
        """
        if self._vision_describer is not None:
            return self._vision_describer(path, original_input, backend), backend

        # 画像と一緒に具体的な質問が来ている場合、後続ターンでは画像そのものを
        # 再度見られないため、最初の解析でできるだけ詳しく答えておきます。
        prompt = f"{DEFAULT_VISION_PROMPT}\n\nユーザーからの元のメッセージ: {original_input}" if original_input else DEFAULT_VISION_PROMPT

        if backend == VISION_BACKEND_OPENAI:
            return self._call_openai_vision(path, prompt), VISION_BACKEND_OPENAI

        if backend != VISION_BACKEND_LOCAL:
            raise NotImplementedError(f"vision backend '{backend}' is not implemented yet.")

        local_text = self._call_local_vision(path, prompt)

        if should_escalate_after_local_result(local_text):
            try:
                openai_text = self._call_openai_vision(path, prompt)
                return (
                    f"{openai_text}\n\n"
                    "（ローカルモデルでの解析結果が不明瞭だったため、PersonalAIの判断でOpenAIに再解析させました）"
                ), VISION_BACKEND_OPENAI
            except Exception:
                # 予算超過・キー未設定などの場合は、ローカルの結果をそのまま正直に返します。
                return local_text, VISION_BACKEND_LOCAL

        return local_text, VISION_BACKEND_LOCAL

    def _call_local_vision(self, path, prompt):
        from ollama import chat

        response = chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt, "images": [str(path)]}],
        )

        return response.message.content

    def _call_openai_vision(self, path, prompt):
        from ai.openai_client import describe_image_with_openai

        return describe_image_with_openai(
            str(path),
            prompt,
            client_factory=self._openai_client_factory,
        )

    def _get_path_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        path_text = input_data.get("path")

        if path_text:
            return str(path_text).strip()

        original_input = input_data.get("original_input", "")
        return extract_image_path_from_text(original_input)

    def _get_original_input_from_request(self, request):
        input_data = getattr(request, "input_data", {}) or {}
        return input_data.get("original_input", "") or ""
