# Atividade 10, Funcoes — RELATORIO

O que foi implementado e resultados, Compiladores, UFPB, julho de 2026

## 1. Resumo da entrega

Entregamos um compilador completo para a linguagem Fun, escrito em
Python 3 puro, estendendo diretamente o compilador da linguagem Cmd
entregue na atividade 9. Ele traduz o fonte para assembly x86_64 em
sintaxe AT&T e monta o executavel chamando o gcc. O pacote inclui as
quatro fases do compilador, um interpretador de referencia usado como
oraculo nos testes, 12 programas de teste validos, 10 casos de erro e
esta documentacao de uso.

Resultado: 22 de 22 testes passando, cada programa valido conferido
nas duas vias de execucao (interpretador e binario nativo).

## 2. Arquitetura final

| Fase | Arquivo | Entrada | Saida |
|------|---------|---------|-------|
| Lexica | `funlang/lexico.py` | texto do fonte | lista de tokens com linha e coluna |
| Sintatica | `funlang/sintatico.py` | tokens | arvore sintatica abstrata |
| Semantica | `funlang/semantico.py` | arvore | tabela de simbolos global + tabelas locais por funcao |
| Geracao | `funlang/codigo.py` | arvore e tabelas | assembly x86_64 |
| Apoio | `funlang/interp.py` | arvore | valor do resultado, usado nos testes |
| Interface | `func.py` | linha de comando | tokens, arvore, assembly ou executavel |

## 3. O que foi feito em cada fase

### 3.1 Analise lexica

Unico token novo: a virgula, usada para separar parametros formais na
declaracao de funcoes e parametros reais na chamada de funcao. Tres
novas palavras-chave: `fun`, `var` e `main`. O restante do
reconhecedor (numeros, identificadores, operadores de um e dois
caracteres, comentarios com `#`) e' o mesmo da atividade 9.

### 3.2 Analise sintatica

Descida recursiva, uma funcao por nao-terminal, como na atividade
anterior. Os pontos novos:

* A lista de declaracoes de topo (`<decl>*`) agora aceita `var
  ident = exp ;` ou `fun ident ( arglist? ) { ... }` e termina quando
  aparece a palavra-chave `main`.
* O reconhecimento de uma lista de parametros (formais ou reais) e'
  feito em looping simples: le' um item, e enquanto o proximo token for
  virgula, consome a virgula e le' outro item — exatamente o
  pseudocodigo da secao 4 do guia, adaptado para os dois casos
  (identificador na declaracao, expressao na chamada).
* A diferenciacao entre referencia a variavel e chamada de funcao e'
  feita com um lookahead de um token: dentro de `<prim>`, ao encontrar
  um identificador, o parser olha o token seguinte; se for `(`, e'
  chamada de funcao, caso contrario e' variavel.

### 3.3 Analise semantica

A tabela de simbolos global guarda, para cada nome, se ele denota uma
variavel global ou uma funcao — e, no caso de funcao, sua aridade e
sua tabela local (classe `Escopo`), como sugerido na secao 5.2 do
guia.

Verificacoes de funcao (secao 5.1):

* Uma chamada so' e' aceita se o nome estiver na tabela global marcado
  como funcao, com o numero de parametros reais batendo com o numero
  de parametros formais.
* As declaracoes sao processadas sequencialmente; uma funcao e'
  inserida na tabela global **antes** de seu proprio corpo ser
  verificado, o que permite recursao direta (o caso de `fib` da secao
  5.1) sem permitir recursao mutua — que, como o guia observa, fica
  como exercicio nao implementado aqui (testado no caso de erro
  `e09_recursao_mutua_nao_suportada.fun`).
* Declarar duas vezes o mesmo nome — variavel global, funcao,
  parametro ou variavel local — e' erro semantico. Usar o nome de uma
  funcao como variavel (ou de uma variavel como funcao) tambem e', com
  mensagens especificas para cada caso.

Verificacoes de variavel (secao 5.2):

* Ao checar o corpo de uma funcao `f`, a analise consulta primeiro a
  tabela local de `f` (parametros e variaveis locais, na ordem em que
  aparecem); se o nome nao estiver la, cai para a tabela global. Isso
  implementa o sombreamento descrito na secao 2: um parametro ou local
  esconde uma variavel global de mesmo nome.
* Fora de qualquer funcao (no bloco `main`), so' a tabela global e'
  consultada — nao ha' variaveis locais no bloco principal, pois a
  gramatica do guia so' inclui `<vardecl>*` no corpo de `fundecl`.

### 3.4 Geracao de codigo

Reaproveita o esquema de traducao de expressoes e comandos da
atividade 9 (toda expressao deixa o resultado em RAX; operacao binaria
avalia o lado direito, empilha, avalia o lado esquerdo, desempilha em
RBX e aplica a instrucao). O que muda:

* **Chamada de funcao**: os argumentos sao avaliados e empilhados em
  ordem inversa (ultimo primeiro), depois `call f_<nome>`; o chamador
  desfaz o espaco dos argumentos somando `8 * n` a RSP logo apos o
  `call`, exatamente a sequencia da secao 6.1.1.
* **Prologo/epilogo de funcao**, segundo a secao 6.1.2: `pushq %rbp`;
  `subq $8*L, %rsp` para reservar espaco das `L` variaveis locais;
  `movq %rsp, %rbp`. No fim, `addq $8*L, %rsp`; `popq %rbp`; `ret`.
