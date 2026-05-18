#!/usr/bin/env bash
# Testes do compilador CI.

set -u
cd "$(dirname "$0")"

erros=0

echo "Teste 1: programa correto (p1.ci com '42')"
rm -f p1.s
if python3 compci.py p1.ci && [[ -f p1.s ]]; then
  echo "  PASSOU - p1.s gerado"
else
  echo "  FALHOU - p1.s nao foi gerado"
  erros=$((erros + 1))
fi

echo
echo "Teste 2: erro de sintaxe (erro.ci com '12abc')"
if python3 compci.py erro.ci 2>/dev/null; then
  echo "  FALHOU - o compilador aceitou entrada invalida"
  erros=$((erros + 1))
else
  echo "  PASSOU - entrada invalida rejeitada"
fi

echo
if [[ $erros -eq 0 ]]; then
  echo "Todos os testes passaram."
else
  echo "$erros teste(s) falharam."
fi
exit $erros
