#!/usr/bin/env bash
# Testes do compilador EV com verificacao automatica.
#
# Casos validos:
#   1. compila o .ev -> .s;
#   2. compara --avaliar com o golden output;
#   3. se houver as/ld x86-64, monta/linka/executa e compara com o oraculo.
#
# Casos invalidos: o compilador deve rejeitar com codigo de saida != 0.

set -u
cd "$(dirname "$0")"

erros=0
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

tem_toolchain=0
if command -v as >/dev/null && command -v ld >/dev/null; then
  cat > "$tmp/probe.s" <<'PROBE'
  .section .text
  .globl _start
_start:
  mov $0, %rax
  call imprime_num
  call sair
  .include "runtime.s"
PROBE
  if as --64 -o "$tmp/probe.o" "$tmp/probe.s" 2>/dev/null \
     && ld -o "$tmp/probe" "$tmp/probe.o" 2>/dev/null \
     && "$tmp/probe" >/dev/null 2>&1; then
    tem_toolchain=1
  fi
fi
if [[ $tem_toolchain -eq 0 ]]; then
  echo "(toolchain x86-64 as/ld indisponivel: os testes de execucao serao pulados;"
  echo " rode via Docker ou em Linux x86-64 para a verificacao cruzada completa)"
  echo
fi

validos="v1_resultado v2_variavel_simples v3_perimetro v4_dependencias \
v5_precedencia v6_assoc_sub v7_div_neg v8_ident_digitos v9_maiusculas \
v10_zero_decls_parenteses"

for nome in $validos; do
  echo "Teste valido: $nome.ev"
  src="testes/$nome.ev"
  asm="$tmp/$nome.s"

  if ! python3 compev.py "$src" -o "$asm" >/dev/null; then
    echo "  FALHOU - erro ao gerar o assembly"
    erros=$((erros + 1)); continue
  fi

  if ! oraculo=$(python3 compev.py --avaliar "$src"); then
    echo "  FALHOU - erro ao avaliar o programa"
    erros=$((erros + 1)); continue
  fi
  golden=$(cat "testes/esperado/$nome.out")
  if [[ "$oraculo" != "$golden" ]]; then
    echo "  FALHOU - interpretador deu '$oraculo', esperado '$golden'"
    erros=$((erros + 1)); continue
  fi

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

invalidos="e1_var_decl_nao_declarada e2_var_resultado_nao_declarada \
e3_ident_com_digito_inicio e4_sem_ponto_virgula e5_sem_resultado \
e6_unario e7_div_zero_decl e8_token_extra_resultado e9_char_invalido \
e10_exp_incompleta e11_digito_unicode"

for nome in $invalidos; do
  echo "Teste invalido: $nome.ev"
  if python3 compev.py "testes/$nome.ev" -o "$tmp/$nome.s" >/dev/null 2>&1; then
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
