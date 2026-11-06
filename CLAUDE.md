# Trava — notas pro Claude

- Add-on do Anki 26.09 (flatpak). Instalado por **cópia** em `~/.var/app/net.ankiweb.Anki/data/Anki2/addons21/trava/` via `instala.sh`; o flatpak não lê `~/deving`, então symlink não funciona. Editou → `./instala.sh` → reiniciar o Anki.
- `config.json` = padrão publicado (`decks: []`, desligado). `config.local.json` = config do Matheus (Botânica + `ignorar` das tags `bot::` que não são árvore); o instala.sh copia por cima; fora do git e do `.ankiaddon`.
- `regras.py` não pode importar `aqt`/`anki`: é ele que os testes e o `simula.py` usam fora do Anki.
- Modelo: nó = tag-folha (fora `ignorar` e `trava::`). Porteiro abre o nó e espera o pai liberar. Nó sem porteiro espera o pai. Pai libera = porteiro aprendido ou `fracao_pai` dos cards dele; pai sem card → avô.
- Hooks: `profile_did_open`, `sync_did_finish`, `reviewer_did_answer_card` (roda depois da resposta gravada e antes do `nextCard()`; junta no `undo_status().last_step`), `browser_will_show_context_menu`. Menus usam `CollectionOp`, pra tela atualizar sozinha.
- Suposição: a tag fica na nota, então todos os cards de uma nota andam juntos.
- Nunca destrancar card sem `trava::trancado`: o Matheus tem suspensões manuais (`corte-flori`).
- Teste de gravação sem tocar na coleção real: copiar `collection.anki2` pro scratchpad e rodar com `flatpak run --filesystem=<dir> --command=python3 net.ankiweb.Anki`, fingindo `aqt`/`aqt.qt`/`aqt.utils`/`aqt.operations` (feito em 2026-11-06, v1 e v2 ok).
- v1 (esquema `bot::` fixo) foi trocada pela v2 (genérica) em 2026-11-06. As duas trancaram exatamente os mesmos 1059 cards.
- Não publicado ainda (GitHub/AnkiWeb): só com o ok do Matheus.
