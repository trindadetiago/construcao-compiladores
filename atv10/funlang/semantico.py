"""Analise semantica: tabela de simbolos global + tabelas locais por funcao.

Segue o esquema da secao 5.2 do guia: a tabela global guarda, para cada
nome, se ele denota uma variavel global ou uma funcao (com sua aridade e
sua tabela local). Ao analisar o corpo de uma funcao f, o compilador
consulta primeiro a tabela local de f e, se nao encontrar, cai para a
tabela global -- o que implementa o sombreamento de variavel global por
parametro/variavel local descrito na secao 2.
"""

from . import ast
from .erros import ErroSemantico


class Escopo:
    """Tabela local de uma funcao: parametros e variaveis locais.

    Guarda duas listas ordenadas (parametros e locais, nessa ordem de
    declaracao) porque a geracao de codigo calcula o deslocamento de cada
    uma de forma diferente (secao 6.1.3 do guia).
    """

    def __init__(self):
        self.params = []
        self.locais = []
        self.mapa = {}  # nome -> ("param", indice) ou ("local", indice)

    def declara_param(self, nome, linha, coluna):
        if nome in self.mapa:
            raise ErroSemantico("parametro %r repetido" % nome, linha, coluna)
        self.mapa[nome] = ("param", len(self.params))
        self.params.append(nome)

    def declara_local(self, nome, linha, coluna):
        if nome in self.mapa:
            raise ErroSemantico(
                "variavel local %r ja declarada (ou e' parametro)" % nome, linha, coluna
            )
        self.mapa[nome] = ("local", len(self.locais))
        self.locais.append(nome)

    def existe(self, nome):
        return nome in self.mapa

    def offset(self, nome):
        """Deslocamento em relacao a RBP, em bytes (secao 6.1.3)."""
        kind, idx = self.mapa[nome]
        l = len(self.locais)
        if kind == "local":
            return idx * 8
        return l * 8 + 16 + idx * 8

    def nlocais(self):
        return len(self.locais)

    def nparams(self):
        return len(self.params)


class TabelaGlobal:
    """Ordem de declaracao das variaveis globais preservada para a BSS."""

    def __init__(self):
        self.vars_ordem = []
        self.mapa = {}  # nome -> ("var",) ou ("fun", nparams, Escopo)

    def declara_var(self, nome, linha, coluna):
        if nome in self.mapa:
            raise ErroSemantico("simbolo %r ja declarado" % nome, linha, coluna)
        self.mapa[nome] = ("var",)
        self.vars_ordem.append(nome)

    def declara_fun(self, nome, escopo, linha, coluna):
        if nome in self.mapa:
            raise ErroSemantico("simbolo %r ja declarado" % nome, linha, coluna)
        self.mapa[nome] = ("fun", len(escopo.params), escopo)

    def existe(self, nome):
        return nome in self.mapa

    def eh_var(self, nome):
        return self.mapa[nome][0] == "var"

    def eh_fun(self, nome):
        return self.mapa[nome][0] == "fun"

    def nparams(self, nome):
        return self.mapa[nome][1]

    def escopo_de(self, nome):
        return self.mapa[nome][2]

    def __iter__(self):
        return iter(self.vars_ordem)

    def __len__(self):
        return len(self.vars_ordem)


def analisar(prog):
    """Valida o programa e devolve a tabela global (com as tabelas locais)."""
    tab = TabelaGlobal()

    for d in prog.decls:
        if isinstance(d, ast.Decl):
            _checa_exp(d.exp, tab, None)
            tab.declara_var(d.nome, d.linha, d.coluna)
        elif isinstance(d, ast.FunDecl):
            _analisa_funcao(d, tab)
        else:
            raise ErroSemantico("declaracao desconhecida %r" % type(d).__name__, 0, 0)

    _checa_cmds(prog.cmds, tab, None)
    _checa_exp(prog.resultado, tab, None)
    return tab


