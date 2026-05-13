"""Terminal UI for paged menus with an info column.

Intentionally independent of ROS / joy code. The controller wires button
events to the public API (move_up, move_down, next_page, prev_page,
select, render). Swapping to a real GUI means replacing this module while
keeping the same surface.

Layout:
    Main  Shift                         <- pages, current one underlined

    > connect                           | info line 0
      disconnect                        | info line 1
      teleop start                      | info line 2
      teleop stop                       | info line 3
"""

import sys
from dataclasses import dataclass
from typing import Callable, Optional, Union


@dataclass
class MenuItem:
    label: Union[str, Callable[[], str]]
    action: Callable[[], None]


class Page:
    def __init__(self, name: str, items: list[MenuItem], initial_cursor: int = 0):
        self.name = name
        self.items = items
        self.cursor = initial_cursor % len(items) if items else 0

    def move_up(self) -> None:
        if self.items:
            self.cursor = (self.cursor - 1) % len(self.items)

    def move_down(self) -> None:
        if self.items:
            self.cursor = (self.cursor + 1) % len(self.items)

    def select(self) -> None:
        if self.items:
            self.items[self.cursor].action()


class TerminalUI:
    MENU_WIDTH = 28

    def __init__(
        self,
        pages: list[Page],
        info_provider: Optional[Callable[[], list[str]]] = None,
        out=sys.stdout,
    ):
        if not pages:
            raise ValueError("TerminalUI requires at least one page")
        self.pages = pages
        self.page_idx = 0
        self.info_provider = info_provider or (lambda: [])
        self.out = out
        self._started = False

    @property
    def current_page(self) -> Page:
        return self.pages[self.page_idx]

    def next_page(self) -> None:
        self.page_idx = (self.page_idx + 1) % len(self.pages)

    def prev_page(self) -> None:
        self.page_idx = (self.page_idx - 1) % len(self.pages)

    def move_up(self) -> None:
        self.current_page.move_up()

    def move_down(self) -> None:
        self.current_page.move_down()

    def select(self) -> None:
        self.current_page.select()

    def start(self) -> None:
        self.out.write("\033[?25l\033[2J\033[H")
        self.out.flush()
        self._started = True

    def stop(self) -> None:
        self.out.write("\033[?25h\n")
        self.out.flush()
        self._started = False

    def render(self) -> None:
        if not self._started:
            self.start()
        info = self.info_provider()
        items = self.current_page.items
        rows = max(len(items), len(info))

        buf = ["\033[H"]
        buf.append(self._render_header() + "\033[K\n")
        buf.append("\033[K\n")
        for i in range(rows):
            left = self._render_menu_row(i)
            right = info[i] if i < len(info) else ""
            buf.append(f"{left} | {right}\033[K\n")
        buf.append("\033[J")
        self.out.write("".join(buf))
        self.out.flush()

    def _render_header(self) -> str:
        parts = []
        for i, page in enumerate(self.pages):
            name = page.name
            if i == self.page_idx:
                parts.append(f"\033[4m{name}\033[24m")
            else:
                parts.append(name)
        return "  ".join(parts)

    def _render_menu_row(self, i: int) -> str:
        items = self.current_page.items
        if i >= len(items):
            return " " * self.MENU_WIDTH
        label = items[i].label
        text = label() if callable(label) else label
        prefix = "> " if i == self.current_page.cursor else "  "
        return f"{prefix}{text}".ljust(self.MENU_WIDTH)
