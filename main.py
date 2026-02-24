"""
main.py - Ponto de entrada do FarmaPop IA.
Verifica licença antes de abrir a aplicação principal.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que o diretório raiz do projeto está no PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from core.config import load_settings, save_settings
from core.license import LicenseError, get_machine_id, validar_licenca, carregar_licenca


def _verificar_licenca(settings: dict) -> tuple[bool, str]:  # type: ignore[type-arg]
    """
    Retorna (valida, mensagem_erro).
    """
    chave = carregar_licenca(settings)
    if not chave:
        return False, ""
    try:
        validar_licenca(chave)
        return True, ""
    except LicenseError as e:
        return False, str(e)


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    settings = load_settings()
    valida, msg_erro = _verificar_licenca(settings)

    if valida:
        # Licença OK → abre o app diretamente
        from ui.app import App
        app = App()
        app.mainloop()
    else:
        # Sem licença ou expirada → abre tela de ativação
        from ui.screens.license_screen import LicenseScreen, LicenseExpiredScreen

        def _abrir_app() -> None:
            from ui.app import App
            app = App()
            app.mainloop()

        if msg_erro:
            # Licença expirada ou inválida
            screen = LicenseExpiredScreen(settings, _abrir_app, msg_extra=msg_erro)
        else:
            # Nunca foi ativado
            screen = LicenseScreen(settings, _abrir_app)

        screen.mainloop()


if __name__ == "__main__":
    main()
