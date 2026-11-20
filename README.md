# Troca Justa

ESCOPO: o que é o projeto, onde mora cada parte e como o catálogo cresce.

Catálogo próprio de alternativas gratuitas ou de código aberto, em português. Implementação independente: não copia o código, os textos nem a base do MakeFree/Tech Robin Hood. O link para o site de referência fica no rodapé.

## Onde mora cada parte

| Parte | Onde | O que faz |
|---|---|---|
| Site público | `docs/` (GitHub Pages, `main` → `/docs`) | Busca no navegador sobre `docs/catalog.json`. Só leitura: sem formulário, sem API, sem rastreador. |
| Sugestão | Issue com o formulário "Sugerir alternativa" | Qualquer pessoa sugere. O issue é público. |
| Catalogador | `catalog_core.py`, `catalog_intake.py`, `catalog_tool.py` | Valida o catálogo, busca e transforma a sugestão num registro **pendente** (`reported`), com checagens automáticas na fonte oficial. |
| Rotina | `.github/workflows/catalogador.yml` (GitHub Actions) | A cada sugestão, abre uma PR com o registro. Toda segunda, valida o catálogo e roda os testes. |
| Revisão | A PR | Uma pessoa lê a fonte, reescreve o resumo, confere preço, licença e sistemas e, se a fonte confirmar, muda para `checked`. O merge publica. |

## Método do catálogo

1. Toda sugestão entra como pendente, com data, motivo, site oficial e área.
2. A rotina confere o que não pede julgamento: se o site responde e, para repositório do GitHub, a licença declarada, o último push e se está arquivado. O resultado vai para a nota de evidência.
3. A revisão humana separa o fato da inferência: a fonte confirma o quê, em que data. "Mesma área" não quer dizer "mesmos recursos".
4. Uma entrada só vira "fonte conferida" depois que alguém leu a fonte oficial.

## Comandos

```sh
./catalog-tool validate
./catalog-tool search Photoshop --json
./catalog-tool intake --event evento.json   # o que o Actions roda a cada sugestão
python3 -m unittest discover -s tests
```

Prévia local do site: `cd docs && python3 -m http.server 8766`, depois abra `http://127.0.0.1:8766`.
