#!/usr/bin/env python3
"""Compilador completo da linguagem EV (Expressoes com Variaveis).

Le um arquivo de entrada com um programa EV, realiza analise lexica, analise
sintatica, analise semantica de variaveis declaradas e gera assembly x86-64
(GAS/AT&T, Linux), pronto para ser montado e executado.

Uso:
    python3 compev.py <arquivo.ev> [-o saida.s] [--otimizar] [--avaliar]

Saida padrao: grava o assembly em um arquivo (por padrao o mesmo nome do
arquivo de entrada com extensao .s, ou o caminho passado em -o). Com "-o -"
o assembly e escrito na saida padrao, sem nenhuma linha extra.

Opcoes auxiliares:
    --avaliar   imprime apenas o valor inteiro do programa, usado como
                oraculo de verificacao nos testes.
    --otimizar  calcula o programa em tempo de compilacao e emite um unico
                "mov $<resultado>, %rax".

Erros lexicos, sintaticos, semanticos ou de compilacao (divisao por zero) sao
reportados em stderr. Codigos de saida: 0 sucesso, 1 erro de compilacao,
2 erro de uso.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Analisador lexico
# ---------------------------------------------------------------------------

NUMERO = "Numero"
IDENT = "Identificador"
PAREN_ESQ = "ParenEsq"
PAREN_DIR = "ParenDir"
SOMA = "Soma"
SUB = "Sub"
MULT = "Mult"
DIV = "Div"
IGUAL = "Igual"
PONTO_VIRGULA = "PontoVirgula"
EOF = "EOF"

SIMBOLOS = {
    "(": PAREN_ESQ,
    ")": PAREN_DIR,
    "+": SOMA,
    "-": SUB,
    "*": MULT,
    "/": DIV,
    "=": IGUAL,
    ";": PONTO_VIRGULA,
}

ESPACOS = {" ", "\t", "\n", "\r"}


def _eh_letra(c: str) -> bool:
    """Retorna True para letras ASCII aceitas em identificadores EV."""
    return ("a" <= c <= "z") or ("A" <= c <= "Z")


def _eh_letra_digito(c: str) -> bool:
    return _eh_letra(c) or _eh_digito(c)


def _eh_digito(c: str) -> bool:
    """Retorna True para os digitos ASCII aceitos pela gramatica EV."""
    return "0" <= c <= "9"


class ErroLexico(Exception):
    """Erro lexico: caractere ou lexema invalido encontrado na entrada."""

    def __init__(self, posicao: int, lexema: str, mensagem: str = None):
        self.posicao = posicao
        self.lexema = lexema
        if mensagem is None:
            mensagem = f"caractere invalido '{lexema}'"
        super().__init__(f"Erro lexico na posicao {posicao}: {mensagem}")


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
        """Retorna o proximo token da entrada (ou EOF no final)."""
        self._pular_espacos()

        if self.pos >= len(self.entrada):
            return Token(EOF, "", self.pos)

        inicio = self.pos
        c = self.entrada[self.pos]

        if _eh_digito(c):
            while self.pos < len(self.entrada) and _eh_digito(self.entrada[self.pos]):
                self.pos += 1
            if self.pos < len(self.entrada) and _eh_letra(self.entrada[self.pos]):
                while (
                    self.pos < len(self.entrada)
                    and _eh_letra_digito(self.entrada[self.pos])
                ):
                    self.pos += 1
                lexema = self.entrada[inicio : self.pos]
                raise ErroLexico(
                    inicio,
                    lexema,
                    f"identificador nao pode comecar com digito: '{lexema}'",
                )
            lexema = self.entrada[inicio : self.pos]
            return Token(NUMERO, lexema, inicio)

        if _eh_letra(c):
            while self.pos < len(self.entrada) and _eh_letra_digito(
                self.entrada[self.pos]
            ):
                self.pos += 1
            lexema = self.entrada[inicio : self.pos]
            return Token(IDENT, lexema, inicio)

        if c in SIMBOLOS:
            self.pos += 1
            return Token(SIMBOLOS[c], c, inicio)

        raise ErroLexico(inicio, c)


# ---------------------------------------------------------------------------
# Semantica da divisao
# ---------------------------------------------------------------------------


def div_trunc(a: int, b: int) -> int:
    """Divisao inteira truncada em direcao a zero (estilo C / idiv do x86)."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


# ---------------------------------------------------------------------------
# Arvore de sintaxe abstrata (AST)
# ---------------------------------------------------------------------------

