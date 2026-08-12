# Compilador da linguagem Fun

Atividade 10, Compiladores, UFPB.

Compilador completo para a linguagem Fun (linguagem Cmd + funcoes):
analise lexica, analise sintatica, analise semantica e geracao de
codigo x86_64 (sintaxe AT&T, montado com gcc). Escrito em Python 3
puro, sem dependencias externas, estendendo diretamente o compilador
da linguagem Cmd entregue na atividade 9.

## Requisitos

* Python 3.8 ou superior
* gcc (para montar e linkar o assembly gerado)
* Linux x86_64 para executar os binarios

O interpretador de referencia (`interp`) roda em qualquer plataforma e
serve para validar a semantica quando nao ha x86_64 disponivel.

## Como executar

```
python3 func.py <acao> <fonte.fun> [saida]
```

| Acao | O que faz |
|------|-----------|
| `tokens` | lista os tokens produzidos pelo analisador lexico |
| `ast` | mostra a arvore sintatica abstrata |
| `check` | roda as tres analises e reporta erros |
| `asm` | gera o assembly x86_64 (stdout ou arquivo) |
| `build` | gera o executavel chamando o gcc |
| `run` | compila para um executavel temporario e executa |
| `interp` | executa pelo interpretador de referencia |

Exemplos:

```
python3 func.py run tests/programas/04_fibonacci_recursivo.fun
python3 func.py asm tests/programas/01_abs.fun abs.s
python3 func.py build tests/programas/05_fatorial_recursivo.fun fatorial
echo 100 | python3 func.py run tests/programas/10_read_dentro_de_funcao.fun
```

O programa compilado imprime o valor da expressao de resultado do bloco
`main` em stdout e termina com codigo de saida 0.

## Como rodar os testes

```
python3 tests/rodar_testes.py
```

ou `make test`. Cada programa em `tests/programas` e executado duas
vezes, pelo interpretador de referencia e pelo binario nativo, e os
dois resultados sao comparados com o valor esperado declarado no topo
do arquivo (comentario `# esperado: ...`, e opcionalmente `# entrada:
...` quando o programa usa `read`). Cada programa em `tests/erros` deve
falhar na fase indicada no topo do arquivo (`# erro: sintatico` ou
`# erro: semantico`). Sao 22 testes: 12 programas validos e 10 casos de
erro.

`make exemplos` roda todos os programas validos pelo interpretador e
imprime o resultado de cada um.

## Estrutura

```
func.py                  interface de linha de comando
funlang/lexico.py        analisador lexico
funlang/sintatico.py     analisador sintatico (descida recursiva)
funlang/ast.py           nos da arvore sintatica
funlang/semantico.py     tabela de simbolos global + tabelas locais por funcao
funlang/codigo.py        gerador de codigo x86_64
funlang/interp.py        interpretador de referencia
funlang/erros.py         erros com fase, linha e coluna
tests/programas/         programas validos com resultado esperado
tests/erros/             programas que devem falhar
docs/relatorio.md        relatorio do que foi feito e resultados
```

## Gramatica implementada

```
<programa>  ::= <decl>* 'main' '{' <cmd>* 'return' <exp> ';' '}'
<decl>      ::= <vardecl> | <fundecl>
<vardecl>   ::= 'var' <ident> '=' <exp> ';'
<fundecl>   ::= 'fun' <ident> '(' <arglist>? ')'
                '{' <vardecl>* <cmd>* 'return' <exp> ';' '}'
<arglist>   ::= <ident> (',' <ident>)*
<cmd>       ::= <if> | <while> | <atrib> | <read>
<if>        ::= 'if' <exp> '{' <cmd>* '}' ('else' '{' <cmd>* '}')?
<while>     ::= 'while' <exp> '{' <cmd>* '}'
<atrib>     ::= <ident> '=' <exp> ';'
<read>      ::= 'read' <ident> ';'
<exp>       ::= <exp_ou>
<exp_ou>    ::= <exp_e> ('or' <exp_e>)*
<exp_e>     ::= <exp_nao> ('and' <exp_nao>)*
<exp_nao>   ::= 'not' <exp_nao> | <exp_c>
<exp_c>     ::= <exp_a> (('<' | '>' | '==' | '<=' | '>=' | '!=') <exp_a>)*
<exp_a>     ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>     ::= <prim> (('*' | '/') <prim>)*
<prim>      ::= <num> | <ident> | '(' <exp> ')' | <fun>
<fun>       ::= <ident> '(' <params>? ')'
<params>    ::= <exp> (',' <exp>)*
<ident>     ::= <letra><letra_digito>*
<num>       ::= <digito><digito>*
```

