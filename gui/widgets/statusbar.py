import customtkinter as ctk

from gui.theme import COLORS as C


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, has_binary: bool, **kwargs):
        super().__init__(parent, corner_radius=0, height=30, fg_color=C["bg_bar"], **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(2, weight=1)

        initial_color = C["warn"] if not has_binary else C["txt_dim"]
        initial_msg   = "Compilador no encontrado — ejecuta 'make'" if not has_binary else "Listo"

        self._dot = ctk.CTkLabel(self, text="●", font=ctk.CTkFont(size=13),
                                 text_color=initial_color)
        self._dot.grid(row=0, column=0, padx=(14, 4), pady=5, sticky="w")

        self._lbl = ctk.CTkLabel(self, text=initial_msg, font=ctk.CTkFont(size=11),
                                 text_color=initial_color)
        self._lbl.grid(row=0, column=1, pady=5, sticky="w")

        ctk.CTkLabel(
            self,
            text="NORMAL: j/k línea, i insertar, v visual, Enter IA línea, Shift+I IA todo, Esc normal/detener  ",
            font=ctk.CTkFont(size=10), text_color=C["txt_dim"],
        ).grid(row=0, column=2, pady=5, sticky="e")

    def set(self, level: str, message: str) -> None:
        color = {"ok": C["ok"], "err": C["err"],
                 "warn": C["warn"], "idle": C["txt_dim"]}.get(level, C["txt_dim"])
        self._dot.configure(text_color=color)
        self._lbl.configure(text=f"  {message}", text_color=color)
