# Compilador da linguagem Cmd

Atividade 09, Compiladores, UFPB.

**Grupo:** Daniel Victor, Tiago Trindade, Yann Fabber, Ralf Dwerich.

Compilador completo para a linguagem Cmd: análise léxica, análise sintática,
análise semântica e geração de código x86_64 (sintaxe AT&T, montado com gcc).
Escrito em Python 3 puro, sem dependências externas.

## Requisitos

* Python 3.8 ou superior
* gcc (para montar e linkar o assembly gerado)
* Linux x86_64 para executar os binários

O interpretador de referência (`interp`) roda em qualquer plataforma e serve
para validar a semântica quando não há x86_64 disponível.

## Como executar

```
python3 cmdc.py <acao> <fonte.cmd> [saida]
```

| Ação | O que faz |
|------|-----------|
| `tokens` | lista os tokens produzidos pelo analisador léxico |
| `ast` | mostra a árvore sintática abstrata |
| `check` | roda as três análises e reporta erros |
| `asm` | gera o assembly x86_64 (stdout ou arquivo) |
| `build` | gera o executável chamando o gcc |
| `run` | compila para um executável temporário e executa |
| `interp` | executa pelo interpretador de referência |

Exemplos:

```
python3 cmdc.py run tests/programas/05_mdc.cmd
python3 cmdc.py asm tests/programas/02_delta.cmd delta.s
python3 cmdc.py build tests/programas/09_fatorial.cmd fatorial
echo 10 | python3 cmdc.py run tests/programas/12_leitura.cmd
```

O programa compilado imprime o valor da expressão de resultado em stdout e
termina com código de saída 0.

## Como rodar os testes

```
python3 tests/rodar_testes.py
```

ou `make test`. Cada programa em `tests/programas` é executado duas vezes, pelo
interpretador de referência e pelo binário nativo, e os dois resultados são
comparados com o valor esperado declarado no topo do arquivo. Cada programa em
`tests/erros` deve falhar na fase indicada no topo do arquivo. São 23 testes:
16 programas válidos e 7 casos de erro.

## Estrutura

```
cmdc.py                 interface de linha de comando
cmdlang/lexico.py       analisador léxico
cmdlang/sintatico.py    analisador sintático (descida recursiva)
cmdlang/ast.py          nós da árvore sintática
cmdlang/semantico.py    tabela de símbolos e verificações
cmdlang/codigo.py       gerador de código x86_64
cmdlang/interp.py       interpretador de referência
cmdlang/erros.py        erros com fase, linha e coluna
tests/programas/        programas válidos com resultado esperado
tests/erros/            programas que devem falhar
docs/planejamento.pdf   plano de execução, escrito antes
docs/relatorio.pdf      relatório do que foi feito e resultados
```

## Gramática implementada

```
<programa>  ::= <decl>* '{' <cmd>* 'return' <exp> ';' '}'
<decl>      ::= <var> '=' <exp> ';'
<var>       ::= <letra><letra_digito>*
<cmd>       ::= <if> | <while> | <atrib> | <read>
<if>        ::= 'if' <exp> '{' <cmd>* '}' ('else' '{' <cmd>* '}')?
<while>     ::= 'while' <exp> '{' <cmd>* '}'
<atrib>     ::= <var> '=' <exp> ';'
<read>      ::= 'read' <var> ';'
<exp>       ::= <exp_ou>
<exp_ou>    ::= <exp_e> ('or' <exp_e>)*
<exp_e>     ::= <exp_nao> ('and' <exp_nao>)*
<exp_nao>   ::= 'not' <exp_nao> | <exp_c>
<exp_c>     ::= <exp_a> (('<' | '>' | '==' | '<=' | '>=' | '!=') <exp_a>)*
<exp_a>     ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>     ::= <prim> (('*' | '/') <prim>)*
<prim>      ::= <num> | <var> | '(' <exp> ')'
<num>       ::= <digito><digito>*
```

Precedência, da mais baixa para a mais alta: `or`, `and`, `not`, comparações,
soma e subtração, multiplicação e divisão, primárias.

## Diferenças em relação ao guia

Extensões implementadas, todas previstas na seção Variações do guia:

* Operadores de comparação `<=`, `>=` e `!=`, no mesmo nível de precedência de `<`, `>` e `==`.
* Operadores booleanos `and`, `or` e `not`, em três novos níveis de precedência abaixo das comparações. Avaliação com curto circuito, resultado normalizado em 0 ou 1.
* O braço `else` é opcional. A ambiguidade do dangling else não existe aqui porque as chaves são obrigatórias.
* Comando `read <var>;` lê um inteiro da entrada padrão e atribui à variável, que precisa estar declarada.
* Comentários de linha iniciados por `#`.

Decisões de projeto que o guia deixa em aberto:

* A restrição de que a atribuição não cria variáveis foi mantida. Atribuir a uma variável não declarada é erro semântico.
* Declarar a mesma variável duas vezes é erro semântico.
* O resultado é impresso com `printf` em vez de virar código de saída do processo, para suportar valores fora da faixa de 0 a 255 e valores negativos.
* Na gramática do guia, o fecho `*` sobre o grupo de operadores de comparação é um erro de digitação. Aqui cada comparação consome exatamente um operador, com associatividade à esquerda.
* Aritmética de 64 bits com sinal. A divisão trunca em direção a zero, seguindo a instrução `IDIV`.

## Modelo de código gerado

Variáveis viram símbolos de 8 bytes na seção `.bss`, acessados de forma
relativa a RIP. Toda expressão deixa o resultado em RAX. Operações binárias
avaliam o lado direito, empilham RAX, avaliam o lado esquerdo, desempilham em
RBX e aplicam a instrução. Comparações usam `CMP` seguido de `SETcc` sobre CL e
transferem RCX para RAX. Condicionais e repetições usam `CMP` contra zero, `JZ`
e rótulos numerados por um contador global.
