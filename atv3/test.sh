#!/usr/bin/env bash
# Monta, linka e executa zeller.s; compara com o resultado do verificador
# em Python para 25/05/2026 (esperado: 2 = segunda-feira).
set -u
cd "$(dirname "$0")"

esperado=2

echo "Verificador em Python:"
python3 zeller.py

echo
echo "Montando e executando zeller.s..."
if ! command -v as >/dev/null || ! command -v ld >/dev/null; then
  echo "  (as/ld nao encontrados - rode dentro de Linux x86-64 ou via Docker)"
  exit 0
fi

as --64 -o zeller.o zeller.s
ld -o zeller zeller.o
saida=$(./zeller)
echo "  saida do assembly: $saida"
echo "  esperado:          $esperado"

if [[ "$saida" == "$esperado" ]]; then
  echo "  PASSOU"
  exit 0
else
  echo "  FALHOU"
  exit 1
fi
