#!/usr/bin/env bash
# Testes do compilador EC1 com verificacao automatica.
#
# Para cada caso valido o script:
#   1. compila o .ec1 -> .s (analise lexica + sintatica + geracao de codigo);
#   2. confere o valor do interpretador do proprio compilador (--avaliar, o
#      "oraculo") com o golden output em testes/esperado/;
#   3. se houver toolchain x86-64 (as/ld funcionais), monta, linka e executa o
#      binario e compara sua saida com o oraculo (verificacao cruzada: garante
#      que o assembly gerado concorda com o interpretador).
#
# Casos invalidos: o compilador deve rejeita-los com codigo de saida != 0.

set -u
cd "$(dirname "$0")"

erros=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Detecta um toolchain x86-64 funcional. So checar "command -v as" nao basta:
# em macOS as/ld existem mas geram Mach-O/arm64, entao fazemos um probe real
# montando e linkando um programa minimo com "as --64".
tem_toolchain=0
if command -v as >/dev/null && command -v ld >/dev/null; then
  printf '  .section .text\n  .globl _start\n_start:\n  ret\n' > "$tmp/probe.s"
  if as --64 -o "$tmp/probe.o" "$tmp/probe.s" 2>/dev/null \
     && ld -o "$tmp/probe" "$tmp/probe.o" 2>/dev/null; then
    tem_toolchain=1
  fi
fi
if [[ $tem_toolchain -eq 0 ]]; then
  echo "(toolchain x86-64 as/ld indisponivel: os testes de execucao serao pulados;"
  echo " rode via Docker ou em Linux x86-64 para a verificacao cruzada completa)"
  echo
fi

# --- Casos validos -----------------------------------------------------------
validos="v1_constante v2_soma v3_sub v4_mult v5_div v6_aninhada_dir \
v7_aninhada_esq v8_ordem_sub v9_ordem_div v10_neg_trunc v11_grande \
v12_soma_mult v13_combinada"

for nome in $validos; do
  echo "Teste valido: $nome.ec1"
  src="testes/$nome.ec1"
  asm="$tmp/$nome.s"

  # 1. geracao de codigo
  if ! python3 compec1.py "$src" -o "$asm" >/dev/null; then
    echo "  FALHOU - erro ao gerar o assembly"
    erros=$((erros + 1)); continue
  fi

  # 2. interpretador (oraculo) vs golden output
  oraculo=$(python3 compec1.py --avaliar "$src")
  golden=$(cat "testes/esperado/$nome.out")
  if [[ "$oraculo" != "$golden" ]]; then
    echo "  FALHOU - interpretador deu '$oraculo', esperado '$golden'"
    erros=$((erros + 1)); continue
  fi

  # 3. verificacao cruzada: binario montado vs oraculo
  if [[ $tem_toolchain -eq 1 ]]; then
    if as --64 -o "$tmp/$nome.o" "$asm" 2>/dev/null \
       && ld -o "$tmp/$nome" "$tmp/$nome.o" 2>/dev/null; then
      saida=$("$tmp/$nome")
      if [[ "$saida" == "$oraculo" ]]; then
        echo "  PASSOU - binario=$saida = interpretador = golden"
      else
        echo "  FALHOU - binario deu '$saida', interpretador deu '$oraculo'"
        erros=$((erros + 1))
      fi
    else
      echo "  FALHOU - erro ao montar/linkar o assembly gerado"
      erros=$((erros + 1))
    fi
  else
    echo "  PASSOU (sem execucao) - interpretador=$oraculo = golden; .s gerado"
  fi
done

echo

# --- Casos invalidos ---------------------------------------------------------
invalidos="e1_paren e2_sem_operador e3_char_invalido e4_div_zero \
e5_div_zero_aninhada"

for nome in $invalidos; do
  echo "Teste invalido: $nome.ec1"
  if python3 compec1.py "testes/$nome.ec1" -o "$tmp/$nome.s" >/dev/null 2>&1; then
    echo "  FALHOU - o compilador aceitou entrada invalida"
    erros=$((erros + 1))
  else
    echo "  PASSOU - erro detectado e reportado"
  fi
done

echo
if [[ $erros -eq 0 ]]; then
  echo "Todos os testes passaram."
else
  echo "$erros teste(s) falharam."
fi
exit $erros
