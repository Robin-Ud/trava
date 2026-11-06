**Trava** — card novo fica suspenso até o pré-requisito ser aprendido. *Primeiro a tag, depois as subtags.*

- `decks`: lista de decks onde o Trava age (inclui subdecks). Vazio = desligado. Ex.: `["Botânica"]`.
- `min_intervalo`: dias de intervalo pra um card contar como aprendido (ele precisa estar em revisão).
- `fracao_pai`: num nó sem porteiro, fração dos cards dele que precisa estar aprendida pras subtags abrirem (1.0 = todos).
- `ignorar`: prefixos de tag que não fazem parte da árvore (ex.: `["bot::nivel", "fonte"]`).
- `avisar`: aviso no canto da tela quando algo destranca durante a revisão.

Tags que o Trava entende (o menu do botão direito no Navegar põe pra você):
- `trava::porteiro`: o card que abre o nó dele; o resto do nó espera ele.
- `trava::id::X` + `trava::precisa::X`: ligação avulsa fora da árvore.
- `trava::trancado`: posta pelo próprio Trava. Ele só destranca o que tem essa tag.

Depois de mudar, use Ferramentas › Trava › Recalcular.
