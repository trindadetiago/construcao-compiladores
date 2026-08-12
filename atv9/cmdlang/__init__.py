"""Compilador da linguagem Cmd."""

from . import ast, codigo, erros, interp, lexico, semantico, sintatico

__all__ = ["ast", "codigo", "erros", "interp", "lexico", "semantico", "sintatico", "compilar"]


def compilar(texto):
    """Fonte Cmd para assembly x86_64. Devolve (asm, programa, tabela)."""
    prog = sintatico.analisar(texto)
    tab = semantico.analisar(prog)
    return codigo.gerar(prog, tab), prog, tab
