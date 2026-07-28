from __future__ import annotations

import re
from collections.abc import Mapping

from .branding import PHRASE_TRANSLATIONS, language_prefix
from .persian_translations import PERSIAN_TRANSLATIONS

_TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
_TAG_NAME_RE = re.compile(r"^<\s*/?\s*([a-zA-Z0-9:-]+)")
_TRANSLATABLE_ATTRIBUTE_RE = re.compile(
    r"(?P<prefix>\b(?:placeholder|title|aria-label)\s*=\s*)"
    r"(?P<quote>[\"'])(?P<value>.*?)(?P=quote)",
    flags=re.IGNORECASE,
)
_VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def _replace_phrases(text: str, translations: Mapping[str, str]) -> str:
    for source in sorted(translations, key=len, reverse=True):
        replacement = translations[source]
        if not source or source == replacement:
            continue

        left_boundary = r"(?<!\w)" if source[0].isalnum() else ""
        right_boundary = r"(?!\w)" if source[-1].isalnum() else ""
        pattern = f"{left_boundary}{re.escape(source)}{right_boundary}"
        text = re.sub(pattern, lambda _match, value=replacement: value, text)
    return text


def _translate_safe_attributes(tag: str, translations: Mapping[str, str]) -> str:
    """Translate user-facing attributes without touching form values or URLs."""

    def replace(match: re.Match[str]) -> str:
        translated = _replace_phrases(match.group("value"), translations)
        return f'{match.group("prefix")}{match.group("quote")}{translated}{match.group("quote")}'

    return _TRANSLATABLE_ATTRIBUTE_RE.sub(replace, tag)


def translate_html_content(
    content: str,
    language_code: str,
    custom: Mapping[str, str] | None = None,
) -> str:
    """Translate rendered interface copy while preserving user-entered values.

    Translation is limited to visible text nodes and safe interface attributes
    such as ``placeholder``, ``title`` and ``aria-label``. Input values, links,
    CSS, JavaScript and elements marked with ``translate=\"no\"`` are never
    changed.
    """

    language = language_prefix(language_code)
    translations = dict(PHRASE_TRANSLATIONS.get(language, {}))
    if language == "fa":
        translations.update(PERSIAN_TRANSLATIONS)
    if custom:
        translations.update({str(key): str(value) for key, value in custom.items()})
    if not translations:
        return content

    output: list[str] = []
    skip_stack: list[bool] = []

    for part in _TAG_SPLIT_RE.split(content):
        if not part:
            continue
        if not part.startswith("<"):
            output.append(part if any(skip_stack) else _replace_phrases(part, translations))
            continue

        stripped = part.lstrip()
        match = _TAG_NAME_RE.match(stripped)
        if not match or stripped.startswith("<!") or stripped.startswith("<?"):
            output.append(part)
            continue

        tag_name = match.group(1).lower()
        is_closing = bool(re.match(r"^<\s*/", stripped))
        is_self_closing = stripped.rstrip().endswith("/>") or tag_name in _VOID_TAGS

        if is_closing:
            output.append(part)
            if skip_stack:
                skip_stack.pop()
            continue

        parent_skipped = any(skip_stack)
        normalized = stripped.lower()
        element_skipped = (
            parent_skipped
            or tag_name in {"script", "style", "code", "pre"}
            or 'translate="no"' in normalized
            or "translate='no'" in normalized
            or "data-no-translate" in normalized
        )

        output.append(part if element_skipped else _translate_safe_attributes(part, translations))
        if not is_self_closing:
            skip_stack.append(element_skipped)

    return "".join(output)
