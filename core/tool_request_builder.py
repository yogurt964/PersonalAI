import re
from dataclasses import dataclass
from typing import Optional

from core.reading_keywords import (
    BASE_PC_OPERATION_KEYWORDS,
    BASE_READING_INTENT_KEYWORDS,
    EXCEL_DOCUMENT_KEYWORDS,
    PDF_TO_FILE_KEYWORDS,
    WORD_DOCUMENT_KEYWORDS,
)
from core.tool_adapter import ToolRequest


@dataclass
class ToolRequestDecision:
    """入力からToolRequestを作るべきかを表す判定結果です。"""

    requires_tool: bool
    tool_request: Optional[ToolRequest]
    reason: str
    capability_name: Optional[str] = None
    should_execute: bool = False


def infer_tool_name_and_action(user_input, input_analysis=None, capability_result=None):
    """ユーザー入力から、必要そうなTool名とactionを推定します。

    Ver1.6ではキーワードベースのdry-runです。
    ここではToolの実行は行わず、ToolRequestを作るための材料だけを返します。
    """
    text = str(user_input or "").strip()
    lowered_text = text.lower()

    capability_match = _infer_from_capability_result(capability_result)

    if capability_match is not None:
        return capability_match

    if not text:
        return _no_tool("空の入力のため、Toolは必要ありません。")

    if _requires_pc_operation(text, lowered_text):
        risk_level = "critical" if _contains_any(text, ["削除", "消して", "delete", "remove"]) else "high"
        return _tool_info(
            "pc_operator",
            "operate_pc",
            risk_level,
            True,
            "PC操作が必要そうな入力です。",
            "pc_operation_required",
        )

    if _requires_document_creation(text, lowered_text, input_analysis):
        return _tool_info(
            "document_creator",
            "create_document",
            "medium",
            True,
            "文書や資料の作成が必要そうな入力です。",
            "document_creation_required",
        )

    if _requires_youtube_reader(text, lowered_text, input_analysis):
        return _tool_info(
            "youtube_reader",
            "summarize_video",
            "medium",
            True,
            "YouTube Readerが必要そうな入力です。",
            "youtube_read_required",
        )

    if _requires_image_reader(text, lowered_text):
        return _tool_info(
            "image_reader",
            "analyze_image",
            "medium",
            True,
            "Image Readerが必要そうな入力です。",
            "image_read_required",
        )

    if _requires_pdf_reader(text, lowered_text):
        return _tool_info(
            "pdf_reader",
            "read_pdf",
            "medium",
            True,
            "PDF Readerが必要そうな入力です。",
            "pdf_read_required",
        )

    if _requires_file_reader(text, lowered_text):
        return _tool_info(
            "file_reader",
            "read_file",
            "medium",
            True,
            "File Readerが必要そうな入力です。",
            "file_read_required",
        )

    if _requires_web_reader(text, lowered_text, input_analysis):
        return _tool_info(
            "web_reader",
            "read_url",
            "medium",
            True,
            "Web Readerが必要そうな入力です。",
            "web_read_required",
        )

    return _no_tool("通常会話として扱えるため、ToolRequestは作りません。")


def build_tool_request_decision(user_input, input_analysis=None, capability_result=None):
    """入力からToolRequestDecisionを作ります。

    通常会話ではToolRequestを作りません。
    Reader系やToolが必要そうな入力ではToolRequestだけを作り、実行はしません。
    """
    inferred = infer_tool_name_and_action(user_input, input_analysis, capability_result)

    if not inferred["requires_tool"]:
        return ToolRequestDecision(
            requires_tool=False,
            tool_request=None,
            reason=inferred["reason"],
            capability_name=inferred.get("capability_name"),
            should_execute=False,
        )

    tool_request = ToolRequest(
        tool_name=inferred["tool_name"],
        action=inferred["action"],
        input_data={
            "original_input": str(user_input or ""),
            "input_analysis": input_analysis,
            "capability_result": capability_result,
        },
        requires_permission=inferred["requires_permission"],
        risk_level=inferred["risk_level"],
    )

    return ToolRequestDecision(
        requires_tool=True,
        tool_request=tool_request,
        reason=inferred["reason"],
        capability_name=inferred.get("capability_name"),
        should_execute=False,
    )


