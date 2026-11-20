"""Núcleo determinístico do catálogo: validação, busca e ordenação transparente."""

from __future__ import annotations

from datetime import date
from difflib import SequenceMatcher
import re
from urllib.parse import urlsplit
from typing import Any


SCHEMA_VERSION = 1
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SOURCE_STATES = {"checked", "reported", "unverified"}
PRICING = {"free", "freemium", "paid", "unknown"}
PLATFORMS = {"macOS", "Windows", "Linux", "BSD", "Android", "iOS", "Web"}
INSTALL_KINDS = {"official-site", "github", "homebrew", "fdroid", "flathub", "snap", "command-line", "extra-steps", "unknown"}
SOURCE_RANK = {"checked": 0, "reported": 1, "unverified": 2}


def normalize(value: str) -> str:
    import unicodedata

    return " ".join(unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode("ascii").lower().split())


def _required_text(item: dict[str, Any], field: str, path: str, errors: list[str], *, maximum: int = 4000) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path}.{field}: obrigatório")
        return ""
    if len(value) > maximum:
        errors.append(f"{path}.{field}: excede {maximum} caracteres")
    return value.strip()


def _unique_records(value: Any, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{label}: precisa ser uma lista")
        return {}
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value):
        path = f"{label}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path}: precisa ser objeto")
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            errors.append(f"{path}.id: use letras minúsculas, números e hífens (1–64 caracteres)")
            continue
        if identifier in result:
            errors.append(f"{path}.id: duplicado ({identifier})")
            continue
        result[identifier] = item
    return result


def _check_categories(item: dict[str, Any], path: str, categories: set[str], errors: list[str]) -> None:
    values = item.get("category_ids")
    if not isinstance(values, list) or not values:
        errors.append(f"{path}.category_ids: informe pelo menos uma categoria")
        return
    if any(not isinstance(value, str) or value not in categories for value in values):
        errors.append(f"{path}.category_ids: contém categoria inexistente")
    elif len(set(values)) != len(values):
        errors.append(f"{path}.category_ids: categoria repetida")


