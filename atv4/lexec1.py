#!/usr/bin/env python3
"""Analisador lexico da linguagem EC1 (Expressoes Constantes 1).

Le um arquivo de entrada (passado como argumento na linha de comando) e
imprime a sequencia de tokens, cada um no formato:

    <tipo, lexema, posicao>

A posicao e o deslocamento (indice) do primeiro caractere do lexema dentro
do arquivo de entrada. Espacos em branco (espaco, tab, nova linha e retorno
de carro) sao ignorados. Qualquer caractere fora do conjunto de digitos,
parenteses e operadores (+ - * /) gera um erro lexico, reportando a posicao.
"""

import sys
from pathlib import Path


# Tipos de token da linguagem EC1.
NUMERO = "Numero"
PAREN_ESQ = "ParenEsq"
PAREN_DIR = "ParenDir"
SOMA = "Soma"
SUB = "Sub"
MULT = "Mult"
DIV = "Div"
EOF = "EOF"

# Mapa de caractere unico -> tipo de token (pontuacao e operadores).
SIMBOLOS = {
    "(": PAREN_ESQ,
    ")": PAREN_DIR,
    "+": SOMA,
    "-": SUB,
    "*": MULT,
    "/": DIV,
}

ESPACOS = {" ", "\t", "\n", "\r"}  # codigos ASCII 32, 9, 10, 13


class ErroLexico(Exception):
    """Erro lexico: caractere invalido encontrado na posicao informada."""

    def __init__(self, posicao: int, caractere: str):
        self.posicao = posicao
        self.caractere = caractere
        super().__init__(f"Erro lexico na posicao {posicao}: caractere invalido '{caractere}'")


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

        Levanta ErroLexico se encontrar um caractere fora do alfabeto da
        linguagem EC1.
        """
        self._pular_espacos()

        if self.pos >= len(self.entrada):
            return Token(EOF, "", self.pos)

        inicio = self.pos
        c = self.entrada[self.pos]

        # Numero: um ou mais digitos.
        if c.isdigit():
            while self.pos < len(self.entrada) and self.entrada[self.pos].isdigit():
                self.pos += 1
            lexema = self.entrada[inicio:self.pos]
            return Token(NUMERO, lexema, inicio)

        # Pontuacao e operadores: um unico caractere.
        if c in SIMBOLOS:
            self.pos += 1
            return Token(SIMBOLOS[c], c, inicio)

        # Qualquer outra coisa e um erro lexico.
        raise ErroLexico(inicio, c)

    def tokens(self) -> list:
        """Retorna todos os tokens da entrada em uma lista (sem o EOF)."""
        resultado = []
        while True:
            token = self.proximo_token()
            if token.tipo == EOF:
                break
            resultado.append(token)
        return resultado


def main() -> int:
    if len(sys.argv) != 2:
        print(f"uso: {sys.argv[0]} <arquivo.ec1>", file=sys.stderr)
        return 2

    origem = Path(sys.argv[1])
    try:
        conteudo = origem.read_text()
    except OSError as e:
        print(f"erro ao ler {origem}: {e}", file=sys.stderr)
        return 2

    lexer = Lexer(conteudo)
    try:
        for token in lexer.tokens():
            print(token)
    except ErroLexico as e:
        print(f"Erro lexico na posicao {e.posicao}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
