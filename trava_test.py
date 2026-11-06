"""Testes do regras.py com cards falsos (não toca no Anki)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regras  # noqa: E402
from regras import PORTEIRO, TRANCADO  # noqa: E402

CFG = {"min_intervalo": 7, "fracao_pai": 1.0, "ignorar": ["bot::nivel"]}
_id = iter(range(1, 100_000))


def card(*tags, ivl=0, type=None, queue=0):
    i = next(_id)
    if type is None:
        type = 2 if ivl else 0
    return {"id": i, "nota": i, "tags": list(tags), "frente": "", "type": type, "ivl": ivl, "queue": queue}


def decide(*cards, **cfg):
    return regras.decide(list(cards), {**CFG, **cfg})


def trancados(r):
    return set(r["trancar"])


class TagDepoisSubtag(unittest.TestCase):
    def test_subtag_espera_a_tag_inteira(self):
        a1, a2 = card("Mat"), card("Mat", ivl=10)
        b = card("Mat::Topico")
        r = decide(a1, a2, b)
        self.assertEqual(trancados(r), {b["id"]})  # a1 ainda é novo → b espera

    def test_tag_toda_aprendida_libera(self):
        a1, a2 = card("Mat", ivl=7), card("Mat", ivl=30)
        b = card("Mat::Topico")
        self.assertEqual(trancados(decide(a1, a2, b)), set())

    def test_fracao_pai(self):
        a1, a2 = card("Mat", ivl=7), card("Mat")
        b = card("Mat::Topico")
        self.assertIn(b["id"], trancados(decide(a1, a2, b)))
        self.assertNotIn(b["id"], trancados(decide(a1, a2, b, fracao_pai=0.5)))

    def test_ivl_6_nao_basta(self):
        a, b = card("Mat", ivl=6), card("Mat::Topico")
        self.assertIn(b["id"], trancados(decide(a, b)))

    def test_pai_sem_card_sobe_pro_avo(self):
        avo = card("A")
        neto = card("A::B::C")  # A::B não tem card
        self.assertIn(neto["id"], trancados(decide(avo, neto)))
        self.assertEqual(trancados(decide(card("A", ivl=9), card("A::B::C"))), set())

    def test_raiz_sem_pai_e_livre(self):
        self.assertEqual(trancados(decide(card("Mat"), card("Outra"))), set())

    def test_tag_nao_folha_nao_conta(self):
        # card com "Mat" e "Mat::Topico" mora só em Mat::Topico
        self.assertEqual(regras.nos(card("Mat", "Mat::Topico")), ["mat::topico"])

    def test_ignorar_e_trava(self):
        c = card("bot", "bot::nivel::familia", "bot::Rosales", PORTEIRO, TRANCADO)
        self.assertEqual(regras.nos(c, CFG["ignorar"]), ["bot::rosales"])


class Porteiro(unittest.TestCase):
    def botanica(self, ordem=0, fam=0, gen=0):
        return {
            "ordem": card("bot::Rosales", PORTEIRO, ivl=ordem),
            "traco_ordem": card("bot::Rosales"),
            "familia": card("bot::Rosales::Rosaceae", PORTEIRO, ivl=fam),
            "traco": card("bot::Rosales::Rosaceae"),
            "genero": card("bot::Rosales::Rosaceae::Prunus", PORTEIRO, ivl=gen),
            "foto": card("bot::Rosales::Rosaceae::Prunus"),
        }

    def ids(self, d, *ks):
        return {d[k]["id"] for k in ks}

    def test_nada_aprendido(self):
        d = self.botanica()
        self.assertEqual(trancados(decide(*d.values())), self.ids(d, "traco_ordem", "familia", "traco", "genero", "foto"))

    def test_ordem_aprendida(self):
        d = self.botanica(ordem=7)
        # porteiro de família abre só com o porteiro da ordem — não precisa do traço-ordem
        self.assertEqual(trancados(decide(*d.values())), self.ids(d, "traco", "genero", "foto"))

    def test_familia_aprendida(self):
        d = self.botanica(ordem=7, fam=7)
        self.assertEqual(trancados(decide(*d.values())), self.ids(d, "foto"))

    def test_tudo(self):
        d = self.botanica(ordem=7, fam=7, gen=7)
        self.assertEqual(trancados(decide(*d.values())), set())


class Seguranca(unittest.TestCase):
    def test_destranca_quem_tem_a_tag(self):
        a = card("Mat", ivl=7)
        b = card("Mat::T", TRANCADO, queue=-1)
        self.assertEqual(decide(a, b)["destrancar"], [b["id"]])

    def test_suspensao_manual_nunca_destranca(self):
        a = card("Mat", ivl=7)
        b = card("Mat::T", queue=-1)
        self.assertEqual(decide(a, b)["destrancar"], [])

    def test_suspensao_manual_no_pai_nao_segura(self):
        a1, a2 = card("Mat", ivl=7), card("Mat", queue=-1)
        b = card("Mat::T")
        self.assertEqual(trancados(decide(a1, a2, b)), set())

    def test_ja_trancado_nao_repete(self):
        a, b = card("Mat"), card("Mat::T", TRANCADO, queue=-1)
        r = decide(a, b)
        self.assertEqual(r["trancar"], [])
        self.assertEqual(r["relatorio"]["mat"]["trancado"], 1)

    def test_comecado_nunca_tranca(self):
        a, b = card("Mat"), card("Mat::T", ivl=2)
        self.assertEqual(trancados(decide(a, b)), set())


class Ligacao(unittest.TestCase):
    def test_precisa_id(self):
        x = card("Fisica", "trava::id::derivada")
        y = card("Quimica", "trava::precisa::derivada")
        self.assertEqual(trancados(decide(x, y)), {y["id"]})
        x["type"], x["ivl"] = 2, 10
        self.assertEqual(trancados(decide(x, y)), set())

    def test_precisa_sem_id_e_livre(self):
        self.assertEqual(trancados(decide(card("Q", "trava::precisa::nada"))), set())

    def test_precisa_e_arvore_juntas(self):
        x = card("F", "trava::id::d", ivl=10)
        pai = card("Q")
        y = card("Q::T", "trava::precisa::d")
        self.assertEqual(trancados(decide(x, pai, y)), {y["id"]})


if __name__ == "__main__":
    unittest.main()