_SIMBOLO_OP = {SOMA: "+", SUB: "-", MULT: "*", DIV: "/"}


def simbolo_variavel(nome: str) -> str:
    """Nome seguro usado no assembly para uma variavel do programa fonte."""
    return f"ev_var_{nome}"


class Exp:
    """Classe base abstrata para nos de expressao."""

    def avaliar(self, ambiente: dict) -> int:  # pragma: no cover
        raise NotImplementedError

    def imprimir(self) -> str:  # pragma: no cover
        raise NotImplementedError

    def gerar(self, emissor: list) -> None:  # pragma: no cover
        raise NotImplementedError

    def coletar_variaveis(self, destino: set) -> None:  # pragma: no cover
        raise NotImplementedError

    def variaveis(self) -> set:
        nomes = set()
        self.coletar_variaveis(nomes)
        return nomes


class Const(Exp):
    """No folha: uma constante inteira."""

    def __init__(self, valor: int):
        self.valor = valor

    def avaliar(self, ambiente: dict) -> int:
        return self.valor

    def imprimir(self) -> str:
        return str(self.valor)

    def gerar(self, emissor: list) -> None:
        emissor.append(f"  mov ${self.valor}, %rax")

    def coletar_variaveis(self, destino: set) -> None:
        return None


class Var(Exp):
    """No folha: referencia a uma variavel."""

    def __init__(self, nome: str):
        self.nome = nome

    def avaliar(self, ambiente: dict) -> int:
        return ambiente[self.nome]

    def imprimir(self) -> str:
        return self.nome

    def gerar(self, emissor: list) -> None:
        emissor.append(f"  mov {simbolo_variavel(self.nome)}(%rip), %rax")

    def coletar_variaveis(self, destino: set) -> None:
        destino.add(self.nome)


class OpBin(Exp):
    """No interno: uma operacao binaria com operandos esquerdo e direito."""

    def __init__(self, operador: str, esq: Exp, dir: Exp):
        self.operador = operador
        self.esq = esq
        self.dir = dir

    def avaliar(self, ambiente: dict) -> int:
        ve = self.esq.avaliar(ambiente)
        vd = self.dir.avaliar(ambiente)
        if self.operador == SOMA:
            return ve + vd
        if self.operador == SUB:
            return ve - vd
        if self.operador == MULT:
            return ve * vd
        if self.operador == DIV:
            if vd == 0:
                raise ZeroDivisionError("divisao por zero na expressao")
            return div_trunc(ve, vd)
        raise RuntimeError(f"operador desconhecido: {self.operador}")  # pragma: no cover

    def imprimir(self) -> str:
        simbolo = _SIMBOLO_OP[self.operador]
        return f"({self.esq.imprimir()} {simbolo} {self.dir.imprimir()})"

    def gerar(self, emissor: list) -> None:
        self.dir.gerar(emissor)
        emissor.append("  push %rax")
        self.esq.gerar(emissor)
        emissor.append("  pop %rbx")

        if self.operador == SOMA:
            emissor.append("  add %rbx, %rax")
        elif self.operador == SUB:
            emissor.append("  sub %rbx, %rax")
        elif self.operador == MULT:
            emissor.append("  imul %rbx, %rax")
        elif self.operador == DIV:
            emissor.append("  cqo")
            emissor.append("  idiv %rbx")
        else:  # pragma: no cover
            raise RuntimeError(f"operador desconhecido: {self.operador}")

    def coletar_variaveis(self, destino: set) -> None:
        self.esq.coletar_variaveis(destino)
        self.dir.coletar_variaveis(destino)


class Decl:
    """Declaracao EV: nome = expressao."""

    def __init__(self, nome: str, exp: Exp):
        self.nome = nome
        self.exp = exp

    def avaliar(self, ambiente: dict) -> None:
        ambiente[self.nome] = self.exp.avaliar(ambiente)

    def imprimir(self) -> str:
        return f"{self.nome} = {self.exp.imprimir()};"

    def gerar(self, emissor: list) -> None:
        emissor.append(f"  # {self.imprimir()}")
        self.exp.gerar(emissor)
        emissor.append(f"  mov %rax, {simbolo_variavel(self.nome)}(%rip)")