def _infer_from_capability_result(capability_result):
    """CapabilityManagerの結果からTool候補が分かる場合に利用します。"""
    primary_capability = _get_value(capability_result, "primary_capability")
    missing_capabilities = _get_value(capability_result, "missing_capabilities", []) or []

    if "pc_operator" in missing_capabilities or primary_capability == "pc_operation_required":
        return _tool_info(
            "pc_operator",
            "operate_pc",
            "high",
            True,
            "CapabilityManagerがPC操作の必要性を示しています。",
            "pc_operation_required",
        )

    capability_map = {
        "document_creation_required": (
            "document_creator",
            "create_document",
            "medium",
            "CapabilityManagerが文書作成Toolの必要性を示しています。",
        ),
        "youtube_read_required": (
            "youtube_reader",
            "summarize_video",
            "medium",
            "CapabilityManagerがYouTube Readerの必要性を示しています。",
        ),
        "web_read_required": (
            "web_reader",
            "read_url",
            "medium",
            "CapabilityManagerがWeb Readerの必要性を示しています。",
        ),
        "pdf_read_required": (
            "pdf_reader",
            "read_pdf",
            "medium",
            "CapabilityManagerがPDF Readerの必要性を示しています。",
        ),
        "image_read_required": (
            "image_reader",
            "analyze_image",
            "medium",
            "CapabilityManagerがImage Readerの必要性を示しています。",
        ),
        "file_read_required": (
            "file_reader",
            "read_file",
            "medium",
            "CapabilityManagerがFile Readerの必要性を示しています。",
        ),
    }

    if primary_capability in capability_map:
        tool_name, action, risk_level, reason = capability_map[primary_capability]
        return _tool_info(tool_name, action, risk_level, True, reason, primary_capability)

    return None


def _requires_youtube_reader(text, lowered_text, input_analysis):
    input_type = _get_value(input_analysis, "input_type")

    if input_type == "youtube" or "youtube.com" in lowered_text or "youtu.be" in lowered_text:
        return True

    return _contains_any(text, ["YouTube", "youtube", "動画"]) and _has_reading_intent(text)


def _requires_web_reader(text, lowered_text, input_analysis):
    input_type = _get_value(input_analysis, "input_type")

    if input_type == "url":
        return True

    if "http://" in lowered_text or "https://" in lowered_text or "URL" in text:
        return True

    return _contains_any(text, ["Webページ", "webページ", "サイト", "記事"]) and _has_reading_intent(text)


def _requires_pdf_reader(text, lowered_text):
    if _is_pdf_creation(text, lowered_text):
        return False

    if ".pdf" in lowered_text:
        return True

    return ("PDF" in text or "pdf" in lowered_text) and _has_reading_intent(text)


def _requires_image_reader(text, lowered_text):
    if re.search(r"\.(png|jpg|jpeg|gif|webp)(\s|$|\?)", lowered_text):
        return True

    return _contains_any(text, ["画像", "写真", "スクショ", "スクリーンショット", "image"]) and _has_reading_intent(text)


def _requires_file_reader(text, lowered_text):
    return (
        _contains_any(text, ["ファイル", "添付ファイル", "ローカルファイル", "file"])
        and _has_reading_intent(text)
        and not _requires_document_creation(text, lowered_text, None)
    )


def _requires_document_creation(text, lowered_text, input_analysis):
    task_type = _get_value(input_analysis, "task_type")
    requires_file_creation = _get_value(input_analysis, "requires_file_creation", False)

    if task_type == "create_document" or requires_file_creation:
        return True

    return _contains_any(
        text,
        [
            *WORD_DOCUMENT_KEYWORDS,
            *EXCEL_DOCUMENT_KEYWORDS,
            "文書作成",
            "資料作成",
            "レポート作成",
            "PDF作成",
            "pdf作成",
            "PDFを作",
            "pdfを作",
            *PDF_TO_FILE_KEYWORDS,
            "文書を作",
            "資料を作",
        ],
    )


def _requires_pc_operation(text, lowered_text):
    return _contains_any(
        text,
        [
            *BASE_PC_OPERATION_KEYWORDS,
            "クリック",
            "キーボード",
            "フォルダ操作",
            "ファイルを削除",
            "削除して",
            "VS Codeを操作",
            "vscodeを操作",
            "delete",
            "remove",
        ],
    )


def _is_pdf_creation(text, lowered_text):
    return _contains_any(text, ["PDF作成", "pdf作成", "PDFを作", "pdfを作", "PDFにして", "pdfにして"])


def _has_reading_intent(text):
    return _contains_any(text, [*BASE_READING_INTENT_KEYWORDS, "確認", "分析"])


def _tool_info(tool_name, action, risk_level, requires_permission, reason, capability_name):
    return {
        "requires_tool": True,
        "tool_name": tool_name,
        "action": action,
        "risk_level": risk_level,
        "requires_permission": requires_permission,
        "reason": reason,
        "capability_name": capability_name,
    }


def _no_tool(reason):
    return {
        "requires_tool": False,
        "tool_name": None,
        "action": None,
        "risk_level": "none",
        "requires_permission": False,
        "reason": reason,
        "capability_name": None,
    }


def _get_value(obj, key, default=None):
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)
