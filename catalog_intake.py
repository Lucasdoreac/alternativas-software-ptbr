"""PARADIGMA: entrada de sugestões do catálogo, de issue form do GitHub até registro pendente de revisão.

A sugestão de um visitante nunca vira fonte conferida sozinha. Este módulo lê o formulário, faz as
checagens determinísticas na fonte oficial (o link responde, o repositório do GitHub declara licença,
data do último push e se está arquivado) e grava o registro como ``reported``: link informado, não
conferido. Quem revisa a PR muda para ``checked`` depois de ler a fonte. Nenhum texto de terceiros é
copiado: o resumo é o motivo escrito por quem sugeriu, e o revisor o reescreve se precisar.
"""

from __future__ import annotations

import copy
import ipaddress
import json
import re
from typing import Any, Callable
from urllib.parse import urlparse
import urllib.request

from catalog_core import PLATFORMS, normalize, validate_catalog

# Rótulos do formulário em .github/ISSUE_TEMPLATE/sugerir-alternativa.yml -> campo.
FIELDS = {
    "Nome da alternativa": "name",
    "Site oficial do projeto": "url",
    "Substitui qual software": "reference",
    "Área": "area",
    "Área nova (só se escolheu Outra)": "area_other",
    "Sistemas em que roda": "platforms",
    "Por que é uma boa alternativa": "why",
}
OTHER_AREA = "Outra"
NO_RESPONSE = "_No response_"

Fetch = Callable[[str], tuple[int, str]]
FetchJson = Callable[[str], dict[str, Any] | None]


class IntakeError(ValueError):
    """Sugestão que não pode virar registro; a mensagem vai para o comentário no issue."""


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize(value)).strip("-")[:64]


def parse_issue_form(body: str) -> dict[str, Any]:
    """Campos de um issue form renderizado (``### Rótulo`` seguido do valor)."""
    form: dict[str, Any] = {}
    for block in re.split(r"^### ", body or "", flags=re.MULTILINE)[1:]:
        label, _, value = block.partition("\n")
        key = FIELDS.get(label.strip())
        if not key:
            continue
        value = value.strip()
        if key == "platforms":
            form[key] = [m.group(2).strip() for m in re.finditer(r"^- \[([xX])\] (.+)$", value, re.MULTILINE)]
        else:
            form[key] = "" if value == NO_RESPONSE else value
    return form


def _public_https(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or host == "localhost" or host.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return address.is_global


def default_fetch(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "troca-justa-catalogador"})
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310 — https público checado antes
        return response.status, response.geturl()


