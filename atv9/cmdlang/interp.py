"""Interpretador de referencia, usado para validar os testes."""

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
    mem = {}
    for d in prog.decls:
        mem[d.nome] = _exp(d.exp, mem, ent)
    _cmds(prog.cmds, mem, ent)
    return _exp(prog.resultado, mem, ent)


def _cmds(lista, mem, ent):
    for c in lista:
        _cmd(c, mem, ent)


def _cmd(c, mem, ent):
    if isinstance(c, ast.Atrib):
        mem[c.nome] = _exp(c.exp, mem, ent)
    elif isinstance(c, ast.Leia):
        mem[c.nome] = w64(ent.numero())
    elif isinstance(c, ast.Se):
        if _exp(c.cond, mem, ent) != 0:
            _cmds(c.entao, mem, ent)
        else:
            _cmds(c.senao, mem, ent)
    elif isinstance(c, ast.Enquanto):
        while _exp(c.cond, mem, ent) != 0:
            _cmds(c.corpo, mem, ent)
    else:
        raise ErroExecucao("comando invalido: %r" % type(c).__name__)


def _exp(e, mem, ent):
    if isinstance(e, ast.Num):
        return w64(e.valor)
    if isinstance(e, ast.Var):
        return mem[e.nome]
    if isinstance(e, ast.Nao):
        return 1 if _exp(e.exp, mem, ent) == 0 else 0
    if isinstance(e, ast.Logico):
        esq = _exp(e.esq, mem, ent) != 0
        if e.op == "and":
            return 1 if esq and _exp(e.dir, mem, ent) != 0 else 0
        return 1 if esq or _exp(e.dir, mem, ent) != 0 else 0
    if isinstance(e, ast.BinOp):
        a = _exp(e.esq, mem, ent)
        b = _exp(e.dir, mem, ent)
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