def _check_url(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or len(value) > 2048:
        errors.append(f"{path}: URL inválida")
        return
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        errors.append(f"{path}: use um endereço http(s) público sem credenciais")


def validate_catalog(data: Any) -> list[str]:
    """Retorna todos os problemas detectáveis sem alterar a entrada."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["catálogo: precisa ser objeto JSON"]
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version: esperado {SCHEMA_VERSION}")
    try:
        date.fromisoformat(data.get("updated_at", ""))
    except (TypeError, ValueError):
        errors.append("updated_at: use data ISO YYYY-MM-DD")

    categories = _unique_records(data.get("categories"), "categories", errors)
    references = _unique_records(data.get("references"), "references", errors)
    software = _unique_records(data.get("software"), "software", errors)
    category_ids = set(categories)

    for group_name, records in (("categories", categories), ("references", references), ("software", software)):
        for identifier, item in records.items():
            path = f"{group_name}.{identifier}"
            _required_text(item, "name", path, errors, maximum=160)
            aliases = item.get("aliases", [])
            if not isinstance(aliases, list) or any(not isinstance(alias, str) or len(alias) > 160 for alias in aliases):
                errors.append(f"{path}.aliases: lista de textos de até 160 caracteres")
            if group_name != "categories":
                _check_categories(item, path, category_ids, errors)
            elif not isinstance(item.get("aliases", []), list):
                errors.append(f"{path}.aliases: precisa ser uma lista")

    for identifier, item in software.items():
        path = f"software.{identifier}"
        _required_text(item, "summary", path, errors, maximum=500)
        _required_text(item, "license", path, errors, maximum=100)
        _required_text(item, "evidence_note", path, errors, maximum=800)
        _check_url(item.get("url"), f"{path}.url", errors)
        _check_url(item.get("source_url"), f"{path}.source_url", errors)
        source_state = item.get("source_state")
        if not isinstance(source_state, str) or source_state not in SOURCE_STATES:
            errors.append(f"{path}.source_state: use checked, reported ou unverified")
        elif source_state == "checked":
            try:
                date.fromisoformat(item.get("checked_at", ""))
            except (TypeError, ValueError):
                errors.append(f"{path}.checked_at: obrigatório quando a fonte está verificada; use YYYY-MM-DD")
        elif item.get("checked_at") not in (None, ""):
            try:
                date.fromisoformat(item["checked_at"])
            except (TypeError, ValueError):
                errors.append(f"{path}.checked_at: use data ISO YYYY-MM-DD")
        if not isinstance(item.get("pricing"), str) or item.get("pricing") not in PRICING:
            errors.append(f"{path}.pricing: valor inválido")
        if not isinstance(item.get("install_kind"), str) or item.get("install_kind") not in INSTALL_KINDS:
            errors.append(f"{path}.install_kind: valor inválido")
        platforms = item.get("platforms")
        if not isinstance(platforms, list) or not platforms or any(not isinstance(p, str) or p not in PLATFORMS for p in platforms):
            errors.append(f"{path}.platforms: informe plataformas conhecidas")
        elif len(set(platforms)) != len(platforms):
            errors.append(f"{path}.platforms: plataforma repetida")

    relations = data.get("relations")
    seen: set[tuple[str, str]] = set()
    if not isinstance(relations, list):
        errors.append("relations: precisa ser uma lista")
    else:
        for index, relation in enumerate(relations):
            path = f"relations[{index}]"
            if not isinstance(relation, dict):
                errors.append(f"{path}: precisa ser objeto")
                continue
            ref_id = relation.get("reference_id")
            software_id = relation.get("software_id")
            if not isinstance(ref_id, str) or ref_id not in references:
                errors.append(f"{path}.reference_id: referência inexistente")
            if not isinstance(software_id, str) or software_id not in software:
                errors.append(f"{path}.software_id: software inexistente")
            key = (str(ref_id), str(software_id))
            if key in seen:
                errors.append(f"{path}: relação duplicada")
            seen.add(key)
            if not isinstance(relation.get("match"), str) or relation.get("match") not in {"same_category", "related_category", "partial"}:
                errors.append(f"{path}.match: use same_category, related_category ou partial")
            _required_text(relation, "note", path, errors, maximum=800)
            if isinstance(ref_id, str) and ref_id in references and isinstance(software_id, str) and software_id in software:
                ref_categories = set(references[ref_id].get("category_ids", []))
                app_categories = set(software[software_id].get("category_ids", []))
                shares_category = bool(ref_categories.intersection(app_categories))
                match = relation.get("match")
                if match in {"same_category", "partial"} and not shares_category:
                    errors.append(f"{path}: same_category/partial exige categoria em comum")
                if match == "related_category" and shares_category:
                    errors.append(f"{path}: related_category exige categorias distintas")
    return errors


def search_catalog(data: dict[str, Any], query: str = "", *, category: str = "", platform: str = "", pricing: str = "", source_state: str = "") -> dict[str, Any]:
    """Busca por referência, alternativa ou categoria e explica a origem do ranking."""
    needle = normalize(query)
    categories = {item["id"]: item for item in data.get("categories", [])}
    references = {item["id"]: item for item in data.get("references", [])}
    software = {item["id"]: item for item in data.get("software", [])}
    matching_references = []
    if needle:
        for ref in references.values():
            searchable = [ref.get("name", ""), *ref.get("aliases", [])]
            if any(needle in normalize(value) or normalize(value) in needle for value in searchable):
                matching_references.append(ref)
    target_categories = set().union(*(set(ref.get("category_ids", [])) for ref in matching_references)) if matching_references else set()
    relation_by_software: dict[str, list[dict[str, Any]]] = {}
    for relation in data.get("relations", []):
        relation_by_software.setdefault(relation["software_id"], []).append(relation)

    rows = []
    for item in software.values():
        item_categories = set(item.get("category_ids", []))
        linked = [r for r in relation_by_software.get(item["id"], [])
                  if not matching_references or r["reference_id"] in {ref["id"] for ref in matching_references}]
        searchable = [item.get("name", ""), *item.get("aliases", [])]
        direct_match = bool(needle and any(needle in normalize(value) for value in searchable))
        category_match = bool(category and category in item_categories)
        query_category_match = bool(needle and any(needle in normalize(categories.get(cid, {}).get("name", ""))
                                                   or any(needle in normalize(alias) for alias in categories.get(cid, {}).get("aliases", []))
                                                   for cid in item_categories))
        if needle and not matching_references and not direct_match and not query_category_match:
            continue
        if matching_references and not linked:
            continue
        if category and not category_match:
            continue
        if platform and platform not in item.get("platforms", []):
            continue
        if pricing and item.get("pricing") != pricing:
            continue
        if source_state and item.get("source_state") != source_state:
            continue
        overlap = len(item_categories.intersection(target_categories))
        relation_rank = min(({"same_category": 0, "partial": 1, "related_category": 2}.get(r.get("match"), 9) for r in linked), default=3)
        rows.append({
            "software": item,
            "relations": linked,
            "references": [references[r["reference_id"]] for r in linked],
            "categories": [categories[cid] for cid in sorted(item_categories) if cid in categories],
            "category_overlap": overlap,
            "relation_rank": relation_rank,
            "source_rank": SOURCE_RANK.get(item.get("source_state"), 9),
        })
    rows.sort(key=lambda row: (-row["category_overlap"], row["relation_rank"], row["source_rank"], normalize(row["software"].get("name", ""))))

    suggestions = []
    if needle and not rows:
        scored = []
        for ref in references.values():
            names = [ref.get("name", ""), *ref.get("aliases", [])]
            ratio = max((SequenceMatcher(a=needle, b=normalize(name)).ratio() for name in names), default=0)
            if ratio >= 0.45:
                scored.append((ratio, ref))
        suggestions = [item[1] for item in sorted(scored, key=lambda pair: (-pair[0], normalize(pair[1]["name"])))[:5]]
    return {
        "query": query,
        "matched_references": matching_references,
        "results": rows,
        "suggestions": suggestions,
        "ranking": "categorias em comum; depois tipo de relação, fonte verificada, link informado e nome",
    }


def catalog_summary(data: dict[str, Any]) -> dict[str, int]:
    return {
        "categories": len(data.get("categories", [])),
        "references": len(data.get("references", [])),
        "software": len(data.get("software", [])),
        "relations": len(data.get("relations", [])),
        "checked_sources": sum(item.get("source_state") == "checked" for item in data.get("software", [])),
    }
