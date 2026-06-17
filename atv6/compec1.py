#!/usr/bin/env python3
"""Compilador completo da linguagem EC1 (Expressoes Constantes 1).

Le um arquivo de entrada com uma expressao EC1, realiza a analise lexica e
sintatica, produz a arvore de sintaxe abstrata (AST) e gera um arquivo
assembly x86-64 (GAS/AT&T, Linux) pronto para ser montado e executado.

Uso:
    python3 compec1.py <arquivo.ec1> [-o saida.s] [--otimizar]

Saida padrao: grava o assembly em um arquivo (por padrao o mesmo nome do
arquivo de entrada com extensao .s, ou o caminho passado em -o). Com "-o -"
o assembly e escrito na saida padrao, sem nenhuma linha extra.

Opcoes auxiliares:
    --avaliar   imprime apenas o valor inteiro da expressao (interpretador,
                usado como oraculo de verificacao nos testes).
    --otimizar  aplica propagacao de constantes: como toda expressao EC1 e
                constante, emite um unico "mov $<resultado>, %rax".

A AST e gerada reaproveitando o analisador da Atividade 05; a novidade desta
atividade e o metodo gerar(), que percorre a arvore emitindo assembly.

Erros lexicos, sintaticos ou de compilacao (divisao por zero) sao reportados
em stderr. Codigos de saida: 0 sucesso, 1 erro de compilacao, 2 erro de uso.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Analisador lexico (reutilizado da Atividade 04/05)
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
# Semantica da divisao
# ---------------------------------------------------------------------------


def div_trunc(a: int, b: int) -> int:
    """Divisao inteira truncada em direcao a zero (estilo C / idiv do x86).

    Difere de // do Python (que arredonda para baixo) quando os operandos
    tem sinais diferentes, por exemplo div_trunc(-7, 2) == -3 (// daria -4).
    O interpretador usa esta semantica para concordar com o assembly gerado.
    """
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


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

    def gerar(self, emissor: list) -> None:  # pragma: no cover
        raise NotImplementedError


class Const(Exp):
    """No folha: uma constante inteira."""

    def __init__(self, valor: int):
        self.valor = valor

    def avaliar(self) -> int:
        return self.valor

    def imprimir(self) -> str:
        return str(self.valor)

    def gerar(self, emissor: list) -> None:
        # Uma constante vira um unico mov do valor imediato para %rax.
        emissor.append(f"  mov ${self.valor}, %rax")


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
            return div_trunc(ve, vd)
        raise RuntimeError(f"operador desconhecido: {self.operador}")  # pragma: no cover

    def imprimir(self) -> str:
        simbolo = _SIMBOLO_OP[self.operador]
        return f"({self.esq.imprimir()} {simbolo} {self.dir.imprimir()})"

    def gerar(self, emissor: list) -> None:
        """Emite o codigo da operacao usando a pilha (esquema "direito primeiro").

        Gera o operando direito (resultado em %rax), empilha, gera o operando
        esquerdo (resultado em %rax) e desempilha o direito em %rbx. Apos o
        pop fica: esquerdo em %rax, direito em %rbx; entao executa a operacao.
        Cada OpBin empilha e desempilha exatamente um valor, entao a pilha
        sempre volta ao estado inicial e o esquema funciona para qualquer
        aninhamento, usando apenas %rax, %rbx (e %rdx, implicito no idiv).
        """
        self.dir.gerar(emissor)               # operando direito -> %rax
        emissor.append("  push %rax")          # salva o direito na pilha
        self.esq.gerar(emissor)               # operando esquerdo -> %rax
        emissor.append("  pop %rbx")           # recupera o direito em %rbx

        if self.operador == SOMA:
            emissor.append("  add %rbx, %rax")     # rax = esq + dir
        elif self.operador == SUB:
            emissor.append("  sub %rbx, %rax")     # rax = esq - dir
        elif self.operador == MULT:
            emissor.append("  imul %rbx, %rax")    # rax = esq * dir
        elif self.operador == DIV:
            emissor.append("  cqo")                # estende o sinal de rax em rdx:rax
            emissor.append("  idiv %rbx")          # rax = esq / dir (trunca p/ zero)
        else:  # pragma: no cover
            raise RuntimeError(f"operador desconhecido: {self.operador}")


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
# Geracao de codigo: montagem do arquivo assembly completo
# ---------------------------------------------------------------------------

# Modelo do arquivo de saida (igual ao da Atividade 02/03): o corpo gerado
# para a expressao deixa o resultado em %rax; em seguida o runtime imprime o
# valor e encerra o processo.
MODELO = """\
  #
  # codigo gerado pelo compilador EC1
  #
  .section .text
  .globl _start

_start:
{corpo}

  call imprime_num
  call sair

  .include "runtime.s"
"""


def gerar_assembly(arvore: Exp, otimizar: bool = False) -> str:
    """Gera o texto completo do arquivo assembly para a AST informada.

    Com otimizar=True aplica propagacao de constantes (toda expressao EC1 e
    constante), emitindo um unico mov com o resultado ja calculado. No modo
    padrao percorre a arvore emitindo o esquema de pilha.
    """
    if otimizar:
        corpo = [f"  mov ${arvore.avaliar()}, %rax"]
    else:
        corpo = []
        arvore.gerar(corpo)
    return MODELO.format(corpo="\n".join(corpo))


# ---------------------------------------------------------------------------
# Interface de linha de comando
# ---------------------------------------------------------------------------


def _analisar_argumentos(argv: list) -> tuple:
    """Interpreta os argumentos da linha de comando.

    Retorna (arquivo, saida, otimizar, avaliar_modo). saida e None para o
    destino padrao (<entrada>.s) ou "-" para a saida padrao.
    """
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
                print(f"uso: {argv[0]} <arquivo.ec1> [-o saida.s] [--otimizar]",
                      file=sys.stderr)
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
                print(f"uso: {argv[0]} <arquivo.ec1> [-o saida.s] [--otimizar]",
                      file=sys.stderr)
                sys.exit(2)
            arquivo = a
        i += 1

    if arquivo is None:
        print(f"uso: {argv[0]} <arquivo.ec1> [-o saida.s] [--otimizar]",
              file=sys.stderr)
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

    lexer = Lexer(conteudo)
    parser = Parser(lexer)

    try:
        arvore = parser.parse()
    except (ErroLexico, ErroSintatico) as e:
        print(e, file=sys.stderr)
        return 1

    # Analise semantica: como todos os valores sao constantes, detectamos
    # divisao por zero ja em tempo de compilacao avaliando a arvore.
    try:
        valor = arvore.avaliar()
    except ZeroDivisionError as e:
        print(f"Erro de compilacao: {e}", file=sys.stderr)
        return 1

    if avaliar_modo:
        print(valor)
        return 0

    assembly = gerar_assembly(arvore, otimizar=otimizar)

    if saida == "-":
        # Saida padrao: apenas o conteudo do .s, sem nenhuma linha extra.
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
