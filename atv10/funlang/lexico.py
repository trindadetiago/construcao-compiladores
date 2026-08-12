"""Analise lexica da linguagem Fun.

Estende o lexico da linguagem Cmd (atividade 9): mesma logica de
reconhecimento de tokens, com um novo tipo de token (virgula) e tres
novas palavras-chave (fun, var, main), como descrito na secao 3 do guia.
"""

from .erros import ErroLexico

NUM = "NUM"
ID = "ID"
PAL = "PAL"
OP = "OP"
PONT = "PONT"
FIM = "FIM"

# palavras-chave da linguagem Cmd + fun, var, main (novas na linguagem Fun)
PALAVRAS = {
    "if", "else", "while", "return", "read", "and", "or", "not",
    "fun", "var", "main",
}

# operadores de 2 caracteres antes dos de 1
OPS2 = ("==", "<=", ">=", "!=")
OPS1 = ("+", "-", "*", "/", "<", ">", "=")
# "," e o unico simbolo novo em relacao ao Cmd (secao 3 do guia)
PONTS = ("{", "}", "(", ")", ";", ",")


class Token:
    __slots__ = ("tipo", "valor", "linha", "coluna")

    def __init__(self, tipo, valor, linha, coluna):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha
        self.coluna = coluna

    def __repr__(self):
        return "Token(%s, %r, %d:%d)" % (self.tipo, self.valor, self.linha, self.coluna)


class Lexer:
    def __init__(self, texto):
        self.txt = texto
        self.i = 0
        self.linha = 1
        self.coluna = 1

    def _avanca(self, n=1):
        for _ in range(n):
            if self.i < len(self.txt):
                if self.txt[self.i] == "\n":
                    self.linha += 1
                    self.coluna = 1
                else:
                    self.coluna += 1
                self.i += 1

    def _atual(self):
        return self.txt[self.i] if self.i < len(self.txt) else ""

    def _pula_branco(self):
        while self.i < len(self.txt):
            c = self.txt[self.i]
            if c.isspace():
                self._avanca()
            elif c == "#":  # comentario ate o fim da linha
                while self.i < len(self.txt) and self.txt[self.i] != "\n":
                    self._avanca()
            else:
                break

    def tokens(self):
        """Lista completa de tokens, terminada por FIM."""
        saida = []
        while True:
            t = self.proximo()
            saida.append(t)
            if t.tipo == FIM:
                return saida

    def proximo(self):
        self._pula_branco()
        lin, col = self.linha, self.coluna
        if self.i >= len(self.txt):
            return Token(FIM, "", lin, col)

        c = self._atual()

        if c.isdigit():
            ini = self.i
            while self._atual().isdigit():
                self._avanca()
            return Token(NUM, int(self.txt[ini:self.i]), lin, col)

        if c.isalpha() or c == "_":
            ini = self.i
            while self._atual().isalnum() or self._atual() == "_":
                self._avanca()
            lexema = self.txt[ini:self.i]
            # palavra chave usa a mesma regra de identificador
            tipo = PAL if lexema in PALAVRAS else ID
            return Token(tipo, lexema, lin, col)

        par = self.txt[self.i:self.i + 2]
        if par in OPS2:
            self._avanca(2)
            return Token(OP, par, lin, col)

        if c in OPS1:
            self._avanca()
            return Token(OP, c, lin, col)

        if c in PONTS:
            self._avanca()
            return Token(PONT, c, lin, col)

        raise ErroLexico("caractere invalido %r" % c, lin, col)


def tokenizar(texto):
    return Lexer(texto).tokens()
