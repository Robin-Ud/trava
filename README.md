# Trava

Add-on do Anki: card novo fica **suspenso até o pré-requisito dele ser aprendido**. *Primeiro a tag, depois as subtags.* Puro Python, zero deps (só o que já vem no Anki).

## A regra

Tag hierárquica vira árvore. Um card mora na tag mais funda dele (`Mat::Cálculo::Derivada`).

- **Subtag espera a tag-pai.** Os cards de `Mat::Cálculo` só aparecem quando os de `Mat` estão aprendidos (todos, ou a fração `fracao_pai`). Pai sem card nenhum → olha o avô.
- **Porteiro** (`trava::porteiro`): o card que abre o nó dele. O resto do nó espera só ele, e ele espera o porteiro do nó-pai. Serve pra quando você não quer terminar a tag inteira antes das subtags.
- **Ligação avulsa:** `trava::id::X` num card e `trava::precisa::X` em outro → o segundo espera o primeiro, mesmo em árvores diferentes.

"Aprendido" = card em revisão com intervalo ≥ 7 dias (`min_intervalo`). Quando você responde um card e ele passa disso, o que dependia dele destranca na hora, vai pra **frente da fila de novos** e aparece um aviso no canto da tela.

### Exemplo: o deck Botânica

```
bot::Rosales                      porteiro "Rosales — clado?"
  └ traço-ordem                     espera ↑
bot::Rosales::Rosaceae            porteiro "Rosaceae — ordem?"   (espera Rosales)
  └ traço, sinônimo                 esperam ↑
bot::Rosales::Rosaceae::Prunus    porteiro "Prunus — família?"   (espera Rosaceae)
  └ foto, origem                    esperam ↑
```

As tags do Botânica são postas por `~/deving/facul/botanica/tags_trava.py`.

## Uso

1. Ferramentas › Complementos › Instalar do arquivo › `trava.ankiaddon`, e reinicia o Anki.
2. Ferramentas › Complementos › Trava › Configurar → coloca o deck em `"decks"`. Vazio = desligado.
3. Pra marcar porteiro e ligação: Navegar › seleciona os cards › botão direito › **Trava**.
4. **Ferramentas › Trava › Relatório** mostra o que está trancado e por quê; **Recalcular** aplica na hora.

- Só tranca card **novo**. O que você já começou nunca sai da fila.
- Trancar = suspender + tag `trava::trancado`. Ele só destranca o que tem essa tag, então suspensão sua nunca é desfeita.
- Recalcula ao abrir o perfil, depois do sync e a cada resposta. O destrancar entra no mesmo Ctrl+Z da resposta.
- Celular: AnkiDroid e AnkiMobile não rodam add-on. Lá o card só fica suspenso até alguém sincronizar com o desktop.

## Desenvolvimento

```bash
./trava_test.sh        # testes com cards falsos
python3 simula.py      # o que ele faria na coleção real (Anki aberto + AnkiConnect; não grava)
./instala.sh           # copia pro addons21 do flatpak (usa config.local.json) e gera trava.ankiaddon
```

| arquivo | o quê |
|---|---|
| `regras.py` | lógica pura (sem Anki) |
| `__init__.py` | hooks, menus, grava na coleção |
| `config.json` / `config.md` | config padrão e a ajuda que aparece na GUI |
| `config.local.json` | config da minha máquina (fora do git e do pacote) |

---

## English

**Trava** ("lock") keeps new cards suspended until their prerequisite is learned (in review with interval ≥ `min_intervalo` days). Prerequisites come from **hierarchical tags**: cards in `A::B` wait for the cards in `A`. Tag one card per node with `trava::porteiro` ("gatekeeper") so the node opens as soon as that card is learned, instead of waiting for the whole parent tag. Tag `trava::id::X` + `trava::precisa::X` for one-off links across trees. It only locks *new* cards, only unsuspends what it suspended itself (`trava::trancado`), and puts unlocked cards at the front of the new queue. Opt-in per deck (`decks` in the config). Browser right-click › Trava to set gatekeepers and links. License: AGPL-3.0.