Precedencia, da mais baixa para a mais alta: `or`, `and`, `not`,
comparacoes, soma e subtracao, multiplicacao e divisao, primarias.

## Diferencas em relacao ao guia

Extensoes ja presentes na atividade 9 (Cmd), mantidas em Fun:

* Operadores de comparacao `<=`, `>=` e `!=`.
* Operadores booleanos `and`, `or` e `not`, com curto-circuito.
* O braco `else` e opcional.
* Comando `read <var>;`, valido tambem dentro do corpo de uma funcao,
  gravando no registro de ativacao quando a variavel e local.
* Comentarios de linha iniciados por `#`.

Decisoes de projeto especificas da linguagem Fun, que o guia deixa em
aberto ou aponta como opcionais:

* **Recursao mutua nao e suportada**, exatamente como o guia antecipa
  na secao 5.1: as declaracoes sao processadas em ordem sequencial e
  uma funcao so entra na tabela de simbolos apos ser declarada (o que
  permite recursao direta). Fica como exercicio nao implementado.
* O bloco `main` nao admite declaracao de variaveis locais propria
  (`var` dentro de `main`), seguindo a gramatica literal do guia — que
  so' inclui `<vardecl>*` no corpo de `fundecl`, nao no corpo do
  `main`. Para guardar estado no bloco principal, use uma variavel
  global.
* Chamada de funcao so' e permitida em posicao de expressao (`<prim>`),
  nunca como comando isolado — tambem conforme a gramatica do guia
  (nao existe producao de "chamada como comando" em `<cmd>`).
* Declarar duas vezes o mesmo nome (variavel global, funcao, parametro
  ou variavel local) e' erro semantico, incluindo usar o mesmo nome
  para uma variavel global e uma funcao.
* Usar o nome de uma funcao como se fosse variavel (ou vice-versa) e'
  erro semantico com mensagem especifica, para evitar confusao entre os
  dois espacos de nomes.
* Multiplicacao usa `imulq` (com sinal), diferente do `mul` (sem sinal)
  do exemplo ilustrativo da secao 6.1.4 do guia — mantendo a mesma
  aritmetica de 64 bits com sinal usada no resto da linguagem.
* Como na atividade 9, o resultado e impresso com `printf` (nao vira
  codigo de saida do processo), o bloco principal continua sendo
  montado sob o rotulo `main` do assembly (para link direto com o
  gcc/libc), e cada funcao definida pelo usuario recebe o rotulo
  `f_<nome>` para nao colidir com simbolos de biblioteca.

## Modelo de geracao de codigo para funcoes

Segue a convencao de chamada da secao 6.1 do guia:

* **Chamada**: os parametros sao avaliados e empilhados em ordem
  inversa (ultimo parametro primeiro), depois `call f_<nome>`; ao
  voltar, o chamador desfaz o espaco dos parametros somando `8 *
  numero_de_argumentos` a RSP. O resultado sempre volta em RAX.
* **Prologo de uma funcao com L variaveis locais**: `pushq %rbp`;
  `subq $8*L, %rsp` (omitido quando L=0); `movq %rsp, %rbp`. A partir
  dai, RBP e o frame pointer do registro de ativacao.
* **Deslocamentos**, calculados exatamente como no exemplo da secao
  6.1.4: a i-esima variavel local fica em `8*i(%rbp)`; o j-esimo
  parametro fica em `(8*L + 16 + 8*j)(%rbp)` — os 16 bytes cobrem o RBP
  anterior salvo na pilha e o endereco de retorno empilhado pelo CALL.
* **Epilogo**: `addq $8*L, %rsp` (desfaz o espaco das locais); `popq
  %rbp` (restaura o RBP do chamador); `ret`.
* Uma referencia a variavel (leitura, escrita ou `read`) usa o
  deslocamento de RBP quando o nome existe na tabela local da funcao
  corrente, e cai para o simbolo da BSS (relativo a RIP) caso
  contrario — implementando o sombreamento descrito na secao 2 do
  guia.

## Aderencia ao guia

O compilador cobre integralmente a gramatica da secao 2.1: declaracoes
de variavel e de funcao misturadas antes do `main`, parametros e
variaveis locais visiveis so' dentro da funcao, sombreamento de
variavel global por parametro/local de mesmo nome, chamada de funcao
como expressao primaria diferenciada de referencia a variavel pelo
lookahead descrito na secao 4, verificacao de numero de parametros e de
declaracao previa (com recursao direta permitida) descrita na secao
5.1, tabela de simbolos local por funcao com fallback para a tabela
global descrita na secao 5.2, e a convencao de chamada baseada em pilha
com RBP como frame pointer descrita na secao 6.1.
