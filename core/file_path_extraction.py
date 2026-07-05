import re


# Windowsのファイル名に使えない文字（保存時にOSが弾く文字）。
# パスの終端（拡張子の手前）を探すときの「ここまでは同じパスの一部」の判定に使います。
_WINDOWS_INVALID_PATH_CHARS = r'<>"|?*\r\n'


def _build_quoted_pattern(extensions):
    ext_group = "|".join(re.escape(ext.lstrip(".")) for ext in extensions)
    return re.compile(
        rf'"([^"]+\.(?:{ext_group}))"|\'([^\']+\.(?:{ext_group}))\'',
        re.IGNORECASE,
    )


def _build_windows_absolute_pattern(extensions):
    ext_group = "|".join(re.escape(ext.lstrip(".")) for ext in extensions)
    # ドライブレター始まりのパスは、スペースや括弧を含んでいても1つのパスとして扱います。
    # （例: "curry_shop_reading_test (1).txt" のような重複ダウンロードのファイル名）
    return re.compile(
        rf'[A-Za-z]:\\[^{_WINDOWS_INVALID_PATH_CHARS}]+?\.(?:{ext_group})',
        re.IGNORECASE,
    )


def _build_bare_pattern(extensions):
    ext_group = "|".join(re.escape(ext.lstrip(".")) for ext in extensions)
    return re.compile(rf'(\S+\.(?:{ext_group}))', re.IGNORECASE)


def extract_single_file_path_from_text(text, extensions):
    """テキストから、ユーザーが指定した単一ファイルのパスを取り出します。

    優先順位:
    1. 引用符で囲まれたパス（スペースを含んでいてもよい）
    2. ドライブレター始まりのWindows絶対パス（スペースや括弧を含んでいてもよい）
    3. スペースを含まない素のパス（相対パスなど）

    ディレクトリ全体やワイルドカードは対象にせず、指定された拡張子で終わる
    1つのパスだけを拾います。
    """
    if not text:
        return None

    text = str(text)

    quoted_match = _build_quoted_pattern(extensions).search(text)

    if quoted_match:
        return next(group for group in quoted_match.groups() if group)

    windows_match = _build_windows_absolute_pattern(extensions).search(text)

    if windows_match:
        return windows_match.group(0)

    bare_match = _build_bare_pattern(extensions).search(text)

    if bare_match:
        return bare_match.group(1)

    return None
