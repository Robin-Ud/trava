"""Lógica pura do Trava: decide quem tranca e quem destranca.

Não importa nada do Anki, então roda e testa fora dele (trava_test.sh, simula.py).

Regra: **primeiro a tag, depois as subtags.**
  - O nó de um card = suas tags-folha (tag que não é prefixo de outra tag do mesmo card),
    tirando `ignorar` e as tags trava::.
  - Porteiro (trava::porteiro) abre o nó: o resto do nó espera ele ser aprendido,
    e ele espera o nó-pai liberar.
  - Nó sem porteiro espera o nó-pai liberar.
  - Pai libera = porteiro aprendido; sem porteiro, `fracao_pai` dos cards dele aprendidos;
    sem card nenhum, sobe pro avô. Acabou a árvore = livre.
  - trava::precisa::X espera algum card com trava::id::X aprendido (ligação fora da árvore).

Cada card chega como dict:
  {"id": int, "nota": int, "tags": [str], "frente": str,
   "type": int, "ivl": int, "queue": int}
  type 0 = novo, 1/3 = aprendendo, 2 = revisão; queue -1 = suspenso.
"""
import re
from collections import defaultdict

TRAVA = "trava::"
TRANCADO = "trava::trancado"
PORTEIRO = "trava::porteiro"
ID = "trava::id::"
PRECISA = "trava::precisa::"
HTML_RE = re.compile(r"<[^>]+>")


def _tags(card):
    return [t.lower() for t in card["tags"]]


def _ignorado(tag, ignorar):
    return tag.startswith(TRAVA) or any(tag == p or tag.startswith(p + "::") for p in ignorar)


def nos(card, ignorar=()):
    """Tags-folha do card (minúsculas): o(s) nó(s) onde ele mora."""
    ign = [p.lower() for p in ignorar]
    ts = [t for t in _tags(card) if not _ignorado(t, ign)]
    return sorted({t for t in ts if not any(o.startswith(t + "::") for o in ts)})


def pai(no):
    return no.rsplit("::", 1)[0] if "::" in no else None


def aprendido(card, min_intervalo):
    return card["type"] == 2 and card["ivl"] >= min_intervalo


def trancado(card):
    return TRANCADO in _tags(card)


def porteiro(card):
    return PORTEIRO in _tags(card)


def _com_prefixo(card, prefixo):
    return [t[len(prefixo):] for t in _tags(card) if t.startswith(prefixo)]


class Arvore:
    def __init__(self, cards, cfg):
        self.n = cfg.get("min_intervalo", 7)
        self.fracao = cfg.get("fracao_pai", 1.0)
        self.ignorar = cfg.get("ignorar", [])
        self.no_de = {c["id"]: nos(c, self.ignorar) for c in cards}
        self.cards_no = defaultdict(list)
        self.porteiros = defaultdict(list)
        self.ids = defaultdict(list)
        for c in cards:
            for no in self.no_de[c["id"]]:
                self.cards_no[no].append(c)
                if porteiro(c):
                    self.porteiros[no].append(c)
            for x in _com_prefixo(c, ID):
                self.ids[x].append(c)
        self._libera = {}

    def libera(self, no):
        """O nó `no` já liberou os filhos?"""
        if no is None:
            return True
        if no not in self._libera:
            ps = self.porteiros.get(no)
            if ps:
                ok = any(aprendido(c, self.n) for c in ps)
            else:
                # suspensão manual (sem a tag do Trava) não conta
                cs = [c for c in self.cards_no.get(no, []) if not (c["queue"] == -1 and not trancado(c))]
                if cs:
                    ok = sum(aprendido(c, self.n) for c in cs) >= self.fracao * len(cs) - 1e-9
                else:
                    ok = self.libera(pai(no))
            self._libera[no] = ok
        return self._libera[no]

    def espera(self, c):
        """Lista de motivos pelos quais o card ainda espera ([] = livre)."""
        motivos = []
        for no in self.no_de[c["id"]]:
            if porteiro(c) or not self.porteiros.get(no):
                if not self.libera(pai(no)):
                    motivos.append(f"pai {pai(no)}")
            elif not any(aprendido(p, self.n) for p in self.porteiros[no]):
                motivos.append(f"porteiro {no}")
        for x in _com_prefixo(c, PRECISA):
            alvo = self.ids.get(x)
            if alvo and not any(aprendido(p, self.n) for p in alvo):
                motivos.append(f"precisa {x}")
        return motivos


def _raiz(arv, c):
    ns = arv.no_de[c["id"]]
    return ns[0].split("::")[0] if ns else "(sem tag)"


def decide(cards, cfg):
    """Devolve {"trancar": [ids], "destrancar": [ids], "relatorio": {...}, "motivos": {...}}.

    Só tranca card novo; destranca só card com a tag trava::trancado.
    """
    arv = Arvore(cards, cfg)
    trancar, destrancar = [], []
    rel = defaultdict(lambda: defaultdict(int))
    motivos = defaultdict(int)
    for c in cards:
        raiz = _raiz(arv, c)
        preso = trancado(c)
        espera = arv.espera(c)
        if espera:
            if c["type"] == 0:
                if not (preso and c["queue"] == -1):
                    trancar.append(c["id"])
                rel[raiz]["trancado"] += 1
                motivos[espera[0].split(" ")[0]] += 1
            else:
                if preso:
                    destrancar.append(c["id"])  # já começado: nunca fica preso
                rel[raiz]["ja_comecado"] += 1
        else:
            if preso:
                destrancar.append(c["id"])
            rel[raiz]["livre"] += 1
    return {"trancar": trancar, "destrancar": destrancar,
            "relatorio": {k: dict(v) for k, v in rel.items()}, "motivos": dict(motivos)}


def texto_relatorio(r):
    linhas = [f"{'tag-raiz':24} {'trancado':>9} {'livre':>7} {'começado':>9}"]
    for raiz in sorted(r["relatorio"]):
        d = r["relatorio"][raiz]
        linhas.append(f"{raiz[:24]:24} {d.get('trancado', 0):9} {d.get('livre', 0):7} {d.get('ja_comecado', 0):9}")
    if r["motivos"]:
        nomes = {"porteiro": "esperando o porteiro do nó", "pai": "esperando o nó-pai",
                 "precisa": "esperando trava::precisa"}
        linhas.append("\ntrancados por:")
        for k, v in sorted(r["motivos"].items(), key=lambda kv: -kv[1]):
            linhas.append(f"  {nomes.get(k, k)}: {v}")
    return "\n".join(linhas)
