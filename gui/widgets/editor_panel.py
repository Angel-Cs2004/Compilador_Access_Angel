import customtkinter as ctk
from typing import Callable

from gui.theme import COLORS as C, EXAMPLE_CODE


class EditorPanel(ctk.CTkFrame):
    def __init__(self, parent, on_cursor_change: Callable[[int, int, str], None] | None = None, **kwargs):
        super().__init__(
            parent, corner_radius=10,
            fg_color=C["bg_panel"], border_width=1, border_color=C["border"],
            **kwargs,
        )
        self._on_cursor_change = on_cursor_change
        self._current_line = 1
        self._mode = "NORMAL"
        self._visual_anchor_line: int | None = None
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_editor()

    def _build_header(self):
        header = ctk.CTkFrame(self, corner_radius=8, fg_color=C["bg_bar"], height=38)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="  ✦ Código fuente  (.acc)",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=C["accent"],
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self._lbl_file = ctk.CTkLabel(
            header, text="nuevo archivo",
            font=ctk.CTkFont(size=11), text_color=C["txt_dim"],
        )
        self._lbl_file.grid(row=0, column=1, padx=12, pady=10, sticky="e")

        self._lbl_mode = ctk.CTkLabel(
            header, text="NORMAL",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=C["ok"],
        )
        self._lbl_mode.grid(row=0, column=2, padx=(0, 12), pady=10, sticky="e")

    def _build_editor(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self._line_numbers = ctk.CTkTextbox(
            body,
            width=48,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none", corner_radius=8, state="disabled",
            fg_color=C["bg_bar"], text_color=C["txt_dim"],
            border_width=1, border_color=C["border"],
            scrollbar_button_color=C["border"],
            activate_scrollbars=False,
        )
        self._line_numbers.grid(row=0, column=0, sticky="ns", padx=(0, 4))

        self._textbox = ctk.CTkTextbox(
            body,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="none", corner_radius=8,
            fg_color=C["bg_code"], text_color=C["txt"],
            border_width=1, border_color=C["border"],
            scrollbar_button_color=C["border"],
        )
        self._textbox.grid(row=0, column=1, sticky="nsew")
        self._textbox.insert("1.0", EXAMPLE_CODE)
        self._configure_tags()
        self._bind_editor_events()
        self._refresh_accessibility_state()

    def _configure_tags(self) -> None:
        for widget in (self._textbox, self._line_numbers):
            try:
                widget.tag_config("current_line", background="#1e3a5f")
            except Exception:
                pass
        try:
            self._textbox.tag_config("visual_line", background="#3b0764")
        except Exception:
            pass

    def _bind_editor_events(self) -> None:
        for sequence in (
            "<KeyRelease>", "<ButtonRelease-1>", "<MouseWheel>",
            "<FocusIn>", "<Configure>",
        ):
            self._textbox.bind(sequence, lambda _event: self.after(0, self._refresh_accessibility_state))

    def _refresh_accessibility_state(self) -> None:
        self._update_line_numbers()
        self._highlight_current_line()
        self._sync_line_numbers_scroll()
        line = self.get_current_line_number()
        total = self.get_total_lines()
        text = self.get_line_text(line)
        if self._on_cursor_change:
            self._on_cursor_change(line, total, text)

    def _update_line_numbers(self) -> None:
        total = self.get_total_lines()
        width = max(2, len(str(total)))
        numbers = "\n".join(f"{line:>{width}}" for line in range(1, total + 1))
        self._line_numbers.configure(state="normal")
        self._line_numbers.delete("1.0", "end")
        self._line_numbers.insert("1.0", numbers)
        self._line_numbers.configure(state="disabled")

    def _highlight_current_line(self) -> None:
        line = self.get_current_line_number()
        for widget in (self._textbox, self._line_numbers):
            try:
                widget.tag_remove("current_line", "1.0", "end")
                widget.tag_add("current_line", f"{line}.0", f"{line}.end")
            except Exception:
                pass
        self._highlight_visual_selection()

    def _highlight_visual_selection(self) -> None:
        try:
            self._textbox.tag_remove("visual_line", "1.0", "end")
            if self._mode != "VISUAL" or self._visual_anchor_line is None:
                return
            current = self.get_current_line_number()
            start = min(self._visual_anchor_line, current)
            end = max(self._visual_anchor_line, current)
            self._textbox.tag_add("visual_line", f"{start}.0", f"{end}.end")
        except Exception:
            pass

    def _sync_line_numbers_scroll(self) -> None:
        try:
            first, _last = self._textbox.yview()
            self._line_numbers.yview_moveto(first)
        except Exception:
            pass

    # ── public API ───────────────────────────────────────────────────────────

    def get_code(self) -> str:
        return self._textbox.get("1.0", "end-1c")

    def set_code(self, text: str) -> None:
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", text)
        self._refresh_accessibility_state()

    def insert_text(self, text: str) -> None:
        self._textbox.insert("end", text)
        self._refresh_accessibility_state()

    def clear(self) -> None:
        self._textbox.delete("1.0", "end")
        self._refresh_accessibility_state()

    def undo_last_line(self) -> None:
        lines = self.get_code().split("\n")
        if lines:
            lines.pop()
            self.set_code("\n".join(lines))

    def set_filename(self, name: str) -> None:
        self._lbl_file.configure(text=name)

    def focus_editor(self) -> None:
        self._textbox.focus_set()

    def bind_editor_key(self, sequence: str, command: Callable) -> None:
        self._textbox.bind(sequence, command)

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        if mode == "VISUAL" and self._visual_anchor_line is None:
            self._visual_anchor_line = self.get_current_line_number()
        if mode != "VISUAL":
            self._visual_anchor_line = None
        color = {"NORMAL": C["ok"], "INSERT": C["accent"], "VISUAL": C["ia"]}.get(mode, C["txt"])
        self._lbl_mode.configure(text=mode, text_color=color)
        self._refresh_accessibility_state()

    def start_visual_selection(self) -> None:
        self._visual_anchor_line = self.get_current_line_number()
        self.set_mode("VISUAL")

    def get_total_lines(self) -> int:
        return max(1, len(self.get_code().split("\n")))

    def get_current_line_number(self) -> int:
        try:
            return int(self._textbox.index("insert").split(".")[0])
        except Exception:
            return 1

    def get_line_text(self, line: int | None = None) -> str:
        line = line or self.get_current_line_number()
        return self._textbox.get(f"{line}.0", f"{line}.end")

    def go_to_line(self, line: int) -> tuple[int, int, str]:
        total = self.get_total_lines()
        target = min(max(1, line), total)
        self._textbox.mark_set("insert", f"{target}.0")
        self._textbox.see(f"{target}.0")
        self.focus_editor()
        self._refresh_accessibility_state()
        return target, total, self.get_line_text(target)

    def go_next_line(self) -> tuple[int, int, str]:
        return self.go_to_line(self.get_current_line_number() + 1)

    def go_previous_line(self) -> tuple[int, int, str]:
        return self.go_to_line(self.get_current_line_number() - 1)
