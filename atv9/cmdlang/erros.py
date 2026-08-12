"""Erros do compilador Cmd."""


class ErroCmd(Exception):
    """Erro de compilacao com fase e posicao."""

    def __init__(self, fase, msg, linha=None, coluna=None):
        self.fase = fase
        self.msg = msg
        self.linha = linha
        self.coluna = coluna
        super().__init__(str(self))

    def __str__(self):
        if self.linha is None:
            return "erro %s: %s" % (self.fase, self.msg)
        return "erro %s (linha %d, coluna %d): %s" % (
            self.fase,
            self.linha,
            self.coluna,
            self.msg,
        )


class ErroLexico(ErroCmd):
    def __init__(self, msg, linha, coluna):
        super().__init__("lexico", msg, linha, coluna)


class ErroSintatico(ErroCmd):
    def __init__(self, msg, linha, coluna):
        super().__init__("sintatico", msg, linha, coluna)


class ErroSemantico(ErroCmd):
    def __init__(self, msg, linha, coluna):
        super().__init__("semantico", msg, linha, coluna)


class ErroExecucao(ErroCmd):
    def __init__(self, msg):
        super().__init__("execucao", msg)
