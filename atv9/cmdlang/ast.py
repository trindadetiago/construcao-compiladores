"""Arvore sintatica abstrata da linguagem Cmd."""

from dataclasses import dataclass, field
from typing import List, Optional


class No:
    pass


# expressoes

@dataclass
class Num(No):
    valor: int
    linha: int = 0
    coluna: int = 0


@dataclass
class Var(No):
    nome: str
    linha: int = 0
    coluna: int = 0


@dataclass
class BinOp(No):
    """Aritmetica e comparacao."""
    op: str
    esq: No
    dir: No
    linha: int = 0
    coluna: int = 0


@dataclass
class Logico(No):
    """and e or, com curto circuito."""
    op: str
    esq: No
    dir: No
    linha: int = 0
    coluna: int = 0


@dataclass
class Nao(No):
    exp: No
    linha: int = 0
    coluna: int = 0


# comandos

@dataclass
class Decl(No):
    nome: str
    exp: No
    linha: int = 0
    coluna: int = 0


@dataclass
class Atrib(No):
    nome: str
    exp: No
    linha: int = 0
    coluna: int = 0


@dataclass
class Se(No):
    cond: No
    entao: List[No]
    senao: List[No] = field(default_factory=list)
    linha: int = 0
    coluna: int = 0


@dataclass
class Enquanto(No):
    cond: No
    corpo: List[No]
    linha: int = 0
    coluna: int = 0


@dataclass
class Leia(No):
    nome: str
    linha: int = 0
    coluna: int = 0


@dataclass
class Programa(No):
    decls: List[Decl]
    cmds: List[No]
    resultado: No


def imprime(no, nivel=0):
    """Dump textual da arvore, usado no modo ast."""
    pad = "  " * nivel
    if isinstance(no, Programa):
        linhas = [pad + "Programa"]
        for d in no.decls:
            linhas.append(imprime(d, nivel + 1))
        linhas.append(pad + "  Corpo")
        for c in no.cmds:
            linhas.append(imprime(c, nivel + 2))
        linhas.append(pad + "  Return")
        linhas.append(imprime(no.resultado, nivel + 2))
        return "\n".join(linhas)
    if isinstance(no, Decl):
        return pad + "Decl %s\n" % no.nome + imprime(no.exp, nivel + 1)
    if isinstance(no, Atrib):
        return pad + "Atrib %s\n" % no.nome + imprime(no.exp, nivel + 1)
    if isinstance(no, Leia):
        return pad + "Leia %s" % no.nome
    if isinstance(no, Se):
        linhas = [pad + "Se", imprime(no.cond, nivel + 1), pad + "  Entao"]
        linhas += [imprime(c, nivel + 2) for c in no.entao]
        linhas.append(pad + "  Senao")
        linhas += [imprime(c, nivel + 2) for c in no.senao]
        return "\n".join(linhas)
    if isinstance(no, Enquanto):
        linhas = [pad + "Enquanto", imprime(no.cond, nivel + 1), pad + "  Corpo"]
        linhas += [imprime(c, nivel + 2) for c in no.corpo]
        return "\n".join(linhas)
    if isinstance(no, (BinOp, Logico)):
        return (pad + "%s\n" % no.op) + imprime(no.esq, nivel + 1) + "\n" + imprime(no.dir, nivel + 1)
    if isinstance(no, Nao):
        return pad + "not\n" + imprime(no.exp, nivel + 1)
    if isinstance(no, Num):
        return pad + str(no.valor)
    if isinstance(no, Var):
        return pad + no.nome
    return pad + repr(no)