def default_fetch_json(url: str) -> dict[str, Any] | None:
    request = urllib.request.Request(url, headers={"User-Agent": "troca-justa-catalogador",
                                                   "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError):
        return None


def check_source(url: str, *, fetch: Fetch = default_fetch, fetch_json: FetchJson = default_fetch_json) -> dict[str, Any]:
    """Checagens que não pedem julgamento. Falha de rede vira fato registrado, não exceção."""
    result: dict[str, Any] = {"url": url, "reachable": False, "final_url": None, "license": None,
                              "pushed_at": None, "archived": None, "github_repo": None}
    try:
        status, final_url = fetch(url)
        result["reachable"] = 200 <= status < 400
        result["final_url"] = final_url
    except Exception as error:  # noqa: BLE001 — qualquer falha de rede é "não respondeu"
        result["error"] = type(error).__name__
    match = re.match(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$", url)
    if match:
        owner, repo = match.groups()
        result["github_repo"] = f"{owner}/{repo}"
        info = fetch_json(f"https://api.github.com/repos/{owner}/{repo}") or {}
        license_info = info.get("license") or {}
        spdx = license_info.get("spdx_id")
        result["license"] = spdx if spdx and spdx != "NOASSERTION" else None
        result["pushed_at"] = (info.get("pushed_at") or "")[:10] or None
        result["archived"] = info.get("archived")
    return result


def _evidence(check: dict[str, Any], today: str) -> str:
    parts = [f"Checagem automática em {today}:"]
    parts.append("o site respondeu" if check["reachable"] else "o site não respondeu")
    if check.get("github_repo"):
        parts.append(f"repositório {check['github_repo']}")
        parts.append(f"licença declarada {check['license']}" if check["license"] else "sem licença declarada no GitHub")
        if check.get("pushed_at"):
            parts.append(f"último push {check['pushed_at']}")
        if check.get("archived"):
            parts.append("repositório arquivado")
    return f"{parts[0]} {', '.join(parts[1:])}. Falta a revisão humana da fonte."


def intake(data: dict[str, Any], form: dict[str, Any], *, issue_number: int, today: str,
           check: Callable[[str], dict[str, Any]] = check_source) -> tuple[dict[str, Any], str, dict[str, Any]]:
    """Novo catálogo com a sugestão como registro ``reported``, o id criado e o resultado da checagem."""
    name = (form.get("name") or "").strip()
    url = (form.get("url") or "").strip()
    reference_name = (form.get("reference") or "").strip()
    area = (form.get("area") or "").strip()
    why = (form.get("why") or "").strip()
    platforms = [p for p in form.get("platforms") or [] if p in PLATFORMS]
    missing = [label for label, value in (("nome", name), ("site oficial", url), ("software substituído", reference_name),
                                           ("área", area), ("motivo", why)) if not value]
    if missing:
        raise IntakeError("Faltou preencher: " + ", ".join(missing) + ".")
    if not platforms:
        raise IntakeError("Marque pelo menos um sistema em que a alternativa roda.")
    if not _public_https(url):
        raise IntakeError("O site oficial precisa ser um endereço https público.")
    new = copy.deepcopy(data)
    software_id = slug(name)
    if not software_id:
        raise IntakeError("O nome da alternativa não gera um identificador válido.")
    if any(item["id"] == software_id for item in new["software"]):
        raise IntakeError(f"{name} já está no catálogo.")

    if area == OTHER_AREA:
        other = (form.get("area_other") or "").strip()
        if not other:
            raise IntakeError("Escolheu Outra área: escreva o nome da área nova.")
        category = next((c for c in new["categories"] if normalize(c["name"]) == normalize(other)), None)
        if category is None:
            category = {"id": slug(other), "name": other[:100], "aliases": []}
            new["categories"].append(category)
    else:
        category = next((c for c in new["categories"] if c["name"] == area), None)
        if category is None:
            raise IntakeError(f"Área desconhecida: {area}.")

    wanted = normalize(reference_name)
    reference = next((r for r in new["references"]
                      if wanted in {normalize(r["name"]), *map(normalize, r.get("aliases", []))}), None)
    if reference is None:
        reference = {"id": slug(reference_name), "name": reference_name[:160], "aliases": [reference_name.lower()[:160]],
                     "category_ids": [category["id"]]}
        new["references"].append(reference)
    elif category["id"] not in reference["category_ids"]:
        reference["category_ids"].append(category["id"])

    result = check(url)
    new["software"].append({
        "id": software_id, "name": name[:160], "aliases": [],
        "summary": why[:500], "category_ids": [category["id"]], "pricing": "unknown",
        "license": result.get("license") or "não conferida", "platforms": platforms,
        "install_kind": "github" if result.get("github_repo") else "official-site",
        "url": url, "source_url": url, "source_state": "reported", "checked_at": None,
        "evidence_note": _evidence(result, today)[:800],
    })
    new["relations"].append({"reference_id": reference["id"], "software_id": software_id, "match": "same_category",
                             "note": f"Sugerida no issue #{issue_number}. {why}"[:800]})
    new["updated_at"] = today
    errors = validate_catalog(new)
    if errors:
        raise IntakeError("A sugestão gerou um registro inválido: " + "; ".join(errors[:5]))
    return new, software_id, result
