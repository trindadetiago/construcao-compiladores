# Atividade 04 - Analisador Lexico da linguagem EC1

Analisador lexico para a linguagem EC1 (Expressoes Constantes 1), referente a
Atividade 04 da disciplina de Compiladores. O analisador recebe um arquivo de
entrada e imprime a sequencia de tokens correspondente.

## Equipe

| Nome | Curso | Matricula | E-mail |
| --- | --- | --- | --- |
| Tiago Trindade de Oliveira | Ciencia da Computacao/CI | 20220054982 | tto@academico.ufpb.br |
| Ralf Dewrich Ferreira | Engenharia da Computacao/CI | 20220060783 | ralf.ferreira@academico.ufpb.br |
| Yan Fabber Lima de Albuquerque | Ciencia da Computacao/CI | 20220070805 | yan.fabber@gmail.com |
| Daniel Victor Carneiro Brandao da Costa | Ciencia da Computacao/CI | 20230089678 | danielvictorcarneiro21@gmail.com |

## A linguagem EC1

Um programa EC1 e uma expressao aritmetica com operandos constantes e as quatro
operacoes, com todas as operacoes entre parenteses:

```
333
(6 * 7)
(3 + (4 + (11 + 7)))
((427 / 7) + (11 * (231 + 5)))
```

O analisador lexico agrupa os caracteres em tokens e classifica cada um nas
classes lexicas da linguagem:

| Tipo | Lexema | Descricao |
| --- | --- | --- |
| `Numero` | um ou mais digitos | constante inteira |
| `ParenEsq` | `(` | parentese esquerdo |
| `ParenDir` | `)` | parentese direito |
| `Soma` | `+` | operador de soma |
| `Sub` | `-` | operador de subtracao |
| `Mult` | `*` | operador de multiplicacao |
| `Div` | `/` | operador de divisao |

Espacos em branco (espaco, tab, nova linha e retorno de carro - codigos ASCII
32, 9, 10 e 13) sao ignorados. Qualquer outro caractere e um **erro lexico**, e
o analisador reporta a posicao em que ele ocorreu.

> Todos os comandos abaixo assumem que voce esta dentro da pasta `atv4/`.

## Requisitos

- Python 3.8+ (sem dependencias externas). Quem preferir pode usar o Dockerfile
  incluido.

## Como executar o analisador

```sh
python3 lexec1.py <arquivo.ec1>
```

A saida e a sequencia de tokens, um por linha, no formato
`<tipo, lexema, posicao>`. A `posicao` e o deslocamento (indice) do primeiro
caractere do lexema dentro do arquivo. Por exemplo, para a entrada
`(33 + (912 * 11))`:

```
<ParenEsq, "(", 0>
<Numero, "33", 1>
<Soma, "+", 4>
<ParenEsq, "(", 6>
<Numero, "912", 7>
<Mult, "*", 11>
<Numero, "11", 13>
<ParenDir, ")", 15>
<ParenDir, ")", 16>
```

Se a entrada contiver um caractere invalido, o analisador imprime
`Erro lexico na posicao X` na saida de erro e termina com codigo diferente de
zero.

## Como rodar os testes

```sh
bash test.sh
```

O script roda 8 testes: 4 com entradas validas (constante simples, expressao
simples, expressao aninhada e expressao com variacoes de espacos/tabs/quebras de
linha) e 4 com entradas invalidas (caractere fora do alfabeto em posicoes
diferentes). Para os casos validos, a saida e comparada com o golden output em
`testes/esperado/`; para os invalidos, verifica-se que o erro lexico e detectado.

## Usando Docker

```sh
docker build -t lexec1 .
docker run --rm -v "$PWD":/app lexec1 testes/v2_simples.ec1
```

## Arquivos do projeto

| Arquivo | Descricao |
| --- | --- |
| `lexec1.py` | Analisador lexico da linguagem EC1. |
| `test.sh` | Script de testes (golden output + deteccao de erros). |
| `testes/*.ec1` | Entradas de teste (`v*` validas, `e*` invalidas). |
| `testes/esperado/*.out` | Saidas esperadas dos casos validos. |
| `Dockerfile` | Ambiente em container com Python. |
| `plano_relatorio_atv4.txt` | Plano e relatorio da atividade. |