def _analisa_funcao(d, tab):
    escopo = Escopo()
    for p in d.params:
        escopo.declara_param(p, d.linha, d.coluna)

    # registra a funcao ANTES de checar o corpo, para permitir recursao
    # direta (secao 5.1 do guia): dentro do corpo de f, uma chamada a f
    # ja encontra f na tabela global.
    if tab.existe(d.nome):
        raise ErroSemantico("simbolo %r ja declarado" % d.nome, d.linha, d.coluna)
    tab.declara_fun(d.nome, escopo, d.linha, d.coluna)

    for vd in d.vardecls:
        _checa_exp(vd.exp, tab, escopo)
        escopo.declara_local(vd.nome, vd.linha, vd.coluna)

    _checa_cmds(d.cmds, tab, escopo)
    _checa_exp(d.resultado, tab, escopo)


def _checa_cmds(cmds, tab, escopo):
    for c in cmds:
        _checa_cmd(c, tab, escopo)


def _checa_cmd(c, tab, escopo):
    if isinstance(c, ast.Atrib):
        _checa_exp(c.exp, tab, escopo)  # lado direito
        _checa_alvo(c.nome, tab, escopo, c.linha, c.coluna)
        return
    if isinstance(c, ast.Leia):
        _checa_alvo(c.nome, tab, escopo, c.linha, c.coluna)
        return
    if isinstance(c, ast.Se):
        _checa_exp(c.cond, tab, escopo)
        _checa_cmds(c.entao, tab, escopo)
        _checa_cmds(c.senao, tab, escopo)
        return
    if isinstance(c, ast.Enquanto):
        _checa_exp(c.cond, tab, escopo)
        _checa_cmds(c.corpo, tab, escopo)
        return
    raise ErroSemantico("comando desconhecido %r" % type(c).__name__, 0, 0)


def _checa_alvo(nome, tab, escopo, linha, coluna):
    """Verifica o alvo de uma atribuicao/leitura: variavel local ou global."""
    if escopo is not None and escopo.existe(nome):
        return
    if tab.existe(nome) and tab.eh_var(nome):
        return
    if tab.existe(nome) and tab.eh_fun(nome):
        raise ErroSemantico(
            "%r e' uma funcao, nao pode ser usada como variavel" % nome, linha, coluna
        )
    raise ErroSemantico("variavel nao declarada %r" % nome, linha, coluna)


def _checa_exp(e, tab, escopo):
    if isinstance(e, ast.Num):
        return
    if isinstance(e, ast.Var):
        if escopo is not None and escopo.existe(e.nome):
            return
        if tab.existe(e.nome) and tab.eh_var(e.nome):
            return
        if tab.existe(e.nome) and tab.eh_fun(e.nome):
            raise ErroSemantico(
                "%r e' uma funcao, use %s(...) para chama-la" % (e.nome, e.nome),
                e.linha, e.coluna,
            )
        raise ErroSemantico("variavel nao declarada %r" % e.nome, e.linha, e.coluna)
    if isinstance(e, (ast.BinOp, ast.Logico)):
        _checa_exp(e.esq, tab, escopo)
        _checa_exp(e.dir, tab, escopo)
        return
    if isinstance(e, ast.Nao):
        _checa_exp(e.exp, tab, escopo)
        return
    if isinstance(e, ast.Chamada):
        _checa_chamada(e, tab, escopo)
        return
    raise ErroSemantico("expressao desconhecida %r" % type(e).__name__, 0, 0)


def _checa_chamada(e, tab, escopo):
    # uma funcao so pode ser local (nunca ha' chamada a nome local que
    # nao seja funcao global, ja que Fun nao permite funcoes aninhadas)
    if not tab.existe(e.nome) or not tab.eh_fun(e.nome):
        if escopo is not None and escopo.existe(e.nome):
            raise ErroSemantico(
                "%r e' uma variavel, nao pode ser chamada como funcao" % e.nome,
                e.linha, e.coluna,
            )
        if tab.existe(e.nome) and tab.eh_var(e.nome):
            raise ErroSemantico(
                "%r e' uma variavel, nao pode ser chamada como funcao" % e.nome,
                e.linha, e.coluna,
            )
        raise ErroSemantico("funcao nao declarada %r" % e.nome, e.linha, e.coluna)

    esperado = tab.nparams(e.nome)
    obtido = len(e.args)
    if obtido != esperado:
        raise ErroSemantico(
            "funcao %r espera %d parametro(s), chamada com %d" % (e.nome, esperado, obtido),
            e.linha, e.coluna,
        )
    for a in e.args:
        _checa_exp(a, tab, escopo)
