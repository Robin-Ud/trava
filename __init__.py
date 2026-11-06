"""Trava — add-on do Anki: card novo fica suspenso até o pré-requisito ser aprendido.

Primeiro a tag, depois as subtags (detalhes em regras.py). A lógica fica em regras.py
(pura, testável fora do Anki); aqui é só a cola: hooks, menus e gravação na coleção.
"""
from anki.collection import OpChanges
from anki.utils import ids2str
from aqt import gui_hooks, mw
from aqt.operations import CollectionOp
from aqt.qt import QAction, QMenu
from aqt.utils import getText, showText, tooltip

from . import regras


def cfg():
    return mw.addonManager.getConfig(__name__)


def coleta(col, c):
    decks = c.get("decks") or []
    if not decks:
        return []
    ids = col.find_cards("(" + " OR ".join(f'"deck:{d}"' for d in decks) + ")")
    if not ids:
        return []
    rows = col.db.all(
        "select c.id, c.nid, c.type, c.ivl, c.queue, n.tags, n.flds "
        f"from cards c join notes n on n.id = c.nid where c.id in {ids2str(ids)}")
    return [{"id": cid, "nota": nid, "type": typ, "ivl": ivl, "queue": queue,
             "tags": tags.split(), "frente": flds.split("\x1f")[0]}
            for cid, nid, typ, ivl, queue, tags, flds in rows]


def aplica(col, r, cards):
    """Grava trancar/destrancar. Devolve as frentes do que foi destrancado."""
    nota = {x["id"]: x["nota"] for x in cards}
    if r["trancar"]:
        col.sched.suspend_cards(r["trancar"])
        col.tags.bulk_add(list({nota[i] for i in r["trancar"]}), regras.TRANCADO)
    if r["destrancar"]:
        soltos = set(r["destrancar"])
        col.sched.unsuspend_cards(r["destrancar"])
        col.tags.bulk_remove(list({nota[i] for i in soltos}), regras.TRANCADO)
        novos = [x["id"] for x in cards if x["id"] in soltos and x["type"] == 0]
        if novos:  # vai pra frente da fila de novos
            col.sched.reposition_new_cards(novos, starting_from=0, step_size=1,
                                           randomize=False, shift_existing=True)
    frente = {x["id"]: regras.HTML_RE.sub("", x["frente"]) for x in cards}
    return [frente[i] for i in r["destrancar"]]


def recalcula(col, merge_em=None):
    """Recalcula tudo. `merge_em` = passo de desfazer onde juntar as mudanças
    (None = cria um passo "Trava"). Devolve (resultado, destrancados, OpChanges)."""
    cards = coleta(col, cfg())
    r = regras.decide(cards, cfg())
    if not (r["trancar"] or r["destrancar"]):
        return r, [], OpChanges()
    alvo = merge_em if merge_em is not None else col.add_custom_undo_entry("Trava")
    soltos = aplica(col, r, cards)
    return r, soltos, col.merge_undo_entries(alvo)


def aviso(soltos):
    if soltos and cfg().get("avisar", True):
        mais = f" e +{len(soltos) - 3}" if len(soltos) > 3 else ""
        tooltip("Destrancou: " + " · ".join(soltos[:3]) + mais, period=4000)


# hooks ####################################################################

def ao_abrir():
    if mw.col is not None:
        aviso(recalcula(mw.col)[1])


def ao_responder(reviewer, card, ease):
    # a resposta já foi gravada; o destrancar entra no mesmo Ctrl+Z dela
    aviso(recalcula(mw.col, merge_em=mw.col.undo_status().last_step)[1])


# menus ####################################################################

def roda(parent, antes=None, msg=None):
    """Recalcula como CollectionOp (a tela atualiza sozinha). `antes(col)` roda no mesmo passo."""
    estado = {}

    def op(col):
        alvo = col.add_custom_undo_entry("Trava")
        if antes:
            antes(col)
        r, soltos, _ = recalcula(col, merge_em=alvo)
        estado.update(r=r, soltos=soltos)
        return col.merge_undo_entries(alvo)

    def fim(_):
        r = estado["r"]
        tooltip((msg + " · " if msg else "") +
                f"Trava: trancou {len(r['trancar'])}, destrancou {len(estado['soltos'])}")

    CollectionOp(parent, op).success(fim).run_in_background()


def menu_relatorio():
    c = cfg()
    if not c.get("decks"):
        showText("O Trava não está agindo em nenhum deck.\n\n"
                 "Ferramentas › Complementos › Trava › Configurar → ponha o nome em \"decks\".",
                 title="Trava")
        return
    r = regras.decide(coleta(mw.col, c), c)
    showText(f"Decks: {', '.join(c['decks'])} · aprendido = revisão com intervalo ≥ {c['min_intervalo']} d\n\n"
             + regras.texto_relatorio(r)
             + f"\n\npendente: trancar {len(r['trancar'])}, destrancar {len(r['destrancar'])}"
               " (Recalcular aplica)", title="Trava", copyBtn=True)


def monta_menu():
    m = QMenu("Trava", mw)
    for nome, fn in (("Recalcular", lambda: roda(mw)), ("Relatório", menu_relatorio)):
        a = QAction(nome, mw)
        a.triggered.connect(fn)
        m.addAction(a)
    mw.form.menuTools.addMenu(m)


def _nome(browser, pergunta):
    txt, ok = getText(pergunta, parent=browser, title="Trava")
    txt = "_".join(txt.strip().split())
    return txt.replace("::", "_") if ok and txt else None


def menu_navegar(browser, menu):
    notas = list(browser.selected_notes())
    if not notas:
        return
    m = menu.addMenu("Trava")

    def porteiro():
        col = mw.col
        todos = all(regras.PORTEIRO in [t.lower() for t in col.get_note(n).tags] for n in notas)
        if todos:
            roda(browser, lambda c: c.tags.bulk_remove(notas, regras.PORTEIRO), "porteiro desmarcado")
        else:
            roda(browser, lambda c: c.tags.bulk_add(notas, regras.PORTEIRO), "porteiro marcado")

    def pre():
        x = _nome(browser, "Nome deste pré-requisito (ex.: derivada):")
        if x:
            roda(browser, lambda c: c.tags.bulk_add(notas, regras.ID + x), f"pré-requisito {x}")

    def depende():
        x = _nome(browser, "Estes cards dependem de qual pré-requisito?")
        if x:
            roda(browser, lambda c: c.tags.bulk_add(notas, regras.PRECISA + x), f"depende de {x}")

    for nome, fn in (("Marcar/desmarcar porteiro", porteiro),
                     ("Marcar como pré-requisito…", pre),
                     ("Depende de…", depende)):
        m.addAction(nome).triggered.connect(fn)


monta_menu()
gui_hooks.profile_did_open.append(ao_abrir)
gui_hooks.sync_did_finish.append(ao_abrir)
gui_hooks.reviewer_did_answer_card.append(ao_responder)
gui_hooks.browser_will_show_context_menu.append(menu_navegar)
