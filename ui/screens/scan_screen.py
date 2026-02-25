"""
scan_screen.py - Tela de digitalização com navegação por etapas.
"""

import threading
import customtkinter as ctk
from PIL import Image, ImageTk
from core import scanner as scan_module
from core.transaction import Transaction


THUMB_SIZE = (120, 120)


class ScanScreen(ctk.CTkFrame):
    def __init__(self, parent, app, transaction: Transaction, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.transaction = transaction
        self._build()
        self._refresh()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Cabeçalho ─────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=40, pady=(32, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        self.lbl_tipo = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#4FC3F7",
        )
        self.lbl_tipo.grid(row=0, column=0, sticky="w")

        self.lbl_titulo = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#E3F2FD",
        )
        self.lbl_titulo.grid(row=1, column=0, sticky="w")

        self.lbl_desc = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="#78909C",
            wraplength=700,
            justify="left",
        )
        self.lbl_desc.grid(row=2, column=0, sticky="w", pady=(4, 0))

        # ── Barra de progresso ────────────────────────────────────────────────
        prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        prog_frame.grid(row=1, column=0, padx=40, pady=12, sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(prog_frame, height=8, corner_radius=4)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.progress_bar.set(0)

        self.lbl_progress = ctk.CTkLabel(
            prog_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#546E7A",
        )
        self.lbl_progress.grid(row=1, column=0, sticky="e")

        # ── Área de thumbs ────────────────────────────────────────────────────
        thumb_container = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=12)
        thumb_container.grid(row=2, column=0, padx=40, pady=8, sticky="nsew")
        thumb_container.grid_columnconfigure(0, weight=1)
        thumb_container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            thumb_container,
            text="Páginas digitalizadas:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#90A4AE",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        self.thumb_scroll = ctk.CTkScrollableFrame(
            thumb_container,
            fg_color="transparent",
            orientation="horizontal",
            height=170,
        )
        self.thumb_scroll.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 12))

        self.lbl_empty = ctk.CTkLabel(
            self.thumb_scroll,
            text="Nenhuma página digitalizada ainda.",
            font=ctk.CTkFont(size=12),
            text_color="#37474F",
        )
        self.lbl_empty.pack(pady=30)

        # ── Controles ─────────────────────────────────────────────────────────
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=3, column=0, padx=40, pady=16, sticky="ew")
        controls.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_scan = ctk.CTkButton(
            controls,
            text="📷   Escanear Página",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color="#1565C0",
            hover_color="#1976D2",
            command=self._do_scan,
        )
        self.btn_scan.grid(row=0, column=0, padx=8, sticky="ew")

        self.btn_import = ctk.CTkButton(
            controls,
            text="📁   Importar Arquivo",
            font=ctk.CTkFont(size=13),
            height=44,
            corner_radius=10,
            fg_color="#1E3A5F",
            hover_color="#263F6A",
            command=self._do_import,
        )
        self.btn_import.grid(row=0, column=1, padx=8, sticky="ew")

        self.btn_next = ctk.CTkButton(
            controls,
            text="Próxima Etapa  ▶",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color="#2E7D32",
            hover_color="#388E3C",
            state="disabled",
            command=self._pergunta_mais_paginas,
        )
        self.btn_next.grid(row=0, column=2, padx=8, sticky="ew")

        self._thumb_refs = []  # evita garbage collection das imagens

    # ── Atualização do estado visual ──────────────────────────────────────────

    def _refresh(self):
        """Atualiza a UI com o estado atual da etapa."""
        t = self.transaction
        etapa = t.etapa_atual

        self.lbl_tipo.configure(
            text=f"🏥  {t.nome_tipo}  •  Etapa {t.etapa_atual_index + 1} de {t.total_etapas}"
        )
        self.lbl_titulo.configure(text=f"{etapa.icone}  {etapa.titulo}")
        self.lbl_desc.configure(text=etapa.descricao)

        progresso = (t.etapa_atual_index) / t.total_etapas
        self.progress_bar.set(progresso)
        self.lbl_progress.configure(text=f"Etapa {t.etapa_atual_index + 1} / {t.total_etapas}")

        self._render_thumbs(etapa.imagens)
        self.btn_next.configure(state="normal" if etapa.tem_imagens else "disabled")

    def _render_thumbs(self, imagens):
        """Renderiza miniaturas das imagens atuais."""
        for widget in self.thumb_scroll.winfo_children():
            widget.destroy()
        self._thumb_refs.clear()

        if not imagens:
            self.lbl_empty = ctk.CTkLabel(
                self.thumb_scroll,
                text="Nenhuma página digitalizada ainda.",
                font=ctk.CTkFont(size=12),
                text_color="#37474F",
            )
            self.lbl_empty.pack(pady=30)
            return

        for i, img in enumerate(imagens):
            frame = ctk.CTkFrame(
                self.thumb_scroll,
                fg_color="#0D2137",
                corner_radius=8,
                border_width=1,
                border_color="#1E3450",
            )
            frame.pack(side="left", padx=6, pady=4)

            # Gera thumbnail
            thumb = img.copy()
            thumb.thumbnail(THUMB_SIZE, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(thumb)
            self._thumb_refs.append(tk_img)

            lbl_img = ctk.CTkLabel(frame, image=tk_img, text="")
            lbl_img.pack(padx=6, pady=(6, 2))

            ctk.CTkLabel(
                frame,
                text=f"Pág. {i + 1}",
                font=ctk.CTkFont(size=10),
                text_color="#546E7A",
            ).pack(pady=(0, 2))

            # Botão remover
            idx = i
            ctk.CTkButton(
                frame,
                text="✕",
                width=24,
                height=20,
                font=ctk.CTkFont(size=10),
                fg_color="#B71C1C",
                hover_color="#C62828",
                corner_radius=4,
                command=lambda i=idx: self._remover_imagem(i),
            ).pack(pady=(0, 6))

    # ── Ações ──────────────────────────────────────────────────────────────────

    def _do_scan(self):
        settings = self.app.settings
        scanner_name = settings.get("scanner_name", "")
        self.btn_scan.configure(state="disabled", text="⌛  Escaneando...")

        def run():
            img = None
            if scanner_name:
                img, err = scan_module.scan_page(scanner_name)
                if err:
                    print(f"[ScanScreen] Falha no scan direto: {err}. Tentando diálogo...")
            
            if img is None:
                img = scan_module.scan_with_dialog()
            
            self.after(0, lambda: self._on_image_captured(img))

        threading.Thread(target=run, daemon=True).start()

    def _do_import(self):
        img = scan_module.import_from_file(self)
        self._on_image_captured(img)

    def _on_image_captured(self, img):
        self.btn_scan.configure(state="normal", text="📷   Escanear Página")
        if img:
            img = scan_module.optimize_image(img)
            self.transaction.etapa_atual.adicionar_imagem(img)
            self._refresh()

    def _remover_imagem(self, index: int):
        self.transaction.etapa_atual.remover_imagem(index)
        self._refresh()

    def _pergunta_mais_paginas(self):
        """Abre diálogo perguntando se há mais páginas."""
        dialog = _MorePagesDialog(self, self.transaction.etapa_atual.titulo)
        self.wait_window(dialog)
        if dialog.result == "next":
            self._avancar_etapa()

    def _avancar_etapa(self):
        tem_proxima = self.transaction.avancar_etapa()
        if tem_proxima:
            self._refresh()
        else:
            # Digitalização concluída → auditoria
            self.app.show_result(self.transaction)


# ── Diálogo "Mais páginas?" ───────────────────────────────────────────────────

class _MorePagesDialog(ctk.CTkToplevel):
    def __init__(self, parent, etapa_titulo: str):
        super().__init__(parent)
        self.result = None
        self.title("")
        self.geometry("420x200")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus()

        # Centraliza
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - 210
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - 100
        self.geometry(f"+{px}+{py}")

        ctk.CTkLabel(
            self,
            text="Mais páginas?",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#E3F2FD",
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            self,
            text=f"Existem mais páginas para «{etapa_titulo}»?",
            font=ctk.CTkFont(size=12),
            text_color="#78909C",
            wraplength=360,
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame,
            text="✔   Sim, há mais páginas",
            width=170,
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=self._sim,
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            btn_frame,
            text="▶   Não, próxima etapa",
            width=170,
            fg_color="#2E7D32",
            hover_color="#388E3C",
            command=self._nao,
        ).grid(row=0, column=1, padx=8)

    def _sim(self):
        self.result = "more"
        self.destroy()

    def _nao(self):
        self.result = "next"
        self.destroy()
