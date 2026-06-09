#!/usr/bin/env bash
# Testes do analisador sintatico e interpretador da linguagem EC1.
#
# Casos validos: a saida do programa e comparada com o golden output
# guardado em testes/esperado/.
# Casos invalidos: o programa deve reportar um erro e sair com codigo
# diferente de zero.

set -u
cd "$(dirname "$0")"

erros=0

# --- Entradas validas: comparar saida com o golden output ---
validos="v1_constante v2_simples v3_aninhada v4_espacos v5_soma_aninhada"
for nome in $validos; do
  echo "Teste valido: $nome.ec1"
  saida=$(python3 parsec1.py "testes/$nome.ec1")
  rc=$?
  esperado=$(cat "testes/esperado/$nome.out")
  if [[ $rc -eq 0 && "$saida" == "$esperado" ]]; then
    echo "  PASSOU - saida bate com o esperado"
  else
    echo "  FALHOU - saida diferente do esperado (rc=$rc)"
    diff <(printf '%s\n' "$esperado") <(printf '%s\n' "$saida")
    erros=$((erros + 1))
  fi
done

echo

# --- Entradas invalidas: devem ser rejeitadas com erro lexico ou sintatico ---
invalidos="e1_sem_fecha e2_sem_operador e3_operador_inicio e4_tokens_extras"
for nome in $invalidos; do
  echo "Teste invalido: $nome.ec1"
  if python3 parsec1.py "testes/$nome.ec1" >/dev/null 2>&1; then
    echo "  FALHOU - o analisador aceitou entrada invalida"
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
