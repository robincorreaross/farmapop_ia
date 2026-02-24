"""
license_screen.py - Tela de ativação de licença do FarmaPop IA.
Exibida ao iniciar o app quando não há licença válida.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import customtkinter as ctk
import tkinter.messagebox as mb

from core.license import (
    LicenseError,
    get_machine_id,
    salvar_licenca,
    validar_licenca,
)
from core.config import save_settings

if TYPE_CHECKING:
    from ui.app import App


class LicenseScreen(ctk.CTk):
    """
    Janela standalone de ativação de licença.
    Abre antes da janela principal do app.
    """

    def __init__(self, settings: dict, on_activate: object) -> None:  # type: ignore[type-arg]
        super().__init__()
        self.settings = settings
        self.on_activate = on_activate
        self.machine_id = get_machine_id()

        self.title("FarmaPop IA — Ativação de Licença")
        self.geometry("580x480")
        self.resizable(False, False)
        self.configure(fg_color="#0A1628")

        # Centraliza a janela
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 580) // 2
        y = (self.winfo_screenheight() - 480) // 2
        self.geometry(f"580x480+{x}+{y}")

        self._build()

    def _build(self) -> None:
        # ── Logo / título ──────────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="💊 FarmaPop IA",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#4FC3F7",
        ).pack(pady=(36, 0))

        ctk.CTkLabel(
            self,
            text="Ativação de Licença",
            font=ctk.CTkFont(size=14),
            text_color="#546E7A",
        ).pack(pady=(2, 24))

        # ── Card Machine ID ────────────────────────────────────────────────────
        mid_frame = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=12)
        mid_frame.pack(padx=48, fill="x")

        ctk.CTkLabel(
            mid_frame,
            text="🖥️  Identificador desta máquina",
            font=ctk.CTkFont(size=11),
            text_color="#546E7A",
        ).pack(anchor="w", padx=20, pady=(14, 0))

        mid_inner = ctk.CTkFrame(mid_frame, fg_color="#152030", corner_radius=8)
        mid_inner.pack(padx=16, pady=(4, 4), fill="x")

        self._mid_label = ctk.CTkLabel(
            mid_inner,
            text=self.machine_id,
            font=ctk.CTkFont(family="Courier New", size=18, weight="bold"),
            text_color="#E3F2FD",
        )
        self._mid_label.pack(side="left", padx=16, pady=10)

        ctk.CTkButton(
            mid_inner,
            text="📋 Copiar",
            width=90,
            height=32,
            corner_radius=6,
            fg_color="#1565C0",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=11),
            command=self._copiar_mid,
        ).pack(side="right", padx=10, pady=10)

        ctk.CTkLabel(
            mid_frame,
            text="Envie este código ao desenvolvedor para receber sua chave de licença.",
            font=ctk.CTkFont(size=11),
            text_color="#37474F",
            wraplength=460,
        ).pack(padx=20, pady=(0, 14))

        # ── Campo de licença ───────────────────────────────────────────────────
        ctk.CTkLabel(
            self,
            text="Cole sua chave de licença abaixo:",
            font=ctk.CTkFont(size=12),
            text_color="#78909C",
        ).pack(padx=48, anchor="w", pady=(20, 4))

        self._key_entry = ctk.CTkEntry(
            self,
            placeholder_text="FARMA-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
            font=ctk.CTkFont(family="Courier New", size=13),
            height=44,
            corner_radius=8,
        )
        self._key_entry.pack(padx=48, fill="x")

        # ── Botão ativar ───────────────────────────────────────────────────────
        ctk.CTkButton(
            self,
            text="🔑  Ativar Licença",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            corner_radius=10,
            fg_color="#0D47A1",
            hover_color="#1565C0",
            command=self._ativar,
        ).pack(padx=48, pady=16, fill="x")

        # ── Status ─────────────────────────────────────────────────────────────
        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#546E7A",
            wraplength=480,
        )
        self._status_label.pack(padx=48)

    def _copiar_mid(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.machine_id)
        self._status_label.configure(
            text="✅ Machine ID copiado para a área de transferência!",
            text_color="#66BB6A",
        )

    def _ativar(self) -> None:
        key = self._key_entry.get().strip()
        if not key:
            self._status_label.configure(
                text="⚠️  Cole a chave de licença antes de ativar.",
                text_color="#FFA726",
            )
            return

        try:
            info = validar_licenca(key)
            # Salva nas settings
            salvar_licenca(key, self.settings)
            save_settings(self.settings)
            dias = info["dias_restantes"]
            exp = info["expiry"]
            mb.showinfo(
                "Licença Ativada",
                f"✅ Licença ativada com sucesso!\n\n"
                f"Válida até: {exp}\n"
                f"Dias restantes: {dias}",
            )
            self.destroy()
            # Chama o callback para abrir o app principal
            self.on_activate()  # type: ignore[operator]
        except LicenseError as e:
            self._status_label.configure(
                text=f"❌  {e}",
                text_color="#EF5350",
            )


class LicenseExpiredScreen(LicenseScreen):
    """
    Variante da tela de ativação exibida quando a licença expirou.
    """

    def __init__(self, settings: dict, on_activate: object, msg_extra: str = "") -> None:
        self._msg_extra = msg_extra
        super().__init__(settings, on_activate)

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="⏰",
            font=ctk.CTkFont(size=48),
        ).pack(pady=(32, 0))

        ctk.CTkLabel(
            self,
            text="Licença Expirada",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#EF5350",
        ).pack(pady=(4, 0))

        if self._msg_extra:
            ctk.CTkLabel(
                self,
                text=self._msg_extra,
                font=ctk.CTkFont(size=12),
                text_color="#78909C",
                wraplength=460,
            ).pack(pady=(4, 16))

        super()._build()
