"""
license.py - Sistema de licenciamento do FarmaPop IA.

- Machine ID: SHA256 de MAC + hostname + platform
- Licença: payload JSON assinado com HMAC-SHA256, codificado em base32
- Formato visual: FARMA-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import platform
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

# ─── Chave secreta (hardcoded — não compartilhe este código) ─────────────────
# Altere esta chave para uma string única e secreta antes de distribuir o app.
_SECRET_KEY = b"FarmaPop_IA@License#2025$Ross&Seguranca_PFPB!"


# ─── Machine ID ──────────────────────────────────────────────────────────────

def get_machine_id() -> str:
    """
    Retorna o fingerprint único desta máquina.
    Combina: MAC address + hostname + sistema operacional.
    Formato de saída: XXXX-XXXX-XXXX-XXXX (16 caracteres hex maiúsculos)
    """
    try:
        mac = str(uuid.getnode())
        hostname = platform.node()
        system = platform.system() + platform.release()
        raw = f"{mac}|{hostname}|{system}"
        digest = hashlib.sha256(raw.encode()).hexdigest().upper()
        # Formata em grupos de 4 para legibilidade
        chars = digest[:16]
        return f"{chars[0:4]}-{chars[4:8]}-{chars[8:12]}-{chars[12:16]}"
    except Exception:
        return "0000-0000-0000-0000"


def _raw_machine_id() -> str:
    """Retorna o machine ID completo (SHA256 hex) para uso interno na validação."""
    try:
        mac = str(uuid.getnode())
        hostname = platform.node()
        system = platform.system() + platform.release()
        raw = f"{mac}|{hostname}|{system}"
        return hashlib.sha256(raw.encode()).hexdigest().upper()
    except Exception:
        return "0" * 64


# ─── Geração de licença ───────────────────────────────────────────────────────

def gerar_licenca(machine_id_display: str, meses: int = 1) -> str:
    """
    Gera uma chave de licença assinada para o machine_id informado.

    Args:
        machine_id_display: Machine ID no formato XXXX-XXXX-XXXX-XXXX (obtido do cliente).
        meses: Quantidade de meses de validade (padrão: 1).

    Returns:
        Chave de licença no formato FARMA-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    """
    expiry = (date.today() + timedelta(days=30 * meses)).isoformat()

    # O machine_id_display sem hífens vira o mid no payload
    mid = machine_id_display.replace("-", "").upper()

    payload = json.dumps({
        "mid": mid,
        "exp": expiry,
        "ver": 1,
    }, separators=(",", ":"))

    # Assina com HMAC-SHA256
    sig = hmac.new(_SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest().upper()

    # Combina payload + assinatura e codifica em base32 (sem '=')
    combined = f"{payload}||{sig}"
    encoded = base64.b32encode(combined.encode()).decode().rstrip("=")

    # Formata em grupos de 5 com prefixo FARMA-
    groups = [encoded[i : i + 5] for i in range(0, len(encoded), 5)]
    key = "FARMA-" + "-".join(groups)
    return key


# ─── Validação de licença ─────────────────────────────────────────────────────

class LicenseError(Exception):
    """Erro específico de licença inválida ou expirada."""


def _decode_key(key: str) -> tuple[str, str]:
    """
    Decodifica a chave no formato FARMA-XXXXX-... e retorna (payload, sig).
    Lança LicenseError se o formato for inválido.
    """
    key = key.strip().upper()
    if not key.startswith("FARMA-"):
        raise LicenseError("Chave inválida: prefixo incorreto.")

    body = key[6:].replace("-", "")  # remove "FARMA-" e todos os hífens

    # Padding base32
    pad = (8 - len(body) % 8) % 8
    try:
        decoded = base64.b32decode(body + "=" * pad).decode()
    except Exception as exc:
        raise LicenseError("Chave inválida: não foi possível decodificar.") from exc

    if "||" not in decoded:
        raise LicenseError("Chave inválida: estrutura incorreta.")

    payload_str, sig = decoded.split("||", 1)
    return payload_str, sig


def validar_licenca(key: str) -> dict:  # type: ignore[type-arg]
    """
    Valida a chave de licença para esta máquina.

    Returns:
        dict com {"valido": True, "expiry": "AAAA-MM-DD", "dias_restantes": N}

    Raises:
        LicenseError com mensagem amigável em caso de falha.
    """
    payload_str, sig_recebida = _decode_key(key)

    # Verifica assinatura
    sig_esperada = hmac.new(
        _SECRET_KEY, payload_str.encode(), hashlib.sha256
    ).hexdigest().upper()

    if not hmac.compare_digest(sig_recebida, sig_esperada):
        raise LicenseError("Chave inválida: assinatura incorreta.")

    # Parseia payload
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as exc:
        raise LicenseError("Chave inválida: dados corrompidos.") from exc

    # Verifica machine ID
    mid_licenca = payload.get("mid", "").upper()
    mid_maquina = _raw_machine_id()[:16]  # primeiros 16 chars do SHA256
    if mid_licenca != mid_maquina:
        raise LicenseError(
            "Licença inválida para esta máquina.\n"
            "Esta chave foi gerada para outro computador."
        )

    # Verifica expiração
    exp_str = payload.get("exp", "")
    try:
        expiry = datetime.strptime(exp_str, "%Y-%m-%d").date()
    except ValueError as exc:
        raise LicenseError("Chave inválida: data de expiração corrompida.") from exc

    today = date.today()
    if today > expiry:
        dias_vencida = (today - expiry).days
        raise LicenseError(
            f"Licença expirada há {dias_vencida} dia(s).\n"
            "Entre em contato para renovar sua licença."
        )

    dias_restantes = (expiry - today).days
    return {
        "valido": True,
        "expiry": exp_str,
        "dias_restantes": dias_restantes,
    }


# ─── Persistência ─────────────────────────────────────────────────────────────

def salvar_licenca(key: str, settings: dict) -> None:  # type: ignore[type-arg]
    """Salva a chave de licença nas settings."""
    settings["license_key"] = key.strip().upper()


def carregar_licenca(settings: dict) -> Optional[str]:  # type: ignore[type-arg]
    """Carrega a chave de licença das settings. Retorna None se não houver."""
    key = settings.get("license_key", "")
    return key if key else None


def verificar_licenca_settings(settings: dict) -> Optional[dict]:  # type: ignore[type-arg]
    """
    Verifica se há uma licença válida nas settings.
    Retorna o dict de resultado ou None se inválida/ausente.
    """
    key = carregar_licenca(settings)
    if not key:
        return None
    try:
        return validar_licenca(key)
    except LicenseError:
        return None
