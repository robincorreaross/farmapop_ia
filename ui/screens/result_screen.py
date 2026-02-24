"""
result_screen.py - Tela de auditoria IA e resultado (aprovado/reprovado).
Inclui modo de Auditoria Manual para revisão de falsos positivos.
"""

from __future__ import annotations

import subprocess
import threading
import tkinter.messagebox as mb
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import customtkinter as ctk

from core.ai_auditor import AuditResult, auditar_transacao
from core.pdf_generator import gerar_pdf
from core.transaction import Transaction

if TYPE_CHECKING:
    from ui.app import App


class ResultScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent: ctk.CTkFrame,
        app: "App",
        transaction: Transaction,
        **kwargs: object,
    ) -> None:
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.transaction = transaction
        self.audit_result: Optional[AuditResult] = None
        # Estado da auditoria manual: True=confirmado erro, False=falso positivo
        self._manual_votes: List[Optional[bool]] = []
        self._build()
        self._start_audit()

    # ── Layout base ─────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=40, pady=(32, 0), sticky="ew")

        ctk.CTkLabel(
            header,
            text="Auditoria IA",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#E3F2FD",
        ).pack(anchor="w")

        self._header_sub = ctk.CTkLabel(
            header,
            text="Analisando os documentos digitalizados conforme as regras do PFPB...",
            font=ctk.CTkFont(size=13),
            text_color="#78909C",
        )
        self._header_sub.pack(anchor="w")

        self.center = ctk.CTkFrame(self, fg_color="#0D1B2A", corner_radius=16)
        self.center.grid(row=1, column=0, padx=40, pady=24, sticky="nsew")
        self.center.grid_columnconfigure(0, weight=1)
        self.center.grid_rowconfigure(0, weight=1)

        self._show_loading()

    def _clear_center(self) -> None:
        for w in self.center.winfo_children():
            w.destroy()

    def _set_subtitle(self, text: str) -> None:
        self._header_sub.configure(text=text)

    # ── Loading ─────────────────────────────────────────────────────────────────

    def _show_loading(self) -> None:
        self._clear_center()
        frame = ctk.CTkFrame(self.center, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="🔍", font=ctk.CTkFont(size=54)).pack(pady=8)

        ctk.CTkLabel(
            frame,
            text="Analisando documentos...",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#4FC3F7",
        ).pack()

        ctk.CTkLabel(
            frame,
            text="Isso pode levar alguns segundos.",
            font=ctk.CTkFont(size=12),
            text_color="#546E7A",
        ).pack(pady=4)

        self.progress = ctk.CTkProgressBar(frame, mode="indeterminate", width=280)
        self.progress.pack(pady=12)
        self.progress.start()

    # ── Auditoria IA ────────────────────────────────────────────────────────────

    def _start_audit(self) -> None:
        def run() -> None:
            try:
                images = self.transaction.todas_imagens()
                result = auditar_transacao(
                    images=images,
                    tipo_transacao=self.transaction.nome_tipo,
                    settings=self.app.settings,
                )
                self.after(0, lambda: self._show_result(result))
            except Exception as e:
                self.after(0, lambda: self._show_error(str(e)))

        threading.Thread(target=run, daemon=True).start()

    def _show_result(self, result: AuditResult) -> None:
        self.audit_result = result
        self._clear_center()
        if result.aprovado:
            self._set_subtitle("Auditoria concluída com sucesso.")
            self._show_approved(result)
        else:
            self._set_subtitle(
                "Irregularidades detectadas. Revise os erros ou inicie uma Auditoria Manual."
            )
            self._show_rejected(result)

    # ── Aprovado ─────────────────────────────────────────────────────────────────

    def _show_approved(self, result: AuditResult, manual: bool = False) -> None:
        frame = ctk.CTkFrame(self.center, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="✅", font=ctk.CTkFont(size=64)).pack(pady=(0, 8))

        label_text = "Aprovado pela Auditoria Manual!" if manual else "Documentação Aprovada!"
        ctk.CTkLabel(
            frame,
            text=label_text,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#66BB6A",
        ).pack()

        if manual:
            ctk.CTkLabel(
                frame,
                text="Todos os erros apontados pela IA foram descartados pelo auditor.",
                font=ctk.CTkFont(size=12),
                text_color="#78909C",
                wraplength=440,
            ).pack(pady=(4, 0))

        dados_frame = ctk.CTkFrame(frame, fg_color="#0A2210", corner_radius=10)
        dados_frame.pack(pady=16, ipadx=20, ipady=12)

        ctk.CTkLabel(
            dados_frame,
            text=f"🔖  Autorização: {result.autorizacao or 'Não identificada'}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#A5D6A7",
        ).pack(padx=24, pady=(8, 2))

        ctk.CTkLabel(
            dados_frame,
            text=f"📅  Data: {result.data or 'Não identificada'}",
            font=ctk.CTkFont(size=13),
            text_color="#A5D6A7",
        ).pack(padx=24, pady=(2, 8))

        if result.observacoes and not manual:
            ctk.CTkLabel(
                frame,
                text=f"ℹ️  {result.observacoes}",
                font=ctk.CTkFont(size=11),
                text_color="#546E7A",
                wraplength=480,
            ).pack(pady=(0, 12))

        ctk.CTkButton(
            frame,
            text="💾   Salvar PDF",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=50,
            width=240,
            corner_radius=10,
            fg_color="#2E7D32",
            hover_color="#388E3C",
            command=self._salvar_pdf,
        ).pack(pady=8)

        ctk.CTkButton(
            frame,
            text="Nova Transação",
            font=ctk.CTkFont(size=12),
            height=36,
            width=180,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="#37474F",
            hover_color="#1E3A5F",
            text_color="#78909C",
            command=self.app.show_home,
        ).pack(pady=4)

    # ── Reprovado ────────────────────────────────────────────────────────────────

    def _show_rejected(self, result: AuditResult) -> None:
        frame = ctk.CTkScrollableFrame(self.center, fg_color="transparent")
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        ctk.CTkLabel(frame, text="❌", font=ctk.CTkFont(size=54)).pack(pady=(24, 4))

        ctk.CTkLabel(
            frame,
            text="Documentação Reprovada",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#EF5350",
        ).pack()

        ctk.CTkLabel(
            frame,
            text="Foram encontradas irregularidades nos documentos. Verifique os erros abaixo.",
            font=ctk.CTkFont(size=12),
            text_color="#78909C",
            wraplength=560,
        ).pack(pady=(4, 16))

        # Lista de erros
        erros_frame = ctk.CTkFrame(frame, fg_color="#1A0A0A", corner_radius=10)
        erros_frame.pack(padx=40, pady=4, fill="x")

        ctk.CTkLabel(
            erros_frame,
            text="⚠️  Erros Encontrados:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#EF9A9A",
        ).pack(anchor="w", padx=20, pady=(12, 4))

        for i, erro in enumerate(result.erros, 1):
            ctk.CTkLabel(
                erros_frame,
                text=f"  {i}.  {erro}",
                font=ctk.CTkFont(size=12),
                text_color="#FFCDD2",
                wraplength=540,
                justify="left",
            ).pack(anchor="w", padx=20, pady=2)

        if result.observacoes:
            ctk.CTkLabel(
                erros_frame,
                text=f"\n📝 {result.observacoes}",
                font=ctk.CTkFont(size=11),
                text_color="#78909C",
                wraplength=520,
            ).pack(padx=20, pady=(4, 12))

        # Botão Auditoria Manual (destaque)
        manual_frame = ctk.CTkFrame(frame, fg_color="#0D1E35", corner_radius=10)
        manual_frame.pack(padx=40, pady=(16, 4), fill="x")

        ctk.CTkLabel(
            manual_frame,
            text="📋  Auditoria Manual",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#4FC3F7",
        ).pack(anchor="w", padx=20, pady=(12, 0))

        ctk.CTkLabel(
            manual_frame,
            text=(
                "A IA pode produzir falsos positivos. Use a auditoria manual para revisar "
                "cada erro apontado e decidir se é válido ou não."
            ),
            font=ctk.CTkFont(size=11),
            text_color="#546E7A",
            wraplength=500,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(2, 8))

        ctk.CTkButton(
            manual_frame,
            text="📋   Iniciar Auditoria Manual",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=42,
            corner_radius=8,
            fg_color="#1565C0",
            hover_color="#1976D2",
            command=self._iniciar_auditoria_manual,
        ).pack(padx=20, pady=(0, 14), fill="x")

        # Botões de ação
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="🗑️   Cancelar e Descartar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            width=220,
            corner_radius=10,
            fg_color="#B71C1C",
            hover_color="#C62828",
            command=self._cancelar,
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            btn_frame,
            text="↩   Voltar e Revisar",
            font=ctk.CTkFont(size=13),
            height=44,
            width=180,
            corner_radius=10,
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=lambda: self.app.show_scan(self.transaction),
        ).grid(row=0, column=1, padx=8)

    # ── Auditoria Manual ─────────────────────────────────────────────────────────

    def _iniciar_auditoria_manual(self) -> None:
        """Inicia o fluxo de revisão manual de cada erro apontado pela IA."""
        if not self.audit_result or not self.audit_result.erros:
            return

        # Reinicia os votos
        self._manual_votes = [None] * len(self.audit_result.erros)
        self._set_subtitle("Auditoria Manual: revise cada erro apontado pela IA.")
        self._show_manual_review(index=0)

    def _show_manual_review(self, index: int) -> None:
        """Mostra a tela de revisão para o erro na posição `index`."""
        result = self.audit_result
        if result is None:
            return

        erros = result.erros
        total = len(erros)

        self._clear_center()
        frame = ctk.CTkFrame(self.center, fg_color="transparent")
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Progresso ──────────────────────────────────────────────────────────
        prog_frame = ctk.CTkFrame(frame, fg_color="transparent")
        prog_frame.pack(padx=40, pady=(24, 0), fill="x")

        ctk.CTkLabel(
            prog_frame,
            text=f"📋  Auditoria Manual  —  Erro {index + 1} de {total}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#4FC3F7",
        ).pack(anchor="w")

        progress_bar = ctk.CTkProgressBar(prog_frame, width=500)
        progress_bar.pack(anchor="w", pady=(6, 0))
        progress_bar.set((index) / total)

        # Indicadores de status dos votos (bolinhas)
        dots_frame = ctk.CTkFrame(prog_frame, fg_color="transparent")
        dots_frame.pack(anchor="w", pady=(4, 0))
        for i in range(total):
            vote = self._manual_votes[i]
            if vote is None:
                color = "#37474F"   # pendente
                symbol = "●"
            elif vote:
                color = "#EF5350"   # confirmado erro
                symbol = "✗"
            else:
                color = "#66BB6A"   # falso positivo descartado
                symbol = "✓"
            ctk.CTkLabel(
                dots_frame,
                text=symbol,
                font=ctk.CTkFont(size=14),
                text_color=color,
                width=22,
            ).pack(side="left", padx=2)

        # ── Erro atual ─────────────────────────────────────────────────────────
        erro_outer = ctk.CTkFrame(frame, fg_color="#0D1B2A", corner_radius=14)
        erro_outer.pack(padx=40, pady=20, fill="x")

        ctk.CTkLabel(
            erro_outer,
            text="Irregularidade apontada pela IA:",
            font=ctk.CTkFont(size=11),
            text_color="#546E7A",
        ).pack(anchor="w", padx=24, pady=(16, 0))

        ctk.CTkLabel(
            erro_outer,
            text=f"⚠️  {erros[index]}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFCDD2",
            wraplength=580,
            justify="left",
        ).pack(anchor="w", padx=24, pady=(6, 16))

        # ── Instrução ──────────────────────────────────────────────────────────
        ctk.CTkLabel(
            frame,
            text="Verifique os documentos digitalizados e decida:",
            font=ctk.CTkFont(size=12),
            text_color="#78909C",
        ).pack(pady=(0, 12))

        # ── Botões de decisão ──────────────────────────────────────────────────
        decision_frame = ctk.CTkFrame(frame, fg_color="transparent")
        decision_frame.pack(pady=4)

        ctk.CTkButton(
            decision_frame,
            text="✅  Erro Correto — Confirmar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=52,
            width=260,
            corner_radius=10,
            fg_color="#7B1FA2",
            hover_color="#8E24AA",
            command=lambda: self._votar(index, True),
        ).grid(row=0, column=0, padx=12, pady=4)

        ctk.CTkButton(
            decision_frame,
            text="❌  Falso Positivo — Ignorar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=52,
            width=260,
            corner_radius=10,
            fg_color="#1B5E20",
            hover_color="#2E7D32",
            command=lambda: self._votar(index, False),
        ).grid(row=0, column=1, padx=12, pady=4)

        # ── Navegação (voltar) ─────────────────────────────────────────────────
        nav_frame = ctk.CTkFrame(frame, fg_color="transparent")
        nav_frame.pack(pady=16)

        if index > 0:
            ctk.CTkButton(
                nav_frame,
                text="← Anterior",
                font=ctk.CTkFont(size=12),
                height=34,
                width=140,
                corner_radius=8,
                fg_color="transparent",
                border_width=1,
                border_color="#37474F",
                hover_color="#1E3A5F",
                text_color="#78909C",
                command=lambda: self._show_manual_review(index - 1),
            ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            nav_frame,
            text="Cancelar Auditoria Manual",
            font=ctk.CTkFont(size=12),
            height=34,
            width=200,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color="#37474F",
            hover_color="#3E1C1C",
            text_color="#78909C",
            command=self._cancelar_auditoria_manual,
        ).grid(row=0, column=1, padx=8)

    def _votar(self, index: int, confirmado: bool) -> None:
        """Registra o voto para o erro `index` e avança ou finaliza."""
        self._manual_votes[index] = confirmado
        result = self.audit_result
        if result is None:
            return
        next_index = index + 1
        if next_index < len(result.erros):
            self._show_manual_review(next_index)
        else:
            self._finalizar_auditoria_manual()

    def _finalizar_auditoria_manual(self) -> None:
        """Calcula resultado final com base nos votos e exibe tela adequada."""
        result = self.audit_result
        if result is None:
            return

        # Erros confirmados como reais
        erros_confirmados = [
            erro
            for erro, vote in zip(result.erros, self._manual_votes)
            if vote is True
        ]

        self._clear_center()

        if erros_confirmados:
            # Ainda há erros reais → reprovado, mas mostrando apenas os confirmados
            self._set_subtitle(
                f"Auditoria Manual concluída: {len(erros_confirmados)} erro(s) confirmado(s)."
            )
            self._show_manual_rejected(result, erros_confirmados)
        else:
            # Todos descartados como falsos positivos → aprovado!
            self._set_subtitle("Auditoria Manual: todos os erros descartados. Aprovado!")
            self._show_approved(result, manual=True)

    def _show_manual_rejected(
        self, result: AuditResult, erros_confirmados: List[str]
    ) -> None:
        """Tela de reprovação após auditoria manual (apenas erros confirmados)."""
        frame = ctk.CTkScrollableFrame(self.center, fg_color="transparent")
        frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        ctk.CTkLabel(frame, text="🔎", font=ctk.CTkFont(size=54)).pack(pady=(24, 4))

        ctk.CTkLabel(
            frame,
            text="Reprovado após Auditoria Manual",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#EF5350",
        ).pack()

        total_ia = len(result.erros)
        descartados = total_ia - len(erros_confirmados)
        ctk.CTkLabel(
            frame,
            text=(
                f"{descartados} de {total_ia} erro(s) da IA foram descartados como falsos positivos.\n"
                f"{len(erros_confirmados)} erro(s) foram confirmados pelo auditor."
            ),
            font=ctk.CTkFont(size=12),
            text_color="#78909C",
            wraplength=560,
            justify="center",
        ).pack(pady=(4, 16))

        erros_frame = ctk.CTkFrame(frame, fg_color="#1A0A0A", corner_radius=10)
        erros_frame.pack(padx=40, pady=4, fill="x")

        ctk.CTkLabel(
            erros_frame,
            text="❌  Erros Confirmados pelo Auditor:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#EF9A9A",
        ).pack(anchor="w", padx=20, pady=(12, 4))

        for i, erro in enumerate(erros_confirmados, 1):
            ctk.CTkLabel(
                erros_frame,
                text=f"  {i}.  {erro}",
                font=ctk.CTkFont(size=12),
                text_color="#FFCDD2",
                wraplength=540,
                justify="left",
            ).pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(
            erros_frame, text="", font=ctk.CTkFont(size=4)
        ).pack(pady=(0, 8))

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="🗑️   Cancelar e Descartar",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
            width=220,
            corner_radius=10,
            fg_color="#B71C1C",
            hover_color="#C62828",
            command=self._cancelar,
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            btn_frame,
            text="↩   Voltar e Revisar",
            font=ctk.CTkFont(size=13),
            height=44,
            width=180,
            corner_radius=10,
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=lambda: self.app.show_scan(self.transaction),
        ).grid(row=0, column=1, padx=8)

    def _cancelar_auditoria_manual(self) -> None:
        """Cancela auditoria manual e volta para a tela de reprovação."""
        self._set_subtitle(
            "Irregularidades detectadas. Revise os erros ou inicie uma Auditoria Manual."
        )
        self._clear_center()
        if self.audit_result:
            self._show_rejected(self.audit_result)

    # ── Erro de conexão ──────────────────────────────────────────────────────────

    def _show_error(self, message: str) -> None:
        self._clear_center()
        frame = ctk.CTkFrame(self.center, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(frame, text="⚠️", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(
            frame,
            text="Erro ao contatar a IA",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFA726",
        ).pack(pady=4)
        ctk.CTkLabel(
            frame,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color="#78909C",
            wraplength=480,
        ).pack(pady=8)

        ctk.CTkButton(
            frame,
            text="⚙️  Verificar Configurações",
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=self.app.show_settings,
        ).pack(pady=4)

        ctk.CTkButton(
            frame,
            text="↩  Voltar",
            fg_color="transparent",
            border_width=1,
            border_color="#37474F",
            hover_color="#1E3A5F",
            text_color="#78909C",
            command=lambda: self.app.show_scan(self.transaction),
        ).pack(pady=4)

    # ── Ações ────────────────────────────────────────────────────────────────────

    def _salvar_pdf(self) -> None:
        result = self.audit_result
        if result is None:
            return
        settings = self.app.settings
        output_folder = settings.get(
            "output_folder", str(Path.home() / "Documents" / "FarmaPop")
        )

        autorizacao = result.autorizacao or "SEM_AUTORIZACAO"
        data = result.data or "SEM_DATA"

        try:
            images = self.transaction.todas_imagens()
            path = gerar_pdf(images, autorizacao, data, output_folder)
            mb.showinfo(
                "PDF Salvo",
                f"Arquivo salvo com sucesso:\n{path}",
            )
            subprocess.Popen(f'explorer /select,"{path}"')
            self.app.show_home()
        except Exception as e:
            mb.showerror("Erro ao salvar PDF", str(e))

    def _cancelar(self) -> None:
        if mb.askyesno(
            "Cancelar transação",
            "Tem certeza? Todas as imagens digitalizadas serão descartadas.",
        ):
            self.app.show_home()
