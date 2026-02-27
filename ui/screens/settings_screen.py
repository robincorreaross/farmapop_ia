"""
settings_screen.py - Tela de configurações: IA, Scanner e Armazenamento.
"""

import threading
import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
from pathlib import Path
from core.config import AVAILABLE_MODELS
from core import scanner as scan_module
from core.ai_auditor import testar_conexao


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        # Cópia local das configurações para edição
        import copy
        self.settings = copy.deepcopy(app.settings)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=40, pady=(32, 8), sticky="ew")

        ctk.CTkLabel(
            header,
            text="Configurações",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#E3F2FD",
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Gerencie as configurações de IA, scanner e armazenamento.",
            font=ctk.CTkFont(size=13),
            text_color="#78909C",
        ).pack(anchor="w")

        # Separador
        ctk.CTkFrame(self, height=1, fg_color="#1E3450").grid(
            row=0, column=0, sticky="ew", padx=40, pady=(80, 0)
        )

        # ScrollFrame com seções
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=40, pady=8)
        scroll.grid_columnconfigure(0, weight=1)

        self._build_ai_section(scroll)
        self._build_storage_section(scroll)
        self._build_scanner_section(scroll)

        # Botão salvar
        ctk.CTkButton(
            self,
            text="💾   Salvar Configurações",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            corner_radius=10,
            fg_color="#1565C0",
            hover_color="#1976D2",
            command=self._salvar,
        ).grid(row=2, column=0, padx=40, pady=16)

    # ── Seção IA ────────────────────────────────────────────────────────────────

    def _build_ai_section(self, parent):
        section = self._make_section(parent, "🤖  Inteligência Artificial")

        # Seleção de provedor
        ctk.CTkLabel(section, text="Provedor de IA:", font=ctk.CTkFont(size=12), text_color="#90A4AE").grid(
            row=0, column=0, sticky="w", padx=4, pady=(4, 2)
        )

        self.provider_var = ctk.StringVar(value=self.settings.get("ai_provider", "gemini"))

        providers_frame = ctk.CTkFrame(section, fg_color="transparent")
        providers_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 12))

        for i, (pid, label) in enumerate([
            ("gemini", "Google Gemini"), 
            ("openai", "OpenAI"), 
            ("anthropic", "Anthropic"),
            ("openrouter", "OpenRouter")
        ]):
            ctk.CTkRadioButton(
                providers_frame,
                text=label,
                variable=self.provider_var,
                value=pid,
                font=ctk.CTkFont(size=13),
                command=self._on_provider_change,
            ).grid(row=0, column=i, padx=12, sticky="w")

        # Chave de API
        ctk.CTkLabel(section, text="Chave de API:", font=ctk.CTkFont(size=12), text_color="#90A4AE").grid(
            row=2, column=0, sticky="w", padx=4, pady=(4, 2)
        )

        api_row = ctk.CTkFrame(section, fg_color="transparent")
        api_row.grid(row=3, column=0, sticky="ew", padx=4)
        api_row.grid_columnconfigure(0, weight=1)

        self.api_key_var = ctk.StringVar(value=self._get_current_key())
        self.api_entry = ctk.CTkEntry(
            api_row,
            textvariable=self.api_key_var,
            show="•",
            font=ctk.CTkFont(size=12),
            height=38,
            placeholder_text="Cole aqui sua chave de API",
        )
        self.api_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.show_key = False
        self.btn_show = ctk.CTkButton(
            api_row,
            text="👁",
            width=40,
            height=38,
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=self._toggle_key_visibility,
        )
        self.btn_show.grid(row=0, column=1)

        # Modelo
        ctk.CTkLabel(section, text="Modelo:", font=ctk.CTkFont(size=12), text_color="#90A4AE").grid(
            row=4, column=0, sticky="w", padx=4, pady=(12, 2)
        )

        model_row = ctk.CTkFrame(section, fg_color="transparent")
        model_row.grid(row=5, column=0, sticky="ew", padx=4)
        model_row.grid_columnconfigure(0, weight=1)

        self.model_var = ctk.StringVar(value=self.settings.get("ai_model", "gemini-2.0-flash"))
        self.model_combo = ctk.CTkComboBox(
            model_row,
            variable=self.model_var,
            values=self._get_models_for_provider(),
            font=ctk.CTkFont(size=12),
            height=38,
        )
        self.model_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        # Info sobre modelos customizados
        ctk.CTkLabel(
            section, 
            text="💡 Para OpenRouter, você pode digitar o ID do modelo (ex: deepseek/deepseek-chat)", 
            font=ctk.CTkFont(size=10), 
            text_color="#546E7A"
        ).grid(row=6, column=0, sticky="w", padx=4, pady=(0, 4))

        self.btn_test = ctk.CTkButton(
            model_row,
            text="🔌  Testar Conexão",
            height=38,
            width=160,
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=self._testar_conexao,
        )
        self.btn_test.grid(row=0, column=1)

        self.lbl_test_result = ctk.CTkLabel(
            section, text="", font=ctk.CTkFont(size=11), text_color="#546E7A"
        )
        self.lbl_test_result.grid(row=7, column=0, sticky="w", padx=4, pady=(4, 8))

    # ── Seção Armazenamento ─────────────────────────────────────────────────────

    def _build_storage_section(self, parent):
        section = self._make_section(parent, "📂  Armazenamento")
        section.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(section, text="Pasta de saída dos PDFs:", font=ctk.CTkFont(size=12), text_color="#90A4AE").grid(
            row=0, column=0, sticky="w", padx=4, pady=(4, 2)
        )

        path_row = ctk.CTkFrame(section, fg_color="transparent")
        path_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 8))
        path_row.grid_columnconfigure(0, weight=1)

        self.folder_var = ctk.StringVar(value=self.settings.get("output_folder", ""))
        self.folder_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.folder_var,
            font=ctk.CTkFont(size=12),
            height=38,
            state="readonly",
        )
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            path_row,
            text="📂  Alterar",
            width=110,
            height=38,
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=self._escolher_pasta,
        ).grid(row=0, column=1)

        # Contagem de PDFs
        self.lbl_count = ctk.CTkLabel(
            section, text="", font=ctk.CTkFont(size=11), text_color="#546E7A"
        )
        self.lbl_count.grid(row=2, column=0, sticky="w", padx=4, pady=(0, 8))
        self._update_pdf_count()

    # ── Seção Scanner ──────────────────────────────────────────────────────────

    def _build_scanner_section(self, parent):
        section = self._make_section(parent, "🖨️  Scanner")
        section.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(section, text="Scanner selecionado:", font=ctk.CTkFont(size=12), text_color="#90A4AE").grid(
            row=0, column=0, sticky="w", padx=4, pady=(4, 2)
        )

        scanner_row = ctk.CTkFrame(section, fg_color="transparent")
        scanner_row.grid(row=1, column=0, sticky="ew", padx=4)
        scanner_row.grid_columnconfigure(0, weight=1)

        self.scanner_list = scan_module.list_scanners()
        scanner_values = self.scanner_list if self.scanner_list else ["(Nenhum scanner detectado)"]

        current_scanner = self.settings.get("scanner_name", "")
        combo_val = current_scanner if current_scanner in self.scanner_list else scanner_values[0]

        self.scanner_var = ctk.StringVar(value=combo_val)
        self.scanner_combo = ctk.CTkComboBox(
            scanner_row,
            variable=self.scanner_var,
            values=scanner_values,
            font=ctk.CTkFont(size=12),
            height=38,
            state="readonly" if not self.scanner_list else "normal",
        )
        self.scanner_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            scanner_row,
            text="🔄  Atualizar",
            width=110,
            height=38,
            fg_color="#1E3A5F",
            hover_color="#1565C0",
            command=self._atualizar_scanners,
        ).grid(row=0, column=1, padx=(0, 8))

        ctk.CTkButton(
            scanner_row,
            text="🧪  Testar",
            width=90,
            height=38,
            fg_color="#37474F",
            hover_color="#455A64",
            command=self._testar_scanner,
        ).grid(row=0, column=2)

        self.lbl_scanner_status = ctk.CTkLabel(
            section,
            text="ℹ️  Caso nenhum scanner seja detectado, o sistema usará importação de arquivo.",
            font=ctk.CTkFont(size=11),
            text_color="#546E7A",
            wraplength=540,
            justify="left",
        )
        self.lbl_scanner_status.grid(row=2, column=0, sticky="w", padx=4, pady=(8, 8))

    # ── Helpers da UI ──────────────────────────────────────────────────────────

    def _make_section(self, parent, title: str) -> ctk.CTkFrame:
        """Cria uma caixa de seção com título."""
        outer = ctk.CTkFrame(parent, fg_color="#0D1B2A", corner_radius=12)
        outer.pack(fill="x", pady=8)
        outer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            outer,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4FC3F7",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        ctk.CTkFrame(outer, height=1, fg_color="#1E3450").grid(
            row=1, column=0, sticky="ew", padx=20, pady=(0, 12)
        )

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))
        inner.grid_columnconfigure(0, weight=1)
        return inner

    def _get_current_key(self) -> str:
        provider = self.provider_var.get() if hasattr(self, "provider_var") else self.settings.get("ai_provider", "gemini")
        return self.settings.get("api_keys", {}).get(provider, "")

    def _get_models_for_provider(self) -> list:
        provider = self.provider_var.get() if hasattr(self, "provider_var") else self.settings.get("ai_provider", "gemini")
        return AVAILABLE_MODELS.get(provider, [])

    def _on_provider_change(self):
        provider = self.provider_var.get()
        # Salva chave atual antes de trocar
        if hasattr(self, "api_key_var"):
            old_provider = self.settings.get("ai_provider", "gemini")
            self.settings.setdefault("api_keys", {})[old_provider] = self.api_key_var.get()

        self.settings["ai_provider"] = provider
        # Atualiza campo de chave
        self.api_key_var.set(self.settings.get("api_keys", {}).get(provider, ""))
        # Atualiza modelos disponíveis
        models = AVAILABLE_MODELS.get(provider, [])
        self.model_combo.configure(values=models)
        self.model_var.set(models[0] if models else "")
        self.lbl_test_result.configure(text="")

    def _toggle_key_visibility(self):
        self.show_key = not self.show_key
        self.api_entry.configure(show="" if self.show_key else "•")

    def _update_pdf_count(self):
        folder = self.settings.get("output_folder", "")
        if folder and Path(folder).exists():
            count = len(list(Path(folder).glob("*.pdf")))
            self.lbl_count.configure(text=f"📄  {count} arquivo(s) PDF salvos nesta pasta.")
        else:
            self.lbl_count.configure(text="⚠️  Pasta não existe ainda (será criada ao salvar o primeiro PDF).")

    def _escolher_pasta(self):
        path = fd.askdirectory(title="Selecionar pasta de saída dos PDFs")
        if path:
            self.folder_var.set(path)
            self.settings["output_folder"] = path
            self._update_pdf_count()

    def _atualizar_scanners(self):
        self.scanner_list = scan_module.list_scanners()
        values = self.scanner_list if self.scanner_list else ["(Nenhum scanner detectado)"]
        self.scanner_combo.configure(values=values)
        self.scanner_var.set(values[0])
        status = f"✅  {len(self.scanner_list)} scanner(s) detectado(s)." if self.scanner_list else "❌  Nenhum scanner encontrado."
        self.lbl_scanner_status.configure(text=status)

    def _testar_scanner(self):
        scanner_name = self.scanner_var.get()
        if not scanner_name or "(Nenhum" in scanner_name:
            mb.showwarning("Scanner", "Nenhum scanner selecionado.")
            return

        self.lbl_scanner_status.configure(text="⌛  Realizando scan de teste...")

        def run():
            img, err = scan_module.scan_page(scanner_name)
            if img:
                self.after(0, lambda: self.lbl_scanner_status.configure(
                    text=f"✅  Scan de teste bem-sucedido! ({img.size[0]}x{img.size[1]} px)",
                    text_color="#66BB6A"
                ))
            else:
                msg = f"❌  Falha no scan: {err}" if err else "❌  Falha no scan de teste. Verifique o scanner."
                self.after(0, lambda: self.lbl_scanner_status.configure(
                    text=msg,
                    text_color="#EF5350"
                ))

        threading.Thread(target=run, daemon=True).start()

    def _testar_conexao(self):
        self.btn_test.configure(state="disabled", text="⌛  Testando...")
        self.lbl_test_result.configure(text="")

        # Monta settings temporário com valor atual do campo
        temp = dict(self.settings)
        temp["ai_provider"] = self.provider_var.get()
        temp["ai_model"] = self.model_var.get()
        temp.setdefault("api_keys", {})[self.provider_var.get()] = self.api_key_var.get()

        def run():
            try:
                testar_conexao(temp)
                self.after(0, lambda: self.lbl_test_result.configure(
                    text="✅  Conexão bem-sucedida!", text_color="#66BB6A"
                ))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg: self.lbl_test_result.configure(
                    text=f"❌  {m}", text_color="#EF5350"
                ))
            finally:
                self.after(0, lambda: self.btn_test.configure(state="normal", text="🔌  Testar Conexão"))

        threading.Thread(target=run, daemon=True).start()

    # ── Salvar ──────────────────────────────────────────────────────────────────

    def _salvar(self):
        # Captura valores atuais
        self.settings["ai_provider"] = self.provider_var.get()
        self.settings["ai_model"] = self.model_var.get()
        self.settings.setdefault("api_keys", {})[self.provider_var.get()] = self.api_key_var.get()
        self.settings["output_folder"] = self.folder_var.get()
        scanner_val = self.scanner_var.get()
        self.settings["scanner_name"] = scanner_val if "(Nenhum" not in scanner_val else ""

        self.app.update_settings(self.settings)
        mb.showinfo("Configurações", "Configurações salvas com sucesso!")