class Programa:
    """No raiz: declaracoes seguidas da expressao de resultado."""

    def __init__(self, declaracoes: list, resultado: Exp):
        self.declaracoes = declaracoes
        self.resultado = resultado

    def avaliar(self) -> int:
        ambiente = {}
        for decl in self.declaracoes:
            decl.avaliar(ambiente)
        return self.resultado.avaliar(ambiente)

    def nomes_variaveis(self) -> list:
        nomes = []
        vistos = set()
        for decl in self.declaracoes:
            if decl.nome not in vistos:
                nomes.append(decl.nome)
                vistos.add(decl.nome)
        return nomes


# ---------------------------------------------------------------------------
# Analise semantica
# ---------------------------------------------------------------------------


class ErroSemantico(Exception):
    """Erro semantico: uso de variavel antes da declaracao."""

    def __init__(self, mensagem: str):
        super().__init__(f"Erro semantico: {mensagem}")


def verificar_semantica(programa: Programa) -> None:
    """Verifica se toda variavel usada ja foi declarada anteriormente."""
    declaradas = set()

    for decl in programa.declaracoes:
        for nome in sorted(decl.exp.variaveis()):
            if nome not in declaradas:
                raise ErroSemantico(
                    f"variavel nao declarada '{nome}' na declaracao de '{decl.nome}'"
                )
        declaradas.add(decl.nome)

    for nome in sorted(programa.resultado.variaveis()):
        if nome not in declaradas:
            raise ErroSemantico(
                f"variavel nao declarada '{nome}' na expressao de resultado"
            )


# ---------------------------------------------------------------------------
# Analisador sintatico descendente recursivo
# ---------------------------------------------------------------------------

OPERADORES_ADITIVOS = {SOMA, SUB}
OPERADORES_MULTIPLICATIVOS = {MULT, DIV}


class ErroSintatico(Exception):
    """Erro sintatico: token inesperado encontrado na posicao informada."""

    def __init__(self, mensagem: str, posicao: int):
        self.posicao = posicao
        super().__init__(f"Erro sintatico na posicao {posicao}: {mensagem}")


class Parser:
    """Analisador sintatico descendente recursivo para a linguagem EV."""

    def __init__(self, lexer: Lexer):
        self._lexer = lexer
        self._lookahead: Token = self._lexer.proximo_token()

    def _avanca(self) -> Token:
        tok = self._lookahead
        self._lookahead = self._lexer.proximo_token()
        return tok

    def _consome(self, tipo: str) -> Token:
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

    def parse(self) -> Programa:
        programa = self._analisa_programa()
        if self._lookahead.tipo != EOF:
            raise ErroSintatico(
                f"tokens inesperados apos o fim do programa: "
                f"{self._lookahead.tipo!r} ('{self._lookahead.lexema}')",
                self._lookahead.posicao,
            )
        return programa

    def _analisa_programa(self) -> Programa:
        """<programa> ::= <decl>* <result>."""
        declaracoes = []
        while self._lookahead.tipo == IDENT:
            declaracoes.append(self._analisa_decl())

        if self._lookahead.tipo != IGUAL:
            raise ErroSintatico(
                f"esperado inicio da expressao de resultado '='; "
                f"encontrado {self._lookahead.tipo!r}",
                self._lookahead.posicao,
            )

        resultado = self._analisa_result()
        return Programa(declaracoes, resultado)

    def _analisa_decl(self) -> Decl:
        """<decl> ::= <ident> '=' <exp> ';'."""
        nome = self._consome(IDENT).lexema
        self._consome(IGUAL)
        exp = self._analisa_exp_a()
        self._consome(PONTO_VIRGULA)
        return Decl(nome, exp)

    def _analisa_result(self) -> Exp:
        """<result> ::= '=' <exp>."""
        self._consome(IGUAL)
        return self._analisa_exp_a()

    def _analisa_exp_a(self) -> Exp:
        """<exp_a> ::= <exp_m> (('+' | '-') <exp_m>)*."""
        esq = self._analisa_exp_m()

        while self._lookahead.tipo in OPERADORES_ADITIVOS:
            operador = self._avanca().tipo
            dir = self._analisa_exp_m()
            esq = OpBin(operador, esq, dir)

        return esq

    def _analisa_exp_m(self) -> Exp:
        """<exp_m> ::= <prim> (('*' | '/') <prim>)*."""
        esq = self._analisa_prim()

        while self._lookahead.tipo in OPERADORES_MULTIPLICATIVOS:
            operador = self._avanca().tipo
            dir = self._analisa_prim()
            esq = OpBin(operador, esq, dir)

        return esq

    def _analisa_prim(self) -> Exp:
        """<prim> ::= <num> | <ident> | '(' <exp_a> ')'."""
        tok = self._lookahead

        if tok.tipo == NUMERO:
            self._avanca()
            return Const(int(tok.lexema))

        if tok.tipo == IDENT:
            self._avanca()
            return Var(tok.lexema)

        if tok.tipo == PAREN_ESQ:
            self._avanca()
            expr = self._analisa_exp_a()
            self._consome(PAREN_DIR)
            return expr

        if tok.tipo == EOF:
            raise ErroSintatico(
                "expressao incompleta: fim inesperado da entrada",
                tok.posicao,
            )
        raise ErroSintatico(
            f"token inesperado {tok.tipo!r} ('{tok.lexema}')",
            tok.posicao,
        )


