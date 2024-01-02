from typing import cast

import structlog
from typing_extensions import TypedDict


class NoteContent(TypedDict):
    id: str
    type: str
    value: str
    children: list["NoteContent"]


class HeadingContent(NoteContent):
    level: int


def to_markdown(content: NoteContent, level: int = 0, indent_width: int = 4) -> str:
    logger = structlog.get_logger("note_content.to_markdown")
    match content:
        case {"type": "RootNode", "children": children}:
            return "".join(to_markdown(child) for child in children)
        case {"type": "BlockNode", "value": value, "children": children}:
            line = f"{' ' * indent_width * level}{value}"
            children = "".join(
                to_markdown(child, level=level + 1, indent_width=indent_width)
                for child in children
            )
            return line + "\n" + children
        case {"type": "HeadingNode", "value": value, "children": children}:
            heading_level = cast(dict[str, int], content)["level"]
            line = f"{' ' * indent_width * level}{'#' * heading_level} {value}"
            children = "".join(
                to_markdown(child, level=level + 1, indent_width=indent_width)
                for child in children
            )
            return line + "\n" + children
        case {"type": "ListItemNode", "value": value, "children": children}:
            line = f"{' ' * indent_width * level}- {value}"
            children = "".join(
                to_markdown(child, level=level + 1, indent_width=indent_width)
                for child in children
            )
            return line + "\n" + children
        case {"type": type}:
            logger.warning(f"Unknown type {type}")
            return ""
        case _:
            logger.warning(f"Unknown content {content}")
            return ""


DEFAULT_NOTE_CONTENT: NoteContent = {
    "id": "root",
    "type": "RootNode",
    "value": "",
    "children": [],
}
