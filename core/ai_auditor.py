"""
ai_auditor.py - Orquestrador de IA para auditoria de documentos do PFPB.
Suporta Google Gemini, OpenAI e Anthropic.
Extrai número de autorização e data, e audita conforme master_prompt.md.
"""

from __future__ import annotations

import base64
import io
import json
from typing import Any, List

from PIL import Image as PILImage

from core.config import get_active_api_key, get_master_prompt


# ─── Resultado da auditoria ─────────────────────────────────────────────────

class AuditResult:
    def __init__(self, raw: dict[str, Any]) -> None:
        self.aprovado: bool = raw.get("aprovado", False)
        self.autorizacao: str = raw.get("autorizacao", "")
        self.data: str = raw.get("data", "")
        self.erros: List[str] = raw.get("erros", [])
        self.observacoes: str = raw.get("observacoes", "")

    def __repr__(self) -> str:
        return (
            f"AuditResult(aprovado={self.aprovado}, "
            f"autorizacao='{self.autorizacao}', data='{self.data}', "
            f"erros={self.erros})"
        )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _image_to_base64(img: PILImage.Image, fmt: str = "JPEG") -> str:
    """Converte imagem PIL para string base64."""
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _build_prompt(master_prompt: str, tipo_transacao: str, total_imagens: int) -> str:
    """Constrói o prompt completo de auditoria."""
    return f"""
{master_prompt}

---

INSTRUÇÕES ADICIONAIS PARA ESTA ANÁLISE:

Você está analisando um dossiê de transação do tipo: **{tipo_transacao}**
Total de imagens enviadas: {total_imagens}

Por favor, realize DUAS tarefas:

**TAREFA 1 - EXTRAÇÃO DE DADOS:**
Leia o Cupom Fiscal e/ou Cupom Vinculado e extraia:
- Número de autorização da transação (ex: 111.222.333.444.555)
- Data da transação (formato DD-MM-AAAA)

**TAREFA 2 - AUDITORIA COMPLETA:**
Analise todos os documentos conforme as regras detalhadas acima.

Responda APENAS com um JSON válido, sem markdown, sem texto extra:
{{
  "aprovado": true ou false,
  "autorizacao": "número extraído ou vazio se não encontrado",
  "data": "data no formato DD-MM-AAAA ou vazio se não encontrada",
  "erros": ["lista de erros encontrados, vazia se aprovado"],
  "observacoes": "observações adicionais relevantes"
}}
""".strip()


def _parse_json_response(text: str) -> dict[str, Any]:
    """Extrai e parseia o JSON da resposta da IA."""
    text = text.strip()
    if text.startswith("```"):
        # Remove a primeira e última linha (```json e ```)
        inner_lines = text.split("\n")
        inner_lines.pop(0)   # remove ```json
        if inner_lines and inner_lines[-1].startswith("```"):
            inner_lines.pop(-1)  # remove ```
        text = "\n".join(inner_lines)
    result: dict[str, Any] = json.loads(text)
    return result


# ─── Clientes por provedor ───────────────────────────────────────────────────

def _audit_gemini(
    images: List[PILImage.Image],
    prompt: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    import google.generativeai as genai  # type: ignore[import-untyped]

    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(model)

    content: list[Any] = [prompt]
    for img in images:
        content.append(img)

    response = client.generate_content(content)
    return _parse_json_response(response.text)


def _audit_openai(
    images: List[PILImage.Image],
    prompt: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    from openai import OpenAI  # type: ignore[import-untyped]

    client = OpenAI(api_key=api_key)

    image_messages: list[dict[str, Any]] = []
    for img in images:
        b64 = _image_to_base64(img)
        image_messages.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}",
                "detail": "high",
            },
        })

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}] + image_messages,
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=2000,
    )
    return _parse_json_response(response.choices[0].message.content or "")


def _audit_anthropic(
    images: List[PILImage.Image],
    prompt: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    import anthropic  # type: ignore[import-untyped]

    client = anthropic.Anthropic(api_key=api_key)

    content: list[dict[str, Any]] = []
    for img in images:
        b64 = _image_to_base64(img)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": b64,
            },
        })
    content.append({"type": "text", "text": prompt})

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": content}],
    )
    return _parse_json_response(response.content[0].text)  # type: ignore[union-attr]


# ─── Função principal ────────────────────────────────────────────────────────

def auditar_transacao(
    images: List[PILImage.Image],
    tipo_transacao: str,
    settings: dict[str, Any],
) -> AuditResult:
    """
    Audita o dossiê de uma transação usando a IA configurada.

    Args:
        images: Lista de todas as imagens digitalizadas (em ordem).
        tipo_transacao: Nome do tipo (ex: "Próprio Paciente").
        settings: Configurações carregadas (provedor, modelo, chave).

    Returns:
        AuditResult com resultado da análise.
    """
    provider: str = settings.get("ai_provider", "gemini")
    model: str = settings.get("ai_model", "gemini-2.0-flash")
    api_key: str = get_active_api_key(settings)

    if not api_key:
        raise ValueError(f"Chave de API não configurada para o provedor '{provider}'.")

    if not images:
        raise ValueError("Nenhuma imagem para auditar.")

    master_prompt = get_master_prompt()
    prompt = _build_prompt(master_prompt, tipo_transacao, len(images))

    try:
        raw: dict[str, Any]
        if provider == "gemini":
            raw = _audit_gemini(images, prompt, api_key, model)
        elif provider == "openai":
            raw = _audit_openai(images, prompt, api_key, model)
        elif provider == "anthropic":
            raw = _audit_anthropic(images, prompt, api_key, model)
        else:
            raise ValueError(f"Provedor desconhecido: {provider}")

        return AuditResult(raw)

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"A IA retornou uma resposta inválida (não é JSON). Detalhes: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Erro durante a auditoria: {e}") from e


def testar_conexao(settings: dict[str, Any]) -> bool:
    """
    Testa a conexão com a API do provedor configurado.
    Retorna True se bem-sucedido.
    """
    provider: str = settings.get("ai_provider", "gemini")
    model: str = settings.get("ai_model", "gemini-2.0-flash")
    api_key: str = get_active_api_key(settings)

    if not api_key:
        raise ValueError("Nenhuma chave de API configurada.")

    test_prompt = "Responda apenas: OK"

    if provider == "gemini":
        import google.generativeai as genai  # type: ignore[import-untyped]
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(model)
        client.generate_content(test_prompt)

    elif provider == "openai":
        from openai import OpenAI  # type: ignore[import-untyped]
        client_oai = OpenAI(api_key=api_key)
        client_oai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=5,
        )

    elif provider == "anthropic":
        import anthropic  # type: ignore[import-untyped]
        client_ant = anthropic.Anthropic(api_key=api_key)
        client_ant.messages.create(
            model=model,
            max_tokens=5,
            messages=[{"role": "user", "content": test_prompt}],
        )

    return True
