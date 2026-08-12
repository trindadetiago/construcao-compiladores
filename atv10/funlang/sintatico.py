"""Analise sintatica: descida recursiva para a linguagem Fun.

Estende o parser da linguagem Cmd (atividade 9) com:
* declaracoes de variavel agora exigem a palavra-chave 'var';
* declaracoes de funcao ('fun nome(params) { ... }');
* o bloco principal agora e' marcado por 'main';
* chamada de funcao como expressao primaria, diferenciada de uma
  referencia a variavel olhando o token seguinte ao identificador
  (secao 4 do guia).
"""

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

    # programa: decl* 'main' '{' cmd* 'return' exp ';' '}'

    def programa(self):
        decls = []
        while self.eh(PAL, "var") or self.eh(PAL, "fun"):
            if self.eh(PAL, "var"):
                decls.append(self.declaracao_var())
            else:
                decls.append(self.declaracao_fun())
        self.exige(PAL, "main")
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

    def declaracao_var(self):
        self.exige(PAL, "var")
        t = self.exige(ID)
        self.exige(OP, "=")
        e = self.expressao()
        self.exige(PONT, ";")
        return ast.Decl(t.valor, e, t.linha, t.coluna)

    def declaracao_fun(self):
        t = self.exige(PAL, "fun")
        nome = self.exige(ID)
        self.exige(PONT, "(")
        params = self.lista_parametros_formais()
        self.exige(PONT, ")")
        self.exige(PONT, "{")
        vardecls = []
        while self.eh(PAL, "var"):
            vardecls.append(self.declaracao_var())
        cmds = self.lista_comandos()
        self.exige(PAL, "return")
        res = self.expressao()
        self.exige(PONT, ";")
        self.exige(PONT, "}")
        return ast.FunDecl(nome.valor, params, vardecls, cmds, res, t.linha, t.coluna)

    def lista_parametros_formais(self):
        """<arglist>? : zero ou mais identificadores separados por virgula."""
        if self.eh(PONT, ")"):
            return []
        params = [self.exige(ID).valor]
        while self.eh(PONT, ","):
            self.come()
            params.append(self.exige(ID).valor)
        return params

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
            # olha o token seguinte para diferenciar variavel de chamada
            # de funcao (secao 4 do guia)
            se_abre_parenteses = self.olha(1).tipo == PONT and self.olha(1).valor == "("
            if se_abre_parenteses:
                return self.chamada()
            self.come()
            return ast.Var(t.valor, t.linha, t.coluna)
        if self.eh(PONT, "("):
            self.come()
            e = self.expressao()
            self.exige(PONT, ")")
            return e
        achado = t.valor if t.tipo != FIM else "fim de arquivo"
        raise ErroSintatico("expressao invalida perto de %r" % achado, t.linha, t.coluna)

    def chamada(self):
        t = self.exige(ID)
        self.exige(PONT, "(")
        args = self.lista_parametros_reais()
        self.exige(PONT, ")")
        return ast.Chamada(t.valor, args, t.linha, t.coluna)

    def lista_parametros_reais(self):
        """<params>? : zero ou mais expressoes separadas por virgula."""
        if self.eh(PONT, ")"):
            return []
        args = [self.expressao()]
        while self.eh(PONT, ","):
            self.come()
            args.append(self.expressao())
        return args


def analisar(texto):
    return Parser(texto).programa()
