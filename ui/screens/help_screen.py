"""
help_screen.py - Tela de Ajuda e Suporte do FarmaPop IA.
Exibe MachineID, validade da licença e contato do administrador.
"""

from __future__ import annotations

import webbrowser
from typing import TYPE_CHECKING

import customtkinter as ctk

from core.license import get_machine_id, carregar_licenca, validar_licenca

if TYPE_CHECKING:
    from ui.app import App


class HelpScreen(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.machine_id = get_machine_id()
        
        # v1.1.7: Usa o cache global do App para evitar lag de rede ao abrir a tela
        # Se o cache ainda não existir (raro), tenta validar de forma rápida
        if self.app._license_cache:
            self.license_info = self.app._license_cache
        else:
            settings = self.app.settings
            key = carregar_licenca(settings)
            try:
                # Fallback síncrono apenas se o cache estiver vazio
                self.license_info = validar_licenca(key or "")
                self.app._license_cache = self.license_info
            except:
                self.license_info = None

        self._build()

    def _build(self) -> None:
        # ── Scrollable Container Principal ───────────────────────────────────
        # Usamos um CTkScrollableFrame para garantir que caiba em qualquer resolução
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.scroll.grid_columnconfigure(0, weight=1)

        # ── Container Centralizado (Max 700px) ──────────────────────────────
        # Criamos um frame que não preenche todo o X, mas tem um limite
        self.main_container = ctk.CTkFrame(self.scroll, fg_color="transparent", width=700)
        self.main_container.grid(row=0, column=0, pady=20, padx=20)
        self.main_container.grid_propagate(True) # container cresce com filhos mas grid dá o limite

        # Título
        ctk.CTkLabel(
            self.main_container,
            text="Central de Ajuda e Suporte",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#4FC3F7"
        ).pack(pady=(20, 30))

        # ── Card de Licenciamento ──────────────────────────────────────────
        license_card = ctk.CTkFrame(self.main_container, fg_color="#0D1B2A", corner_radius=15, border_width=1, border_color="#1E3A5F")
        license_card.pack(fill="x", pady=10)

        ctk.CTkLabel(
            license_card,
            text="💳  Informações de Licenciamento",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#90A4AE"
        ).pack(anchor="w", padx=25, pady=(20, 15))

        # MachineID Box
        mid_box = ctk.CTkFrame(license_card, fg_color="#152030", corner_radius=10)
        mid_box.pack(padx=20, pady=5, fill="x")
        
        ctk.CTkLabel(
            mid_box,
            text="Machine ID:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#546E7A"
        ).pack(side="left", padx=15, pady=12)

        ctk.CTkLabel(
            mid_box,
            text=self.machine_id,
            font=ctk.CTkFont(family="Courier New", size=15, weight="bold"),
            text_color="#E3F2FD"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            mid_box,
            text="📋 Copiar",
            width=90,
            height=32,
            fg_color="#1565C0",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._copiar_mid
        ).pack(side="right", padx=15)

        # Status/Expiração Row
        status_row = ctk.CTkFrame(license_card, fg_color="transparent")
        status_row.pack(padx=25, pady=(15, 20), fill="x")

        exp = "Desconhecida"
        metodo = "Pendente"
        if self.license_info:
            exp = self.license_info.get("expiry", "N/A")
            metodo = "Online" if self.license_info.get("metodo") == "online" else "Offline"

        ctk.CTkLabel(
            status_row,
            text=f"📅  Vencimento: {exp}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#81C784" if self.license_info else "#EF5350"
        ).pack(side="left")

        ctk.CTkLabel(
            status_row,
            text=f"Tipo: {metodo}",
            font=ctk.CTkFont(size=11),
            text_color="#546E7A"
        ).pack(side="right")

        # ── Card de Suporte ───────────────────────────────────────────────
        support_card = ctk.CTkFrame(self.main_container, fg_color="#0D1B2A", corner_radius=15, border_width=1, border_color="#1E3A5F")
        support_card.pack(fill="x", pady=20)

        ctk.CTkLabel(
            support_card,
            text="🛠️  Suporte Técnico",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#90A4AE"
        ).pack(anchor="w", padx=25, pady=(20, 10))

        ctk.CTkLabel(
            support_card,
            text="Precisa de renovação ou ajuda técnica? Chame nosso time diretamente pelo WhatsApp no botão abaixo.",
            font=ctk.CTkFont(size=12),
            text_color="#78909C",
            wraplength=600,
            justify="left"
        ).pack(anchor="w", padx=25, pady=(0, 20))

        # Botão WhatsApp centralizado e com largura controlada
        btn_zap = ctk.CTkButton(
            support_card,
            text="💬  Chamar Robinson no WhatsApp",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            width=400,
            corner_radius=12,
            fg_color="#2E7D32",
            hover_color="#388E3C",
            text_color="white",
            command=self._abrir_whatsapp
        )
        btn_zap.pack(pady=(0, 25))

    def _copiar_mid(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.machine_id)
        from tkinter import messagebox
        messagebox.showinfo("Copiado", "✅ Machine ID copiado! Pode enviar pelo WhatsApp.")

    def _abrir_whatsapp(self) -> None:
        msg = f"Olá Robinson, preciso de suporte no FarmaPop IA (Machine ID: {self.machine_id})"
        import urllib.parse
        url = f"https://wa.me/5516991080895?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)
