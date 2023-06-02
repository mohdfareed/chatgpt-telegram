"""Formatter of messages sent by the bot."""

# unsupported telegram tags:
# spoiler: using simpler syntax `<tg-spoiler>`
# code blocks: using `<code>` as it is copyable in telegram
# emoji: can't guarantee id validity

_inline = r"(?<![@#\\\w]){0}(.+?){0}(?!\w)"

_markdown_patterns = dict(
    underlined=_inline.format(r"__"),
    italic=_inline.format(r"_"),  # only after underlined
    code=_inline.format(r"```"),
    mono=_inline.format(r"`"),  # only after code blocks
    bold=_inline.format(r"\*"),
    strikethrough=_inline.format(r"~"),
    spoiler=_inline.format(r"\|\|"),
    link=r"(?<![@#\w])\[(.+?)\]\((.+?)\)(?!\w)",
)

_html_syntax = dict(
    bold=r"<b>\1</b>",
    italic=r"<i>\1</i>",
    underlined=r"<u>\1</u>",
    strikethrough=r"<s>\1</s>",
    spoiler=r"<tg-spoiler>\1</tg-spoiler>",
    link=r'<a href="\2">\1</a>',
    mono=r"<code>\1</code>",
    code=r"<code>\1</code>",
)

_valid_tags = [
    # bold
    "b",
    "strong",
    # italic
    "i",
    "em",
    # underline
    "u",
    "ins",
    # strikethrough
    "s",
    "strike",
    "del",
    # spoiler
    "tg-spoiler",  # spoiler
    # link
    "a",
    # code
    "code",
    "pre",  # not preferred
]

_valid_attrs = {
    "a": ["href"],
    "code": ["class"],
}  # can't verify emoji-id validity, therefore not supported


def markdown_to_html(text: str) -> str:
    """Convert markdown text to HTML."""
    return _parse_html(_parse_markdown(text))


def _parse_html(text):
    import html

    from bs4 import BeautifulSoup

    for tag in (html_soup := BeautifulSoup(text, "html.parser")).find_all():
        # escape invalid tags
        if tag.name not in _valid_tags:
            tag.replace_with(html.unescape(str(tag)))
            continue

        # escape tag if it has invalid attributes
        for attr in tag.attrs:
            if attr not in _valid_attrs.get(tag.name, []):
                tag.replace_with(html.unescape(str(tag)))

    return str(html_soup)


def _parse_markdown(text):
    import re

    for tag, pattern in _markdown_patterns.items():
        # replace markdown with html syntax
        text = re.sub(pattern, _html_syntax[tag], text)

    return text
