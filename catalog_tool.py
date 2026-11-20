"""CLI determinística do catalogador: valida, busca e transforma sugestões em registros pendentes de revisão."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from datetime import date

from catalog_core import catalog_summary, search_catalog, validate_catalog
from catalog_intake import IntakeError, intake, parse_issue_form


DEFAULT_CATALOG = Path(__file__).resolve().parent / "docs" / "catalog.json"
DEFAULT_METRICS = Path.home() / ".local" / "state" / "troca-justa" / "metrics.jsonl"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="catalog-tool", description="Validar e consultar o catálogo Troca Justa")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validar estrutura, fontes e relações")
    sub.add_parser("health", help="verificar prontidão sem alterar estado")
    sub.add_parser("metrics", help="ler contagens locais sem termos de busca")
    take = sub.add_parser("intake", help="transformar a sugestão de um issue em registro pendente de revisão")
    take.add_argument("--event", type=Path, required=True, help="JSON do evento do GitHub (GITHUB_EVENT_PATH)")
    take.add_argument("--today", default="", help="data ISO; padrão: hoje")
    search = sub.add_parser("search", help="buscar alternativas por nome ou categoria")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--category", default="")
    search.add_argument("--platform", default="")
    search.add_argument("--pricing", choices=("free", "freemium", "paid", "unknown"), default="")
    search.add_argument("--source-state", choices=("checked", "reported", "unverified"), default="")
    search.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        if args.command == "metrics":
            counts: Counter[str] = Counter()
            recent = []
            try:
                if DEFAULT_METRICS.is_symlink():
                    raise OSError("métrica simbólica recusada")
                for line in DEFAULT_METRICS.read_text(encoding="utf-8").splitlines():
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    counts[f"{entry.get('action', 'unknown')}:{entry.get('status', 'unknown')}"] += 1
                    recent.append(entry)
            except OSError:
                pass
            print(json.dumps({"counts": dict(sorted(counts.items())), "recent": recent[-20:], "stores_queries": False}, ensure_ascii=False))
            return 0
        data = load(args.catalog)
        if args.command == "intake":
            issue = json.loads(args.event.read_text(encoding="utf-8")).get("issue") or {}
            try:
                new, software_id, check = intake(data, parse_issue_form(issue.get("body") or ""),
                                                 issue_number=int(issue.get("number") or 0),
                                                 today=args.today or date.today().isoformat())
            except IntakeError as error:
                print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
                return 3
            args.catalog.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"ok": True, "software_id": software_id, "check": check}, ensure_ascii=False))
            return 0
        errors = validate_catalog(data)
        if args.command == "validate":
            if errors:
                print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False))
                return 1
            print(json.dumps({"valid": True, "summary": catalog_summary(data)}, ensure_ascii=False))
            return 0
        if args.command == "health":
            result = {"ready": not errors, "catalog_path": str(args.catalog.resolve()),
                      "summary": catalog_summary(data), "errors": errors}
            print(json.dumps(result, ensure_ascii=False))
            return 0 if not errors else 1
        if errors:
            print(json.dumps({"error": "catálogo inválido", "details": errors}, ensure_ascii=False), file=sys.stderr)
            return 1
        result = search_catalog(data, args.query, category=args.category, platform=args.platform,
                                pricing=args.pricing, source_state=args.source_state)
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            if result["matched_references"]:
                print("Referência: " + ", ".join(item["name"] for item in result["matched_references"]))
            for row in result["results"]:
                item = row["software"]
                print(f"{item['name']} | {', '.join(category['name'] for category in row['categories'])} | fonte: {item['source_state']}")
                print(f"  {item['source_url']}")
            if not result["results"]:
                print("Nenhum resultado catalogado.")
            print("Ordem: " + result["ranking"])
        return 0
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": f"catálogo não pode ser lido ({type(error).__name__})"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
