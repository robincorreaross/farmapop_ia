"""
scanner.py - Interface com scanners via WIA (Windows Image Acquisition).
Permite listar, selecionar e escanear com dispositivos WIA.
Fallback: importar imagens de arquivos locais.
"""

from __future__ import annotations

import io
from typing import List, Optional

from PIL import Image


def list_scanners() -> List[str]:
    """
    Lista os scanners disponíveis via WIA.
    Retorna lista de nomes de dispositivos.
    """
    scanners: List[str] = []
    try:
        import win32com.client  # type: ignore[import-untyped]
        wia = win32com.client.Dispatch("WIA.DeviceManager")
        for device_info in wia.DeviceInfos:
            if device_info.Type == 1:  # Scanner type
                name = device_info.Properties("Name").Value
                scanners.append(name)
    except Exception:  # noqa: BLE001
        pass
    return scanners


def _get_wia_device(device_name: str) -> object | None:
    """Obtém o objeto de dispositivo WIA pelo nome."""
    try:
        import win32com.client  # type: ignore[import-untyped]
        wia = win32com.client.Dispatch("WIA.DeviceManager")
        for device_info in wia.DeviceInfos:
            if device_info.Type == 1:
                name = device_info.Properties("Name").Value
                if name == device_name:
                    return device_info.Connect()
    except Exception:  # noqa: BLE001
        pass
    return None


def scan_page(device_name: str, dpi: int = 200) -> Optional[Image.Image]:
    """
    Escaneia uma página usando WIA.
    Retorna imagem PIL ou None em caso de falha.
    """
    try:
        device = _get_wia_device(device_name)
        if device is None:
            return None

        scan_item = device.Items[1]  # type: ignore[union-attr]

        try:
            scan_item.Properties("Horizontal Resolution").Value = dpi
            scan_item.Properties("Vertical Resolution").Value = dpi
        except Exception:  # noqa: BLE001
            pass

        # JPEG GUID
        image_file = scan_item.Transfer("{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}")
        data = bytes(image_file.FileData.BinaryData)
        img = Image.open(io.BytesIO(data))
        return img.convert("RGB")

    except Exception as e:
        print(f"[Scanner] Erro ao escanear: {e}")
        return None


def scan_with_dialog() -> Optional[Image.Image]:
    """
    Abre o diálogo nativo do WIA para selecionar scanner e escanear.
    Útil como fallback quando o scanner não está pré-configurado.
    """
    try:
        import win32com.client  # type: ignore[import-untyped]
        dialog = win32com.client.Dispatch("WIA.CommonDialog")
        image_file = dialog.ShowAcquireImage(
            1, 1, 4,
            "{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}",
            False, True, False,
        )
        if image_file:
            data = bytes(image_file.FileData.BinaryData)
            img = Image.open(io.BytesIO(data))
            return img.convert("RGB")
    except Exception as e:
        print(f"[Scanner] Erro no diálogo WIA: {e}")
    return None


def import_from_file(parent_window: object = None) -> Optional[Image.Image]:
    """
    Abre caixa de diálogo para importar imagem de arquivo (JPEG/PNG).
    Retorna imagem PIL ou None se cancelado.
    """
    import tkinter as tk
    from tkinter import filedialog

    root: object
    if parent_window is None:
        root = tk.Tk()
        tk.Tk.withdraw(root)  # type: ignore[arg-type]
    else:
        root = parent_window

    filepath: str = filedialog.askopenfilename(
        title="Selecionar Imagem",
        filetypes=[
            ("Imagens", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("Todos os arquivos", "*.*"),
        ],
    )

    if parent_window is None:
        tk.Tk.destroy(root)  # type: ignore[arg-type]

    if filepath:
        try:
            img = Image.open(filepath)
            return img.convert("RGB")
        except Exception as e:
            print(f"[Scanner] Erro ao importar arquivo: {e}")

    return None


def optimize_image(img: Image.Image, max_size: int = 2480) -> Image.Image:
    """
    Otimiza a imagem para o PDF: redimensiona mantendo proporção se necessário.
    """
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_size:
        if w > h:
            new_w = max_size
            new_h = int(h * max_size / w)
        else:
            new_h = max_size
            new_w = int(w * max_size / h)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    return img
