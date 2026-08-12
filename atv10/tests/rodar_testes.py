#!/usr/bin/env python3
"""Roda todos os testes: interpretador e binario nativo."""

import os
import platform
import re
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from funlang import codigo, interp, semantico, sintatico
from funlang.erros import ErroCmd

DIR_OK = os.path.join(RAIZ, "tests", "programas")
DIR_ERRO = os.path.join(RAIZ, "tests", "erros")

NATIVO = platform.machine() in ("x86_64", "AMD64") and platform.system() == "Linux"


def meta(texto, chave):
    """Le metadados dos comentarios no topo do arquivo."""
    m = re.search(r"^#\s*%s:\s*(.+)$" % chave, texto, re.M)
    return m.group(1).strip() if m else None


def tem_gcc():
    try:
        subprocess.run(["gcc", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def roda_nativo(asm, entrada):
    with tempfile.TemporaryDirectory() as d:
        fonte = os.path.join(d, "p.s")
        alvo = os.path.join(d, "p")
        with open(fonte, "w", encoding="utf-8") as f:
            f.write(asm)
        r = subprocess.run(["gcc", "-no-pie", fonte, "-o", alvo], capture_output=True, text=True)
        if r.returncode != 0:
            return None, "gcc falhou: " + r.stderr.strip().splitlines()[0]
        r = subprocess.run([alvo], input=(entrada or "") + "\n", capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return None, "binario retornou %d" % r.returncode
        return r.stdout.strip(), None


def testa_validos(usar_gcc):
    falhas = []
    arquivos = sorted(f for f in os.listdir(DIR_OK) if f.endswith(".fun"))
    for nome in arquivos:
        caminho = os.path.join(DIR_OK, nome)
        texto = open(caminho, encoding="utf-8").read()
        esperado = meta(texto, "esperado")
        entrada = meta(texto, "entrada")
        detalhes = []
        try:
            prog = sintatico.analisar(texto)
            tab = semantico.analisar(prog)
            obtido = str(interp.executar(prog, entrada))
            if obtido != esperado:
                detalhes.append("interp deu %s, esperava %s" % (obtido, esperado))
            if usar_gcc:
                nat, err = roda_nativo(codigo.gerar(prog, tab), entrada)
                if err:
                    detalhes.append(err)
                elif nat != esperado:
                    detalhes.append("nativo deu %s, esperava %s" % (nat, esperado))
        except ErroCmd as e:
            detalhes.append(str(e))
        status = "ok" if not detalhes else "FALHOU"
        print("  %-38s %-8s %s" % (nome, status, "; ".join(detalhes)))
        if detalhes:
            falhas.append(nome)
    return len(arquivos), falhas


def testa_erros():
    falhas = []
    arquivos = sorted(f for f in os.listdir(DIR_ERRO) if f.endswith(".fun"))
    for nome in arquivos:
        caminho = os.path.join(DIR_ERRO, nome)
        texto = open(caminho, encoding="utf-8").read()
        fase = meta(texto, "erro")
        detalhes = []
        try:
            prog = sintatico.analisar(texto)
            semantico.analisar(prog)
            detalhes.append("compilou, esperava erro %s" % fase)
        except ErroCmd as e:
            if e.fase != fase:
                detalhes.append("erro %s, esperava %s" % (e.fase, fase))
        status = "ok" if not detalhes else "FALHOU"
        print("  %-38s %-8s %s" % (nome, status, "; ".join(detalhes)))
        if detalhes:
            falhas.append(nome)
    return len(arquivos), falhas


def main():
    usar_gcc = NATIVO and tem_gcc()
    print("programas validos (interpretador%s):" % (" e binario nativo" if usar_gcc else " apenas"))
    n1, f1 = testa_validos(usar_gcc)
    print("\nprogramas com erro esperado:")
    n2, f2 = testa_erros()
    total, falhas = n1 + n2, f1 + f2
    print("\n%d/%d testes passaram" % (total - len(falhas), total))
    if not usar_gcc:
        print("aviso: gcc x86_64 indisponivel, o binario nativo nao foi testado")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
