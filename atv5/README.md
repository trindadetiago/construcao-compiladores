# Atividade 05 - Analisador Sintático e Interpretador da linguagem EC1

Analisador sintático descendente recursivo para a linguagem EC1
(Expressões Constantes 1), referente à Atividade 05 da disciplina de
Compiladores. O programa reutiliza o analisador léxico da Atividade 04,
produz a árvore de sintaxe abstrata (AST) e a interpreta por varredura
de árvore, imprimindo o valor da expressão.

## Equipe

| Nome | Curso | Matrícula | E-mail |
| --- | --- | --- | --- |
| Tiago Trindade de Oliveira | Ciência da Computação/CI | 20220054982 | tto@academico.ufpb.br |
| Ralf Dewrich Ferreira | Engenharia da Computação/CI | 20220060783 | ralf.ferreira@academico.ufpb.br |
| Yan Fabber Lima de Albuquerque | Ciência da Computação/CI | 20220070805 | yan.fabber@gmail.com |
| Daniel Victor Carneiro Brandão da Costa | Ciência da Computação/CI | 20230089678 | danielvictorcarneiro21@gmail.com |

## A linguagem EC1

Um programa EC1 é uma expressão aritmética com operandos constantes e as
quatro operações, com todas as operações entre parênteses:

```
333
(6 * 7)
(3 + (4 + (11 + 7)))
((427 / 7) + (11 * (231 + 5)))
```

A gramática reconhecida pelo analisador sintático é:

```
<programa>   ::= <expressao>
<expressao>  ::= <literal> | '(' <expressao> <operador> <expressao> ')'
<operador>   ::= '+' | '-' | '*' | '/'
<literal>    ::= <digito>+
```

## Arquitetura

O projeto é composto por três camadas:

| Camada | Classe | Descrição |
| --- | --- | --- |
| Análise léxica | `Lexer` | Reutilizado da Atividade 04; fornece `proximo_token()` |
| Análise sintática | `Parser` | Descendente recursivo; produz a AST |
| Interpretação | `Exp.avaliar()` | Varredura de árvore; retorna o valor inteiro |

### Nós da AST

| Classe | Campos | Descrição |
| --- | --- | --- |
| `Const` | `valor: int` | Constante inteira (folha da árvore) |
| `OpBin` | `operador, esq, dir` | Operação binária com dois sub-nós |

> Todos os comandos abaixo assumem que você está dentro da pasta `atv5/`.

## Requisitos

- Python 3.8+ (sem dependências externas). Quem preferir pode usar o Dockerfile
  incluído.

## Como executar o analisador

```sh
python3 parsec1.py <arquivo.ec1>
```

A saída é o valor inteiro da expressão. Por exemplo:

```sh
$ echo "(33 + (912 * 11))" | python3 parsec1.py /dev/stdin
10065
```

### Opção `--arvore`

Para exibir também a representação em notação parentesizada da AST antes
do valor, use a opção `--arvore`:

```sh
$ python3 parsec1.py --arvore testes/v3_aninhada.ec1
(33 + (912 * 11))
10065
```

### Erros léxicos e sintáticos

Se a entrada contiver um caractere inválido, o analisador imprime
`Erro lexico na posicao X` em stderr e termina com código diferente de zero.

Se a entrada violar a gramática (parêntese não fechado, operador ausente,
tokens após o fim da expressão, etc.), o analisador imprime
`Erro sintatico na posicao X: <mensagem>` em stderr e termina com código
diferente de zero.

Exemplos de erros detectados:

```sh
$ python3 parsec1.py testes/e1_sem_fecha.ec1
Erro sintatico na posicao 6: esperado ParenDir, encontrado EOF

$ python3 parsec1.py testes/e2_sem_operador.ec1
Erro sintatico na posicao 3: operador esperado, encontrado 'Numero' ('7')
```

## Como rodar os testes

```sh
bash test.sh
```

O script roda 9 testes: 5 com entradas válidas (constante simples, operação
simples, expressão aninhada, expressão com variações de espaços/tabs/quebras
de linha e soma profundamente aninhada) e 4 com entradas inválidas (parêntese
não fechado, operador ausente, operador onde deveria haver operando e tokens
extras após a expressão). Para os casos válidos, a saída é comparada com o
golden output em `testes/esperado/`; para os inválidos, verifica-se que o
erro é detectado e o programa termina com código diferente de zero.

## Usando Docker

```sh
docker build -t parsec1 .
docker run --rm -v "$PWD":/app parsec1 testes/v2_simples.ec1
docker run --rm -v "$PWD":/app parsec1 --arvore testes/v3_aninhada.ec1
```

## Arquivos do projeto

| Arquivo | Descrição |
| --- | --- |
| `parsec1.py` | Analisador léxico, sintático e interpretador da linguagem EC1 |
| `test.sh` | Script de testes (golden output + detecção de erros) |
| `testes/*.ec1` | Entradas de teste (`v*` válidas, `e*` inválidas) |
| `testes/esperado/*.out` | Saídas esperadas dos casos válidos |
| `Dockerfile` | Ambiente em container com Python |