# ---------------------------------------------------------------------------
# Geracao de codigo: montagem do arquivo assembly completo
# ---------------------------------------------------------------------------

MODELO = """\
  #
  # codigo gerado pelo compilador EV
  #
  .section .bss
{bss}

  .section .text
  .globl _start

_start:
{corpo}

  call imprime_num
  call sair

  .include "runtime.s"
"""


def gerar_assembly(programa: Programa, otimizar: bool = False) -> str:
    """Gera o texto completo do arquivo assembly para o programa informado."""
    if otimizar:
        bss = ["  # sem variaveis no modo otimizado"]
        corpo = [f"  mov ${programa.avaliar()}, %rax"]
    else:
        nomes = programa.nomes_variaveis()
        bss = [f"  .lcomm {simbolo_variavel(nome)}, 8" for nome in nomes]
        if not bss:
            bss = ["  # sem variaveis"]

        corpo = []
        for decl in programa.declaracoes:
            decl.gerar(corpo)
        corpo.append("  # = " + programa.resultado.imprimir())
        programa.resultado.gerar(corpo)

    return MODELO.format(bss="\n".join(bss), corpo="\n".join(corpo))


# ---------------------------------------------------------------------------
# Interface de linha de comando
# ---------------------------------------------------------------------------


def _uso(programa: str) -> str:
    return f"uso: {programa} <arquivo.ev> [-o saida.s] [--otimizar] [--avaliar]"


def _analisar_argumentos(argv: list) -> tuple:
    args = argv[1:]
    arquivo = None
    saida = None
    otimizar = False
    avaliar_modo = False

    i = 0
    while i < len(args):
        a = args[i]
        if a == "-o":
            i += 1
            if i >= len(args):
                print(_uso(argv[0]), file=sys.stderr)
                sys.exit(2)
            saida = args[i]
        elif a == "--otimizar":
            otimizar = True
        elif a == "--avaliar":
            avaliar_modo = True
        elif a.startswith("-") and a != "-":
            print(f"opcao desconhecida: {a}", file=sys.stderr)
            sys.exit(2)
        else:
            if arquivo is not None:
                print(_uso(argv[0]), file=sys.stderr)
                sys.exit(2)
            arquivo = a
        i += 1

    if arquivo is None:
        print(_uso(argv[0]), file=sys.stderr)
        sys.exit(2)

    return arquivo, saida, otimizar, avaliar_modo


def main() -> int:
    arquivo, saida, otimizar, avaliar_modo = _analisar_argumentos(sys.argv)
    origem = Path(arquivo)

    try:
        conteudo = origem.read_text()
    except OSError as e:
        print(f"erro ao ler {origem}: {e}", file=sys.stderr)
        return 2

    try:
        lexer = Lexer(conteudo)
        parser = Parser(lexer)
        programa = parser.parse()
        verificar_semantica(programa)
        valor = programa.avaliar()
    except (ErroLexico, ErroSintatico, ErroSemantico) as e:
        print(e, file=sys.stderr)
        return 1
    except ZeroDivisionError as e:
        print(f"Erro de compilacao: {e}", file=sys.stderr)
        return 1

    if avaliar_modo:
        print(valor)
        return 0

    assembly = gerar_assembly(programa, otimizar=otimizar)

    if saida == "-":
        sys.stdout.write(assembly)
    else:
        destino = Path(saida) if saida else origem.with_suffix(".s")
        try:
            destino.write_text(assembly)
        except OSError as e:
            print(f"erro ao gravar {destino}: {e}", file=sys.stderr)
            return 1
        print(f"gerado: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
