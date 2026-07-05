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


def _iter_pattern_matches(pattern, text):
    for match in pattern.finditer(text):
        groups = match.groups()
        value = next((group for group in groups if group), None) if groups else match.group(0)

        if value:
            yield match.start(), match.end(), value


def extract_multiple_file_paths_from_text(text, extensions, max_files=5):
    """テキストから、ユーザーが名指しした複数ファイルのパスを、出現順に取り出します。

    extract_single_file_path_from_textと同じ優先順位（引用符 > Windows絶対パス > 素のパス）で
    パスを探し、既に見つかった範囲と重ならないものだけを拾います。
    重複を除いて出現順に並べ、max_files件を超える場合は先頭からその件数までに切り詰めます。

    ディレクトリ全体やワイルドカードには対応しません。ユーザーが明示的に列挙した
    ファイルパスだけを対象にします。
    """
    if not text:
        return []

    text = str(text)
    consumed_spans = []
    ordered_paths = []
    seen = set()

    patterns = (
        _build_quoted_pattern(extensions),
        _build_windows_absolute_pattern(extensions),
        _build_bare_pattern(extensions),
    )

    for pattern in patterns:
        for start, end, value in _iter_pattern_matches(pattern, text):
            if any(start < span_end and end > span_start for span_start, span_end in consumed_spans):
                continue

            consumed_spans.append((start, end))

            if value not in seen:
                seen.add(value)
                ordered_paths.append((start, value))

    ordered_paths.sort(key=lambda item: item[0])
    return [path for _, path in ordered_paths][:max_files]
