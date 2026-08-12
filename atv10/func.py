#!/usr/bin/env python3
"""Compilador da linguagem Fun. Uso: python3 func.py <acao> <fonte.fun>"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from funlang import ast, codigo, interp, lexico, semantico, sintatico
from funlang.erros import ErroCmd

ACOES = ("tokens", "ast", "check", "asm", "build", "run", "interp")

USO = """uso: python3 func.py <acao> <fonte.fun> [saida]

acoes:
  tokens   lista os tokens do fonte
  ast      mostra a arvore sintatica
  check    roda analise lexica, sintatica e semantica
  asm      gera o assembly x86_64 (saida opcional, padrao stdout)
  build    gera o executavel via gcc (saida opcional)
  run      compila para um executavel temporario e executa
  interp   executa pelo interpretador de referencia
"""


def le(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def monta(asm, saida):
    """Chama o gcc no assembly gerado."""
    with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False) as f:
        f.write(asm)
        tmp = f.name
    try:
        r = subprocess.run(["gcc", "-no-pie", tmp, "-o", saida], capture_output=True, text=True)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            raise SystemExit("falha ao montar com gcc")
    finally:
        os.unlink(tmp)


def principal(argv):
    if len(argv) < 3 or argv[1] not in ACOES:
        sys.stderr.write(USO)
        return 2

    acao, fonte = argv[1], argv[2]
    saida = argv[3] if len(argv) > 3 else None
    texto = le(fonte)

    try:
        if acao == "tokens":
            for t in lexico.tokenizar(texto):
                print(t)
            return 0

        prog = sintatico.analisar(texto)

        if acao == "ast":
            print(ast.imprime(prog))
            return 0

        tab = semantico.analisar(prog)

        if acao == "check":
            nfun = sum(1 for d in prog.decls if isinstance(d, ast.FunDecl))
            print("ok: %d variaveis globais, %d funcoes, %d comandos no main" % (
                len(tab), nfun, len(prog.cmds)
            ))
            return 0

        if acao == "interp":
            print(interp.executar(prog))
            return 0

        asm = codigo.gerar(prog, tab)

        if acao == "asm":
            if saida:
                with open(saida, "w", encoding="utf-8") as f:
                    f.write(asm)
            else:
                sys.stdout.write(asm)
            return 0

        if acao == "build":
            alvo = saida or os.path.splitext(fonte)[0]
            monta(asm, alvo)
            print(alvo)
            return 0

        if acao == "run":
            with tempfile.TemporaryDirectory() as d:
                alvo = os.path.join(d, "prog")
                monta(asm, alvo)
                return subprocess.run([alvo]).returncode

    except ErroCmd as e:
        sys.stderr.write("%s: %s\n" % (fonte, e))
        return 1
    except FileNotFoundError as e:
        sys.stderr.write("%s\n" % e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(principal(sys.argv))