* **Acesso a variaveis locais e parametros** (secao 6.1.3): cada
  variavel local `i` fica em `8*i(%rbp)`; cada parametro `j` fica em
  `(8*L + 16 + 8*j)(%rbp)` — os 16 bytes correspondem ao RBP antigo
  salvo na pilha e ao endereco de retorno empilhado pelo `CALL`. Essa
  formula foi conferida contra o exemplo passo a passo da secao 6.1.4
  do guia (funcao `f(x)` com locais `y`, `z`): o assembly gerado pelo
  compilador bate byte a byte com os deslocamentos do exemplo (`y` em
  `0(%rbp)`, `z` em `8(%rbp)`, `x` em `32(%rbp)`).
* **Referencia a variavel** (leitura, escrita ou `read`) escolhe entre
  RBP-relativo (se o nome existe na tabela local da funcao corrente) e
  RIP-relativo na BSS (caso contrario) — a mesma logica de fallback
  usada na analise semantica, agora aplicada a' geracao de codigo.
* O bloco `main` do programa Fun continua virando o rotulo `main` do
  assembly (montado como um `main` de C normal via gcc); cada funcao
  do usuario recebe o rotulo `f_<nome>`, para nunca colidir com nomes
  de biblioteca como `main`, `printf` ou `scanf`.

## 4. Extensoes mantidas da atividade 9

| Extensao | Como foi feita |
|---|---|
| Comparacoes `<=` `>=` `!=` | Mesmo nivel de precedencia das outras comparacoes. |
| Booleanos `and` `or` `not` | Curto-circuito por salto condicional, resultado normalizado em 0 ou 1. |
| `if` sem `else` | Braco opcional na gramatica. |
| Comando `read v;` | Le' um inteiro via `scanf`; agora tambem funciona dentro do corpo de uma funcao, gravando no local certo (RBP-relativo ou BSS). |
| Comentarios com `#` | Descartados no analisador lexico. |

## 5. Resultados dos testes

`python3 tests/rodar_testes.py` compila e executa tudo. Cada programa
valido roda no interpretador e no binario nativo, e os dois valores
sao comparados com o esperado declarado no topo do arquivo. Cada
programa de erro precisa falhar exatamente na fase indicada.

| Programa valido | Obtido |
|---|---|
| 01 abs (exemplo do guia) | 42 |
| 02 sem parametros | 42 |
| 03 multiplos locais (exemplo 6.1.4 do guia) | 131714583 |
| 04 fibonacci recursivo | 10946 |
| 05 fatorial recursivo | 3628800 |
| 06 fatorial iterativo (sem recursao) | 3628800 |
| 07 funcao chama funcao | 1612 |
| 08 multiplos parametros (chamadas aninhadas) | 121 |
| 09 sombreamento de global | 1006 |
| 10 read dentro de funcao | 105 |
| 11 logicos dentro de funcao | 1 |
| 12 mdc recursivo | 6 |

| Caso de erro | Fase obtida |
|---|---|
| e01 variavel nao declarada | semantico |
| e02 funcao nao declarada | semantico |
| e03 aridade incorreta | semantico |
| e04 parametro duplicado | semantico |
| e05 funcao duplicada | semantico |
| e06 variavel usada como funcao | semantico |
| e07 funcao usada como variavel | semantico |
| e08 variavel local nao visivel fora da funcao | semantico |
| e09 recursao mutua nao suportada | semantico |
| e10 falta a palavra-chave main | sintatico |

Resultado: 22 de 22 testes passando, sem divergencia entre
interpretador e binario nativo.

## 6. Aderencia ao planejamento

O planejamento seguiu diretamente a estrutura do guia da atividade 10:
estender as quatro fases do compilador da atividade 9 para suportar
declaracao e chamada de funcao, com enfase na convencao de chamada da
secao 6.1 (pilha + RBP como frame pointer). Todos os itens previstos
foram implementados: gramatica completa da secao 2.1, verificacoes
semanticas da secao 5, e geracao de codigo fiel ao exemplo passo a
passo da secao 6.1.4. O unico item que o proprio guia aponta como
opcional — recursao mutua — nao foi implementado, e esse
comportamento e' coberto por um caso de teste (`e09`).

## 7. Limitacoes e trabalho futuro

* Sem otimizacao: toda expressao passa pela pilha, mesmo quando um
  registrador bastaria, e toda variavel local ocupa 8 bytes fixos.
* Recursao mutua nao e' suportada (secao 5.1 do guia trata isso como
  exercicio opcional).
* Como na atividade 9, nao ha' deteccao de divisao por zero ou de
  transbordo aritmetico em tempo de compilacao.
* Nao ha' checagem de alinhamento de pilha de 16 bytes antes de
  chamadas a `printf`/`scanf` da libc; na pratica isso nao afetou os
  testes executados (gcc/glibc em x86_64 Linux), mas e' uma
  simplificacao herdada da atividade 9 que uma proxima iteracao
  poderia corrigir.
* Proximo passo natural, se pedido: permitir funcoes mutuamente
  recursivas, adiando a insercao de todas as funcoes na tabela global
  para antes da checagem de qualquer corpo de funcao.
