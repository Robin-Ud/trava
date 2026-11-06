"""Roda o regras.py contra a coleção real via AnkiConnect, sem gravar nada.

  python3 simula.py            # relatório por tag-raiz
  python3 simula.py -v         # + lista o que destrancaria agora

Precisa do Anki aberto (AnkiConnect em localhost:8765).
Lê config.local.json se existir, senão config.json.
"""
import json
import os
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import regras  # noqa: E402


def ac(action, **params):
    req = urllib.request.Request("http://localhost:8765", json.dumps(
        {"action": action, "version": 6, "params": params}).encode())
    r = json.load(urllib.request.urlopen(req))
    if r["error"]:
        raise Exception(r["error"])
    return r["result"]


def config():
    for nome in ("config.local.json", "config.json"):
        p = os.path.join(AQUI, nome)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)


def consulta(decks):
    return "(" + " OR ".join(f'"deck:{d}"' for d in decks) + ")"


def coleta(cfg):
    if not cfg["decks"]:
        return []
    ids = ac("findCards", query=consulta(cfg["decks"]))
    info = ac("cardsInfo", cards=ids)
    tags = {n["noteId"]: n["tags"] for n in ac("notesInfo", notes=list({c["note"] for c in info}))}
    out = []
    for c in info:
        frente = min(c["fields"].values(), key=lambda f: f["order"])["value"]
        out.append({"id": c["cardId"], "nota": c["note"], "tags": tags[c["note"]],
                    "frente": frente, "type": c["type"], "ivl": c["interval"], "queue": c["queue"]})
    return out


def main():
    cfg = config()
    cards = coleta(cfg)
    r = regras.decide(cards, cfg)
    print(f"{len(cards)} cards em {', '.join(cfg['decks']) or '(nenhum deck no config)'} · "
          f"aprendido = revisão com ivl ≥ {cfg['min_intervalo']} d\n")
    print(regras.texto_relatorio(r))
    print(f"\nagora: trancaria {len(r['trancar'])}, destrancaria {len(r['destrancar'])}")
    if "-v" in sys.argv:
        frente = {c["id"]: regras.HTML_RE.sub("", c["frente"])[:70] for c in cards}
        for i in r["destrancar"]:
            print("  +", frente[i])


if __name__ == "__main__":
    main()
