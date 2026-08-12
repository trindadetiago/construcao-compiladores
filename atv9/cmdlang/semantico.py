"""Analise semantica: tabela de simbolos e uso de variaveis."""

from . import ast
from .erros import ErroSemantico


class TabelaSimbolos:
    """Ordem de declaracao preservada para a secao BSS."""

    def __init__(self):
        self.ordem = []
        self.mapa = {}

    def declara(self, nome, linha, coluna):
        if nome in self.mapa:
            raise ErroSemantico("variavel %r ja declarada" % nome, linha, coluna)
        self.mapa[nome] = len(self.ordem)
        self.ordem.append(nome)

    def existe(self, nome):
        return nome in self.mapa

    def __iter__(self):
        return iter(self.ordem)

    def __len__(self):
        return len(self.ordem)


def analisar(prog):
    """Valida o programa e devolve a tabela de simbolos."""
    tab = TabelaSimbolos()

    # declaracoes: lado direito so usa o que ja foi declarado
    for d in prog.decls:
        _checa_exp(d.exp, tab)
        tab.declara(d.nome, d.linha, d.coluna)

    _checa_cmds(prog.cmds, tab)
    _checa_exp(prog.resultado, tab)
    return tab


def _checa_cmds(cmds, tab):
    for c in cmds:
        _checa_cmd(c, tab)


def _checa_cmd(c, tab):
    if isinstance(c, ast.Atrib):
        _checa_exp(c.exp, tab)  # lado direito
        if not tab.existe(c.nome):  # lado esquerdo
            raise ErroSemantico(
                "atribuicao a variavel nao declarada %r" % c.nome, c.linha, c.coluna
            )
        return
    if isinstance(c, ast.Leia):
        if not tab.existe(c.nome):
            raise ErroSemantico(
                "leitura em variavel nao declarada %r" % c.nome, c.linha, c.coluna
            )
        return
    if isinstance(c, ast.Se):
        _checa_exp(c.cond, tab)
        _checa_cmds(c.entao, tab)
        _checa_cmds(c.senao, tab)
        return
    if isinstance(c, ast.Enquanto):
        _checa_exp(c.cond, tab)
        _checa_cmds(c.corpo, tab)
        return
    raise ErroSemantico("comando desconhecido %r" % type(c).__name__, 0, 0)


def _checa_exp(e, tab):
    if isinstance(e, ast.Num):
        return
    if isinstance(e, ast.Var):
        if not tab.existe(e.nome):
            raise ErroSemantico(
                "variavel nao declarada %r" % e.nome, e.linha, e.coluna
            )
        return
    if isinstance(e, (ast.BinOp, ast.Logico)):
        _checa_exp(e.esq, tab)
        _checa_exp(e.dir, tab)
        return
    if isinstance(e, ast.Nao):
        _checa_exp(e.exp, tab)
        return
    raise ErroSemantico("expressao desconhecida %r" % type(e).__name__, 0, 0)
