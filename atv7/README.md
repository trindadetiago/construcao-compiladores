# Atividade 07 - Compilador da linguagem EC2

Compilador completo para a linguagem EC2 (Expressoes Constantes 2), referente
a Atividade 07 da disciplina de Compiladores. Esta entrega parte do compilador
da Atividade 06 e troca a gramatica de expressoes para aceitar operadores sem
parenteses obrigatorios, respeitando precedencia e associatividade.

## Equipe

| Nome | Curso | Matricula | E-mail |
| --- | --- | --- | --- |
| Tiago Trindade de Oliveira | Ciencia da Computacao/CI | 20220054982 | tto@academico.ufpb.br |
| Ralf Dewrich Ferreira | Engenharia da Computacao/CI | 20220060783 | ralf.ferreira@academico.ufpb.br |
| Yan Fabber Lima de Albuquerque | Ciencia da Computacao/CI | 20220070805 | yan.fabber@gmail.com |
| Daniel Victor Carneiro Brandao da Costa | Ciencia da Computacao/CI | 20230089678 | danielvictorcarneiro21@gmail.com |

## A linguagem EC2

Um programa EC2 e uma expressao aritmetica com constantes inteiras, os quatro
operadores basicos e parenteses opcionais para alterar a ordem natural das
operacoes:

```text
333
6 * 7
7 + 5 * 3
(7 + 5) * 3
2 * (3 + 4) + 5
```

A gramatica reconhecida pelo analisador sintatico e:

```text
<programa> ::= <exp_a>
<exp_a>   ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>   ::= <prim>  (('*' | '/') <prim>)*
<prim>    ::= <num> | '(' <exp_a> ')'
<num>     ::= <digito>+
```

O nivel `<exp_m>` tem precedencia maior que `<exp_a>`, portanto multiplicacao
e divisao sao agrupadas antes de soma e subtracao. Operadores no mesmo nivel
sao associativos a esquerda: `10 - 8 - 2` e interpretado como `(10 - 8) - 2`.

## Arquitetura

O compilador continua organizado nas mesmas camadas da Atividade 06:

| Camada | Classe/funcao | Descricao |
| --- | --- | --- |
| Analise lexica | `Lexer` | Reconhece numeros, parenteses, operadores e fim de entrada |
| Analise sintatica | `Parser` | Produz a AST usando as regras `exp_a`, `exp_m` e `prim` |
| Interpretacao | `Exp.avaliar()` | Calcula o valor inteiro da AST, usado como oraculo dos testes |
| Geracao de codigo | `Exp.gerar()` | Emite assembly x86-64, igual ao esquema da Atividade 06 |

A AST nao muda: constantes usam `Const` e operacoes binarias usam `OpBin`.
A geracao de codigo tambem nao muda; cada expressao deixa seu resultado em
`%rax`, e o runtime imprime esse valor.

### Pontos de atencao do parser

- O lookahead (`self._lookahead`) e consultado antes de consumir tokens. O
  parser so chama `_avanca()` quando ja sabe que o token atual e operador do
  nivel sendo analisado.
- A associatividade a esquerda e preservada atualizando o acumulador:
  `esq = OpBin(operador, esq, dir)`. Assim, `100 / 10 / 2` vira
  `(100 / 10) / 2`, nao `100 / (10 / 2)`.
- Parenteses continuam existindo, mas agora sao tratados em `<prim>`:
  `'(' <exp_a> ')'`.

## Como usar

Todos os comandos abaixo assumem que voce esta dentro da pasta `atv7/`.

```sh
python3 compec2.py <arquivo.ec2|arquivo.ec1> [-o saida.s] [--otimizar]
```

Por padrao, o assembly e gravado em um arquivo com o mesmo nome da entrada e
extensao `.s`. Com `-o -`, o assembly e escrito na saida padrao sem linhas
extras.

```sh
$ python3 compec2.py testes/v14_precedencia.ec1 -o prog.s
gerado: prog.s
```

### Opcoes auxiliares

- `--avaliar`: imprime apenas o valor inteiro da expressao.
  ```sh
  $ python3 compec2.py --avaliar testes/v15_assoc_sub.ec1
  0
  ```
- `--otimizar`: calcula a constante em tempo de compilacao e emite um unico
  `mov $<resultado>, %rax`.

### Montar e executar o assembly

Em Linux x86-64 com `as` e `ld` disponiveis:

```sh
as --64 -o prog.o prog.s
ld -o prog prog.o
./prog
```

## Erros

Caracteres fora do alfabeto geram `Erro lexico`; violacoes da gramatica geram
`Erro sintatico`; divisao por zero gera `Erro de compilacao`. Em todos os
casos, a mensagem vai para `stderr` e o programa termina com codigo diferente
de zero.

O compilador nao implementa operador unario. Portanto `-1 + 2` e rejeitado.

## Como rodar os testes

```sh
bash test.sh
```

A suite contem casos validos herdados da Atividade 06 e novos casos EC2 sem
parenteses obrigatorios. Os principais casos novos cobrem:

- precedencia: `7 + 5 * 3` resulta em `22`;
- associatividade a esquerda em subtracao: `10 - 8 - 2` resulta em `0`;
- associatividade a esquerda em divisao: `100 / 10 / 2` resulta em `5`;
- parenteses alterando precedencia: `(7 + 5) * 3` resulta em `36`;
- lookahead sem consumir `)`: `2 * (3 + 4) + 5` resulta em `19`.

Para cada caso valido, o script gera assembly, compara `--avaliar` com o
golden output e, se houver toolchain x86-64 funcional, monta, linka e executa o
binario para comparar a saida real com o oraculo.

## Usando Docker

A imagem inclui `binutils` e `python3`, permitindo rodar a suite completa em um
ambiente Linux x86-64:

```sh
docker build -t compec2 .
docker run --rm -v "$PWD":/app compec2
```

Para compilar e executar uma expressao especifica:

```sh
docker run --rm -v "$PWD":/app compec2 bash -c \
  "python3 compec2.py testes/v14_precedencia.ec1 -o prog.s && \
   as --64 -o prog.o prog.s && ld -o prog prog.o && ./prog"
```

## Arquivos do projeto

| Arquivo | Descricao |
| --- | --- |
| `compec2.py` | Compilador EC2: lexico, sintatico, interpretador e gerador |
| `runtime.s` | Sub-rotinas `imprime_num` e `sair` |
| `test.sh` | Testes automaticos com oraculo e verificacao cruzada |
| `Dockerfile` | Ambiente em container com `binutils` e `python3` |
| `testes/*.ec1` | Entradas de teste validas e invalidas |
| `testes/esperado/*.out` | Saidas esperadas dos casos validos |
