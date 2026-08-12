"""Interpretador de referencia, usado como oraculo nos testes.

Estende o interpretador da linguagem Cmd com ambiente de execucao para
funcoes: cada chamada cria um dicionario local novo (parametros e
variaveis locais), e a leitura de uma variavel primeiro tenta o
dicionario local corrente e so' depois cai para o dicionario global --
o mesmo sombreamento usado na analise semantica e na geracao de codigo.
"""

import sys

from . import ast
from .erros import ErroExecucao

MASCARA = (1 << 64) - 1
LIMITE = 1 << 63


def w64(v):
    """Trunca para inteiro de 64 bits com sinal, como o registrador."""
    v &= MASCARA
    return v - (1 << 64) if v >= LIMITE else v


def div(a, b):
    if b == 0:
        raise ErroExecucao("divisao por zero")
    q = abs(a) // abs(b)  # trunca em direcao a zero, como IDIV
    return w64(-q if (a < 0) != (b < 0) else q)


class Entrada:
    """Fonte de numeros para o comando read."""

    def __init__(self, texto=None):
        self.itens = texto.split() if texto is not None else None
        self.i = 0

    def numero(self):
        if self.itens is None:
            linha = sys.stdin.readline()
            if not linha:
                raise ErroExecucao("entrada vazia")
            return int(linha.split()[0])
        if self.i >= len(self.itens):
            raise ErroExecucao("entrada insuficiente")
        v = int(self.itens[self.i])
        self.i += 1
        return v


def executar(prog, entrada=None):
    """Roda o programa e devolve o valor da expressao de resultado."""
    ent = entrada if isinstance(entrada, Entrada) else Entrada(entrada)
    glob = {}
    funcs = {}
    for d in prog.decls:
        if isinstance(d, ast.Decl):
            glob[d.nome] = _exp(d.exp, glob, None, funcs, ent)
        elif isinstance(d, ast.FunDecl):
            funcs[d.nome] = d
        else:
            raise ErroExecucao("declaracao invalida: %r" % type(d).__name__)
    _cmds(prog.cmds, glob, None, funcs, ent)
    return _exp(prog.resultado, glob, None, funcs, ent)


def _chamar(node, glob, local, funcs, ent):
    f = funcs[node.nome]
    valores = [_exp(a, glob, local, funcs, ent) for a in node.args]
    novo_local = {}
    for pnome, v in zip(f.params, valores):
        novo_local[pnome] = v
    for vd in f.vardecls:
        novo_local[vd.nome] = _exp(vd.exp, glob, novo_local, funcs, ent)
    _cmds(f.cmds, glob, novo_local, funcs, ent)
    return _exp(f.resultado, glob, novo_local, funcs, ent)


def _cmds(lista, glob, local, funcs, ent):
    for c in lista:
        _cmd(c, glob, local, funcs, ent)


def _cmd(c, glob, local, funcs, ent):
    if isinstance(c, ast.Atrib):
        v = _exp(c.exp, glob, local, funcs, ent)
        if local is not None and c.nome in local:
            local[c.nome] = v
        else:
            glob[c.nome] = v
    elif isinstance(c, ast.Leia):
        v = w64(ent.numero())
        if local is not None and c.nome in local:
            local[c.nome] = v
        else:
            glob[c.nome] = v
    elif isinstance(c, ast.Se):
        if _exp(c.cond, glob, local, funcs, ent) != 0:
            _cmds(c.entao, glob, local, funcs, ent)
        else:
            _cmds(c.senao, glob, local, funcs, ent)
    elif isinstance(c, ast.Enquanto):
        while _exp(c.cond, glob, local, funcs, ent) != 0:
            _cmds(c.corpo, glob, local, funcs, ent)
    else:
        raise ErroExecucao("comando invalido: %r" % type(c).__name__)


def _exp(e, glob, local, funcs, ent):
    if isinstance(e, ast.Num):
        return w64(e.valor)
    if isinstance(e, ast.Var):
        if local is not None and e.nome in local:
            return local[e.nome]
        return glob[e.nome]
    if isinstance(e, ast.Nao):
        return 1 if _exp(e.exp, glob, local, funcs, ent) == 0 else 0
    if isinstance(e, ast.Logico):
        esq = _exp(e.esq, glob, local, funcs, ent) != 0
        if e.op == "and":
            return 1 if esq and _exp(e.dir, glob, local, funcs, ent) != 0 else 0
        return 1 if esq or _exp(e.dir, glob, local, funcs, ent) != 0 else 0
    if isinstance(e, ast.Chamada):
        return _chamar(e, glob, local, funcs, ent)
    if isinstance(e, ast.BinOp):
        a = _exp(e.esq, glob, local, funcs, ent)
        b = _exp(e.dir, glob, local, funcs, ent)
        op = e.op
        if op == "+":
            return w64(a + b)
        if op == "-":
            return w64(a - b)
        if op == "*":
            return w64(a * b)
        if op == "/":
            return div(a, b)
        if op == "==":
            return 1 if a == b else 0
        if op == "!=":
            return 1 if a != b else 0
        if op == "<":
            return 1 if a < b else 0
        if op == ">":
            return 1 if a > b else 0
        if op == "<=":
            return 1 if a <= b else 0
        return 1 if a >= b else 0
    raise ErroExecucao("expressao invalida: %r" % type(e).__name__)
