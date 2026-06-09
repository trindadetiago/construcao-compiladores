#!/usr/bin/env python3
"""Analisador sintatico da linguagem EC1 (Expressoes Constantes 1).

Le um arquivo de entrada (passado como argumento na linha de comando),
realiza a analise lexica e sintatica, produz a arvore de sintaxe abstrata
(AST), interpreta o programa por varredura da arvore e imprime o resultado.

Saida normal (entrada valida):
    <valor inteiro da expressao>

Com a opcao --arvore, imprime tambem a arvore em notacao parentesizada antes
do valor:
    <representacao da arvore>
    <valor>

Erros lexicos ou sintaticos sao reportados em stderr e o programa termina
com codigo de saida diferente de zero.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Analisador lexico (reutilizado da Atividade 04)
# ---------------------------------------------------------------------------

NUMERO = "Numero"
PAREN_ESQ = "ParenEsq"
PAREN_DIR = "ParenDir"
SOMA = "Soma"
SUB = "Sub"
MULT = "Mult"
DIV = "Div"
EOF = "EOF"

SIMBOLOS = {
    "(": PAREN_ESQ,
    ")": PAREN_DIR,
    "+": SOMA,
    "-": SUB,
    "*": MULT,
    "/": DIV,
}

ESPACOS = {" ", "\t", "\n", "\r"}


class ErroLexico(Exception):
    """Erro lexico: caractere invalido encontrado na posicao informada."""

    def __init__(self, posicao: int, caractere: str):
        self.posicao = posicao
        self.caractere = caractere
        super().__init__(
            f"Erro lexico na posicao {posicao}: caractere invalido '{caractere}'"
        )


class Token:
    """Um token: tipo (classe lexica), lexema (string da entrada) e posicao."""

    def __init__(self, tipo: str, lexema: str, posicao: int):
        self.tipo = tipo
        self.lexema = lexema
        self.posicao = posicao

    def __str__(self) -> str:
        return f'<{self.tipo}, "{self.lexema}", {self.posicao}>'


class Lexer:
    """Analisador lexico com interface proximo_token() sobre uma string."""

    def __init__(self, entrada: str):
        self.entrada = entrada
        self.pos = 0

    def _pular_espacos(self) -> None:
        while self.pos < len(self.entrada) and self.entrada[self.pos] in ESPACOS:
            self.pos += 1

    def proximo_token(self) -> Token:
        """Retorna o proximo token da entrada (ou um token EOF no final).

        Levanta ErroLexico se encontrar um caractere fora do alfabeto EC1.
        """
        self._pular_espacos()

        if self.pos >= len(self.entrada):
            return Token(EOF, "", self.pos)

        inicio = self.pos
        c = self.entrada[self.pos]

        if c.isdigit():
            while self.pos < len(self.entrada) and self.entrada[self.pos].isdigit():
                self.pos += 1
            lexema = self.entrada[inicio : self.pos]
            return Token(NUMERO, lexema, inicio)

        if c in SIMBOLOS:
            self.pos += 1
            return Token(SIMBOLOS[c], c, inicio)

        raise ErroLexico(inicio, c)


# ---------------------------------------------------------------------------
# Arvore de sintaxe abstrata (AST)
# ---------------------------------------------------------------------------

# Representacao do operador como string legivel.
_SIMBOLO_OP = {SOMA: "+", SUB: "-", MULT: "*", DIV: "/"}


class Exp:
    """Classe base abstrata para nos da arvore de sintaxe abstrata."""

    def avaliar(self) -> int:  # pragma: no cover
        raise NotImplementedError

    def imprimir(self) -> str:  # pragma: no cover
        raise NotImplementedError


class Const(Exp):
    """No folha: uma constante inteira."""

    def __init__(self, valor: int):
        self.valor = valor

    def avaliar(self) -> int:
        return self.valor

    def imprimir(self) -> str:
        return str(self.valor)


class OpBin(Exp):
    """No interno: uma operacao binaria com operandos esquerdo e direito."""

    def __init__(self, operador: str, esq: Exp, dir: Exp):
        self.operador = operador   # tipo do token: SOMA | SUB | MULT | DIV
        self.esq = esq
        self.dir = dir

    def avaliar(self) -> int:
        ve = self.esq.avaliar()
        vd = self.dir.avaliar()
        if self.operador == SOMA:
            return ve + vd
        if self.operador == SUB:
            return ve - vd
        if self.operador == MULT:
            return ve * vd
        if self.operador == DIV:
            if vd == 0:
                raise ZeroDivisionError("divisao por zero na expressao")
            return ve // vd
        raise RuntimeError(f"operador desconhecido: {self.operador}")  # pragma: no cover

    def imprimir(self) -> str:
        simbolo = _SIMBOLO_OP[self.operador]
        return f"({self.esq.imprimir()} {simbolo} {self.dir.imprimir()})"


# ---------------------------------------------------------------------------
# Analisador sintatico descendente recursivo
# ---------------------------------------------------------------------------

OPERADORES = {SOMA, SUB, MULT, DIV}


class ErroSintatico(Exception):
    """Erro sintatico: token inesperado encontrado na posicao informada."""

    def __init__(self, mensagem: str, posicao: int):
        self.posicao = posicao
        super().__init__(f"Erro sintatico na posicao {posicao}: {mensagem}")


class Parser:
    """Analisador sintatico descendente recursivo para a linguagem EC1.

    Recebe um Lexer ja instanciado e produz a AST atraves do metodo parse().
    O analisador consome tokens sob demanda via proximo_token(); um token
    de lookahead e mantido internamente para guiar as decisoes de producao.
    """

    def __init__(self, lexer: Lexer):
        self._lexer = lexer
        self._lookahead: Token = self._lexer.proximo_token()

    # --- Primitivas internas ------------------------------------------------

    def _avanca(self) -> Token:
        """Consume o lookahead atual e le o proximo token."""
        tok = self._lookahead
        self._lookahead = self._lexer.proximo_token()
        return tok

    def _consome(self, tipo: str) -> Token:
        """Consome o lookahead se ele tiver o tipo esperado; erro caso contrario."""
        if self._lookahead.tipo != tipo:
            raise ErroSintatico(
                f"esperado {tipo}, encontrado {self._lookahead.tipo!r}"
                + (
                    f" ('{self._lookahead.lexema}')"
                    if self._lookahead.lexema
                    else ""
                ),
                self._lookahead.posicao,
            )
        return self._avanca()

    # --- Regras gramaticais -------------------------------------------------

    def parse(self) -> Exp:
        """Ponto de entrada: analisa um <programa> e retorna sua AST.

        Apos a expressao principal, verifica se a entrada chegou ao fim.
        """
        arvore = self._analisa_exp()
        if self._lookahead.tipo != EOF:
            raise ErroSintatico(
                f"tokens inesperados apos o fim da expressao: "
                f"{self._lookahead.tipo!r} ('{self._lookahead.lexema}')",
                self._lookahead.posicao,
            )
        return arvore

    def _analisa_exp(self) -> Exp:
        """Analisa uma <expressao> e retorna o no correspondente da AST.

        <expressao> ::= <literal> | '(' <expressao> <operador> <expressao> ')'
        """
        tok = self._lookahead

        if tok.tipo == NUMERO:
            self._avanca()
            return Const(int(tok.lexema))

        if tok.tipo == PAREN_ESQ:
            self._avanca()                       # consome '('
            esq = self._analisa_exp()            # operando esquerdo
            operador = self._analisa_operador()  # operador
            dir = self._analisa_exp()            # operando direito
            self._consome(PAREN_DIR)             # exige ')'
            return OpBin(operador, esq, dir)

        # Nenhuma producao aplicavel: erro sintatico.
        if tok.tipo == EOF:
            raise ErroSintatico(
                "expressao incompleta: fim inesperado da entrada",
                tok.posicao,
            )
        raise ErroSintatico(
            f"token inesperado {tok.tipo!r} ('{tok.lexema}')",
            tok.posicao,
        )

    def _analisa_operador(self) -> str:
        """Analisa um <operador> e retorna seu tipo de token.

        <operador> ::= '+' | '-' | '*' | '/'
        """
        tok = self._lookahead
        if tok.tipo not in OPERADORES:
            raise ErroSintatico(
                f"operador esperado, encontrado {tok.tipo!r}"
                + (f" ('{tok.lexema}')" if tok.lexema else ""),
                tok.posicao,
            )
        self._avanca()
        return tok.tipo


# ---------------------------------------------------------------------------
# Interface de linha de comando
# ---------------------------------------------------------------------------


def _analisar_argumentos(argv: list[str]) -> tuple[Path, bool]:
    """Interpreta os argumentos da linha de comando.

    Retorna (caminho_do_arquivo, exibir_arvore).
    """
    args = argv[1:]
    exibir_arvore = False
    arquivos = []

    for a in args:
        if a == "--arvore":
            exibir_arvore = True
        elif a.startswith("-"):
            print(f"opcao desconhecida: {a}", file=sys.stderr)
            sys.exit(2)
        else:
            arquivos.append(a)

    if len(arquivos) != 1:
        print(f"uso: {argv[0]} [--arvore] <arquivo.ec1>", file=sys.stderr)
        sys.exit(2)

    return Path(arquivos[0]), exibir_arvore


def main() -> int:
    origem, exibir_arvore = _analisar_argumentos(sys.argv)

    try:
        conteudo = origem.read_text()
    except OSError as e:
        print(f"erro ao ler {origem}: {e}", file=sys.stderr)
        return 2

    lexer = Lexer(conteudo)
    parser = Parser(lexer)

    try:
        arvore = parser.parse()
    except ErroLexico as e:
        print(e, file=sys.stderr)
        return 1
    except ErroSintatico as e:
        print(e, file=sys.stderr)
        return 1

    try:
        valor = arvore.avaliar()
    except ZeroDivisionError as e:
        print(f"Erro em tempo de execucao: {e}", file=sys.stderr)
        return 1

    if exibir_arvore:
        print(arvore.imprimir())
    print(valor)
    return 0


if __name__ == "__main__":
    sys.exit(main())
