"""Analise sintatica: descida recursiva para a linguagem Cmd."""

from . import ast
from .erros import ErroSintatico
from .lexico import FIM, ID, NUM, OP, PAL, PONT, tokenizar

COMPARACOES = ("<", ">", "==", "<=", ">=", "!=")


class Parser:
    def __init__(self, texto):
        self.toks = tokenizar(texto)
        self.p = 0

    # utilitarios

    def olha(self, k=0):
        j = min(self.p + k, len(self.toks) - 1)
        return self.toks[j]

    def come(self):
        t = self.toks[self.p]
        if t.tipo != FIM:
            self.p += 1
        return t

    def eh(self, tipo, valor=None):
        t = self.olha()
        return t.tipo == tipo and (valor is None or t.valor == valor)

    def exige(self, tipo, valor=None):
        t = self.olha()
        if not self.eh(tipo, valor):
            esperado = valor if valor is not None else tipo
            achado = t.valor if t.tipo != FIM else "fim de arquivo"
            raise ErroSintatico(
                "esperava %r, encontrou %r" % (esperado, achado), t.linha, t.coluna
            )
        return self.come()

    # programa

    def programa(self):
        decls = []
        while self.eh(ID):
            decls.append(self.declaracao())
        self.exige(PONT, "{")
        cmds = self.lista_comandos()
        self.exige(PAL, "return")
        res = self.expressao()
        self.exige(PONT, ";")
        self.exige(PONT, "}")
        t = self.olha()
        if t.tipo != FIM:
            raise ErroSintatico("lixo apos o fim do programa", t.linha, t.coluna)
        return ast.Programa(decls, cmds, res)

    def declaracao(self):
        t = self.exige(ID)
        self.exige(OP, "=")
        e = self.expressao()
        self.exige(PONT, ";")
        return ast.Decl(t.valor, e, t.linha, t.coluna)

    # comandos

    def lista_comandos(self):
        cmds = []
        while True:
            if self.eh(PAL, "if"):
                cmds.append(self.comando_se())
            elif self.eh(PAL, "while"):
                cmds.append(self.comando_enquanto())
            elif self.eh(PAL, "read"):
                cmds.append(self.comando_leia())
            elif self.eh(ID):
                cmds.append(self.comando_atrib())
            else:
                return cmds

    def bloco(self):
        self.exige(PONT, "{")
        cmds = self.lista_comandos()
        self.exige(PONT, "}")
        return cmds

    def comando_se(self):
        t = self.exige(PAL, "if")
        cond = self.expressao()
        entao = self.bloco()
        senao = []
        if self.eh(PAL, "else"):  # else opcional
            self.come()
            senao = self.bloco()
        return ast.Se(cond, entao, senao, t.linha, t.coluna)

    def comando_enquanto(self):
        t = self.exige(PAL, "while")
        cond = self.expressao()
        corpo = self.bloco()
        return ast.Enquanto(cond, corpo, t.linha, t.coluna)

    def comando_leia(self):
        t = self.exige(PAL, "read")
        v = self.exige(ID)
        self.exige(PONT, ";")
        return ast.Leia(v.valor, t.linha, t.coluna)

    def comando_atrib(self):
        t = self.exige(ID)
        self.exige(OP, "=")
        e = self.expressao()
        self.exige(PONT, ";")
        return ast.Atrib(t.valor, e, t.linha, t.coluna)

    # expressoes, da menor para a maior precedencia

    def expressao(self):
        return self.exp_ou()

    def exp_ou(self):
        e = self.exp_e()
        while self.eh(PAL, "or"):
            t = self.come()
            e = ast.Logico("or", e, self.exp_e(), t.linha, t.coluna)
        return e

    def exp_e(self):
        e = self.exp_nao()
        while self.eh(PAL, "and"):
            t = self.come()
            e = ast.Logico("and", e, self.exp_nao(), t.linha, t.coluna)
        return e

    def exp_nao(self):
        if self.eh(PAL, "not"):
            t = self.come()
            return ast.Nao(self.exp_nao(), t.linha, t.coluna)
        return self.exp_comp()

    def exp_comp(self):
        e = self.exp_aditiva()
        while self.olha().tipo == OP and self.olha().valor in COMPARACOES:
            t = self.come()
            e = ast.BinOp(t.valor, e, self.exp_aditiva(), t.linha, t.coluna)
        return e

    def exp_aditiva(self):
        e = self.exp_mult()
        while self.olha().tipo == OP and self.olha().valor in ("+", "-"):
            t = self.come()
            e = ast.BinOp(t.valor, e, self.exp_mult(), t.linha, t.coluna)
        return e

    def exp_mult(self):
        e = self.primaria()
        while self.olha().tipo == OP and self.olha().valor in ("*", "/"):
            t = self.come()
            e = ast.BinOp(t.valor, e, self.primaria(), t.linha, t.coluna)
        return e

    def primaria(self):
        t = self.olha()
        if t.tipo == NUM:
            self.come()
            return ast.Num(t.valor, t.linha, t.coluna)
        if t.tipo == ID:
            self.come()
            return ast.Var(t.valor, t.linha, t.coluna)
        if self.eh(PONT, "("):
            self.come()
            e = self.expressao()
            self.exige(PONT, ")")
            return e
        achado = t.valor if t.tipo != FIM else "fim de arquivo"
        raise ErroSintatico("expressao invalida perto de %r" % achado, t.linha, t.coluna)


def analisar(texto):
    return Parser(texto).programa()
