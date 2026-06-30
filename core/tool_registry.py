from core.tool_adapter import UnimplementedToolAdapter


DEFAULT_UNIMPLEMENTED_TOOLS = {
    "web_reader": "Webページを読み取るReader。Ver1.4では未実装です。",
    "pdf_reader": "PDFを読み取るReader。Ver1.4では未実装です。",
    "image_reader": "画像を読み取るReader。Ver1.4では未実装です。",
    "youtube_reader": "YouTubeを読み取るReader。Ver1.4では未実装です。",
    "file_reader": "ローカルファイルを読み取るReader。Ver1.4では未実装です。",
    "document_creator": "Word / Excel / PDFなどを作成するTool。Ver1.4では未実装です。",
    "pc_operator": "PC操作を行うTool。Ver1.4では未実装です。",
}


class ToolRegistry:
    """Tool / Adapterを名前で管理する小さなRegistryです。"""

    def __init__(self, register_default_tools=True):
        self.adapters = {}

        if register_default_tools:
            self._register_default_unimplemented_tools()

    def register(self, adapter):
        """Adapterを登録します。"""
        self.adapters[adapter.name] = adapter
        return adapter

    def get(self, tool_name):
        """tool_nameに対応するAdapterを返します。未登録なら未実装Adapterを返します。"""
        adapter = self.adapters.get(tool_name)

        if adapter is not None:
            return adapter

        return UnimplementedToolAdapter(
            name=tool_name,
            description="未登録のToolです。Ver1.4では実行しません。",
        )

    def list_tools(self):
        """登録済みTool名の一覧を返します。"""
        return sorted(self.adapters.keys())

    def is_available(self, tool_name):
        """指定Toolが実行可能かを返します。"""
        return self.get(tool_name).is_available()

    def _register_default_unimplemented_tools(self):
        """将来接続する予定のToolを、未実装Adapterとして登録します。"""
        for tool_name, description in DEFAULT_UNIMPLEMENTED_TOOLS.items():
            self.register(
                UnimplementedToolAdapter(
                    name=tool_name,
                    description=description,
                )
            )
