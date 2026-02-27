"""
retro_audit_screen.py - Tela de auditoria retroativa para PDFs existentes.
"""

from __future__ import annotations
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

from core.ai_auditor import auditar_transacao
from core.pdf_converter import pdf_to_images
from core.usage_manager import UsageManager
from ui.screens.result_screen import ResultScreen

class RetroAuditScreen(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.usage_manager = UsageManager()
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Container Central
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Verifica se há IA configurada
        settings = self.app.settings
        api_key = settings.get("api_keys", {}).get(settings.get("ai_provider", ""), "")
        
        if not api_key:
            self._show_no_ai_warning()
        else:
            self._show_upload_area()

    def _show_no_ai_warning(self):
        """Aviso amigável quando a IA não está configurada."""
        for w in self.main_container.winfo_children():
            w.destroy()
            
        warning_frame = ctk.CTkFrame(self.main_container, fg_color="#1A1A1A", corner_radius=15, border_width=1, border_color="#D32F2F")
        warning_frame.pack(expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            warning_frame,
            text="⚠️  Inteligência Artificial Não Configurada",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#EF5350"
        ).pack(pady=(30, 10), padx=40)
        
        ctk.CTkLabel(
            warning_frame,
            text="Para auditar documentos, você precisa primeiro configurar um provedor de IA\n(Gemini, OpenRouter, etc) e inserir sua Chave de API.",
            font=ctk.CTkFont(size=13),
            text_color="#B0BEC5",
            justify="center"
        ).pack(pady=10, padx=40)
        
        ctk.CTkButton(
            warning_frame,
            text="Ir para Configurações",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            command=self.app.show_settings
        ).pack(pady=(20, 30))

    def _show_upload_area(self):
        """Área principal de upload de PDF."""
        for w in self.main_container.winfo_children():
            w.destroy()
            
        header = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 30))
        
        ctk.CTkLabel(
            header,
            text="Auditoria Retroativa com IA",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#E3F2FD"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Suba um PDF de uma transação já realizada para que a IA faça a conferência completa.",
            font=ctk.CTkFont(size=13),
            text_color="#78909C"
        ).pack(anchor="w")

        # Drop Zone (Simulada)
        self.drop_zone = ctk.CTkFrame(self.main_container, fg_color="#0D1B2A", corner_radius=20, border_width=2, border_color="#1E3A5F", height=300)
        self.drop_zone.pack(fill="both", expand=True, pady=10)
        self.drop_zone.pack_propagate(False)

        ctk.CTkLabel(
            self.drop_zone,
            text="📄",
            font=ctk.CTkFont(size=64)
        ).pack(pady=(60, 10))

        ctk.CTkLabel(
            self.drop_zone,
            text="Clique para selecionar o arquivo PDF",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#4FC3F7"
        ).pack(pady=5)

        ctk.CTkLabel(
            self.drop_zone,
            text="O arquivo será processado e analisado pela IA configurada.",
            font=ctk.CTkFont(size=12),
            text_color="#546E7A"
        ).pack(pady=5)

        ctk.CTkButton(
            self.drop_zone,
            text="Selecionar Arquivo PDF",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            width=220,
            fg_color="#1565C0",
            hover_color="#1976D2",
            command=self._escolher_arquivo
        ).pack(pady=30)

    def _escolher_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecionar Transação em PDF",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if path:
            self._processar_auditoria(path)

    def _processar_auditoria(self, pdf_path: str):
        # Limpa tela e mostra progresso
        for w in self.main_container.winfo_children():
            w.destroy()
            
        loading_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        loading_frame.pack(expand=True)
        
        self.status_lbl = ctk.CTkLabel(
            loading_frame,
            text="Conversão: Processando PDF...",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#4FC3F7"
        )
        self.status_lbl.pack(pady=20)
        
        self.progress_bar = ctk.CTkProgressBar(loading_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        def run():
            try:
                # 1. Converter PDF em Imagens
                self.after(0, lambda: self.status_lbl.configure(text="Conversão: Extraindo imagens do PDF..."))
                images = pdf_to_images(pdf_path)
                
                if not images:
                    raise ValueError("Não foi possível extrair imagens deste PDF.")

                # 2. Verificar Limite Diário
                cache = getattr(self.app, "_license_cache", None)
                limite = int(cache.get("auditorias_limite", 0)) if cache else 0
                if limite > 0:
                    consumo = self.usage_manager.get_count()
                    if consumo >= limite:
                        self.after(0, lambda: messagebox.showwarning("Limite Excedido", "Você atingiu o limite diário de auditorias IA."))
                        self.after(0, self._show_upload_area)
                        return

                # 3. Auditar com IA
                self.after(0, lambda: self.status_lbl.configure(text="IA: Analisando documentos..."))
                self.usage_manager.increment()
                
                # Para auditoria retroativa, o 'tipo' é genérico se o PDF não informar
                result = auditar_transacao(
                    images=images,
                    tipo_transacao="Auditoria Retroativa (PDF)",
                    settings=self.app.settings
                )
                
                # 4. Mostrar Resultado
                # Criamos um "mock" de transação apenas para satisfazer a ResultScreen
                class MockTransaction:
                    def __init__(self, imgs):
                        self.imgs = imgs
                        self.nome_tipo = "Retroativa"
                    def todas_imagens(self): return self.imgs

                mock_tx = MockTransaction(images)
                self.after(0, lambda: self._show_result(mock_tx, result))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg, p=pdf_path: self._show_error_ui(m, p))

        threading.Thread(target=run, daemon=True).start()

    def _show_result(self, transaction, result):
        for w in self.winfo_children():
            w.destroy()
        
        # Reutilizamos a ResultScreen, mas customizada
        res_screen = ResultScreen(self, self.app, transaction=transaction)
        res_screen.grid(row=0, column=0, sticky="nsew")
        
        # Injetamos o resultado diretamente (pulando o _start_audit dela)
        res_screen.after(100, lambda: res_screen._show_result(result))
        
        # Adiciona botão de voltar
        btn_back = ctk.CTkButton(
            res_screen,
            text="⬅️  Nova Auditoria Retroativa",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#37474F",
            hover_color="#455A64",
            command=self._reset_screen
        )
        btn_back.place(x=40, y=30) # Fixado no topo

    def _show_error_ui(self, message: str, pdf_path: str):
        """Exibe interface de erro com opção de retry."""
        for w in self.main_container.winfo_children():
            w.destroy()
            
        err_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        err_frame.pack(expand=True)
        
        ctk.CTkLabel(err_frame, text="⚠️", font=ctk.CTkFont(size=48)).pack()
        ctk.CTkLabel(
            err_frame, 
            text="Falha na Auditoria", 
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFA726"
        ).pack(pady=4)
        
        ctk.CTkLabel(
            err_frame,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color="#78909C",
            wraplength=500
        ).pack(pady=10)
        
        ctk.CTkButton(
            err_frame,
            text="🔄  Tentar Novamente",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            width=240,
            fg_color="#1565C0",
            hover_color="#1976D2",
            command=lambda: self._processar_auditoria(pdf_path)
        ).pack(pady=8)
        
        ctk.CTkButton(
            err_frame,
            text="⬅️  Voltar",
            font=ctk.CTkFont(size=14),
            height=40,
            width=240,
            fg_color="transparent",
            border_width=1,
            border_color="#37474F",
            text_color="#78909C",
            command=self._show_upload_area
        ).pack(pady=4)

    def _reset_screen(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()
