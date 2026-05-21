#!/usr/bin/env python3
"""Compilador CI - traduz constantes inteiras para assembly x86-64."""

import re
import sys
from pathlib import Path


MODELO = """\
  #
  # saida do compilador CI
  #

  .section .text
  .globl _start

_start:
  mov ${valor}, %rax

  call imprime_num
  call sair

  .include "runtime.s"
"""


def main() -> int:
    if len(sys.argv) != 2:
        print(f"uso: {sys.argv[0]} <arquivo.ci>", file=sys.stderr)
        return 2

    origem = Path(sys.argv[1])
    try:
        conteudo = origem.read_text().strip()
    except OSError as e:
        print(f"erro ao ler {origem}: {e}", file=sys.stderr)
        return 2

    # Analise: o programa deve ser apenas uma constante inteira.
    if not re.fullmatch(r"[0-9]+", conteudo):
        print(
            f"erro de sintaxe: '{conteudo}' nao e uma constante inteira valida",
            file=sys.stderr,
        )
        return 1

    # Sintese: insere a constante no modelo e grava o .s.
    saida = origem.with_suffix(".s")
    saida.write_text(MODELO.format(valor=conteudo))
    print(f"gerado: {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
