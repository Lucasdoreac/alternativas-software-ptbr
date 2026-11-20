"""A sugestão de teste usa um nome fictício: um nome real pode entrar no catálogo e transformar o teste de
registro novo num teste de duplicado (aconteceu com o Krita em 2026-11-20).

CAMINHO COBERTO: catalog_intake.parse_issue_form e intake (issue form -> registro "reported" válido),
check_source com rede injetada, a CLI `intake` sobre um evento do GitHub, e a guarda de que o site público
em docs/ só busca: sem formulário de escrita, sem API e sem curadoria exposta.

REVERT-CHECK: com `intake` gravando `source_state="checked"`, test_sugestao_vira_registro_pendente falha;
sem a checagem de https público, test_site_que_nao_e_https_publico_e_recusado falha; com o formulário de
curadoria de volta em docs/index.html ou `/api/` em docs/app.js, test_site_publico_so_busca falha.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from catalog_core import validate_catalog  # noqa: E402
from catalog_intake import IntakeError, check_source, intake, parse_issue_form  # noqa: E402

BODY = """### Nome da alternativa

Exemplo Livre de Teste

### Site oficial do projeto

https://exemplo-livre.org/

### Substitui qual software

Adobe Photoshop

### Área

Edição de imagem

### Área nova (só se escolheu Outra)

_No response_

### Sistemas em que roda

- [X] macOS
- [ ] Windows
- [X] Linux

### Por que é uma boa alternativa

Pintura digital e edição de imagens com camadas.
"""


def catalog() -> dict:
    return json.loads((ROOT / "docs" / "catalog.json").read_text(encoding="utf-8"))


def fake_check(url: str) -> dict:
    return {"url": url, "reachable": True, "final_url": url, "license": None, "pushed_at": None,
            "archived": None, "github_repo": None}


class IntakeTest(unittest.TestCase):
    def test_formulario_e_lido_com_sistemas_marcados(self) -> None:
        form = parse_issue_form(BODY)
        self.assertEqual(form["name"], "Exemplo Livre de Teste")
        self.assertEqual(form["platforms"], ["macOS", "Linux"])
        self.assertEqual(form["area_other"], "")

    def test_sugestao_vira_registro_pendente(self) -> None:
        new, software_id, _ = intake(catalog(), parse_issue_form(BODY), issue_number=7, today="2026-11-20",
                                     check=fake_check)
        self.assertEqual(validate_catalog(new), [])
        record = next(item for item in new["software"] if item["id"] == software_id)
        self.assertEqual(record["source_state"], "reported")
        self.assertIn("Falta a revisão humana", record["evidence_note"])
        relation = next(r for r in new["relations"] if r["software_id"] == software_id)
        self.assertEqual(relation["reference_id"], "photoshop")

    def test_duplicado_e_recusado(self) -> None:
        body = BODY.replace("Exemplo Livre de Teste", "GIMP")
        with self.assertRaisesRegex(IntakeError, "já está no catálogo"):
            intake(catalog(), parse_issue_form(body), issue_number=8, today="2026-11-20", check=fake_check)

    def test_site_que_nao_e_https_publico_e_recusado(self) -> None:
        for url in ("http://krita.org/", "https://localhost/x", "https://127.0.0.1/", "https://10.0.0.2/"):
            with self.assertRaisesRegex(IntakeError, "https público"):
                intake(catalog(), parse_issue_form(BODY.replace("https://exemplo-livre.org/", url)), issue_number=9,
                       today="2026-11-20", check=fake_check)

    def test_area_nova_cria_categoria(self) -> None:
        body = BODY.replace("Edição de imagem\n", "Outra\n").replace(
            "### Área nova (só se escolheu Outra)\n\n_No response_", "### Área nova (só se escolheu Outra)\n\nPintura digital")
        new, software_id, _ = intake(catalog(), parse_issue_form(body), issue_number=10, today="2026-11-20",
                                     check=fake_check)
        self.assertIn("pintura-digital", {c["id"] for c in new["categories"]})
        self.assertEqual(validate_catalog(new), [])

    def test_checagem_do_github_le_licenca_e_arquivamento(self) -> None:
        result = check_source("https://github.com/KDE/krita", fetch=lambda url: (200, url),
                              fetch_json=lambda url: {"license": {"spdx_id": "GPL-3.0"}, "pushed_at": "2026-11-19T10:00:00Z",
                                                      "archived": False})
        self.assertEqual((result["license"], result["pushed_at"], result["github_repo"]),
                         ("GPL-3.0", "2026-11-19", "KDE/krita"))

    def test_falha_de_rede_e_registrada_sem_excecao(self) -> None:
        def boom(url: str):
            raise OSError("sem rede")
        result = check_source("https://krita.org/", fetch=boom)
        self.assertFalse(result["reachable"])
        self.assertEqual(result["error"], "OSError")

    def test_cli_intake_grava_o_catalogo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            path.write_text((ROOT / "docs" / "catalog.json").read_text(encoding="utf-8"), encoding="utf-8")
            event = Path(tmp) / "event.json"
            body = BODY.replace("https://exemplo-livre.org/", "http://exemplo-livre.org/")  # recusado antes de qualquer rede
            event.write_text(json.dumps({"issue": {"number": 11, "body": body}}), encoding="utf-8")
            run = subprocess.run([sys.executable, str(ROOT / "catalog_tool.py"), "--catalog", str(path), "intake",
                                  "--event", str(event)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 3, run.stderr)
            self.assertIn("https público", json.loads(run.stdout)["error"])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), catalog())


class PublicSiteTest(unittest.TestCase):
    def test_site_publico_so_busca(self) -> None:
        html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")
        self.assertEqual(html.count("<form"), 1)
        self.assertNotIn("<textarea", html)
        for forbidden in ("/api/", "method:", "localStorage"):
            self.assertNotIn(forbidden, script)
        self.assertIn("techrobinhood.com", html)
        self.assertIn("sugerir-alternativa.yml", html)

    def test_catalogo_publicado_e_valido(self) -> None:
        self.assertEqual(validate_catalog(catalog()), [])


if __name__ == "__main__":
    unittest.main()
