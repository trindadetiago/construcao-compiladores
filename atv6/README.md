# Atividade 06 - Compilador da linguagem EC1

Compilador completo para a linguagem EC1 (Expressões Constantes 1), referente
à Atividade 06 da disciplina de Compiladores. O programa reúne as etapas das
atividades anteriores — análise léxica (Atividade 04), análise sintática e
interpretação (Atividade 05) — e adiciona um **gerador de código** que traduz
a expressão para **assembly x86-64 (GAS/AT&T, Linux)**, pronto para ser montado
e executado.

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

A gramática da linguagem é:

```
<programa>   ::= <expressao>
<expressao>  ::= <literal> | '(' <expressao> <operador> <expressao> ')'
<operador>   ::= '+' | '-' | '*' | '/'
<literal>    ::= <digito>+
```

## Arquitetura

O compilador é dividido em quatro camadas. As três primeiras vêm das atividades
anteriores; a geração de código é a novidade desta atividade.

| Camada | Classe/Função | Descrição |
| --- | --- | --- |
| Análise léxica | `Lexer` | Reutilizado da Atividade 04; fornece `proximo_token()` |
| Análise sintática | `Parser` | Descendente recursivo; produz a AST |
| Interpretação | `Exp.avaliar()` | Varredura da árvore; calcula o valor (usado como oráculo nos testes) |
| Geração de código | `Exp.gerar()` | Varredura da árvore; emite o assembly x86-64 |

### Nós da AST

| Classe | Campos | `gerar()` emite |
| --- | --- | --- |
| `Const` | `valor: int` | `mov $<valor>, %rax` |
| `OpBin` | `operador, esq, dir` | código dos operandos + a instrução da operação |

### Esquema de tradução

A geração de código é recursiva, no mesmo estilo de `avaliar()` e `imprimir()`:
cada nó recebe um emissor (lista de linhas) e anexa suas instruções. A
convenção é que o resultado da expressão termine no registrador `%rax`.

Para uma operação binária usamos a **pilha** para guardar o resultado
intermediário, no esquema "direito primeiro", que deixa os operandos já na
ordem certa para a subtração e a divisão:

1. gera o operando **direito** (resultado em `%rax`);
2. `push %rax` (salva o direito na pilha);
3. gera o operando **esquerdo** (resultado em `%rax`);
4. `pop %rbx` (recupera o direito em `%rbx`);
5. agora **esquerdo em `%rax`, direito em `%rbx`** — executa a operação:

```asm
add  %rbx, %rax     # SOMA:  rax = esq + dir
sub  %rbx, %rax     # SUB:   rax = esq - dir
imul %rbx, %rax     # MULT:  rax = esq * dir
cqo                 # DIV:   estende o sinal de rax em rdx:rax
idiv %rbx           #        rax = esq / dir (quociente)
```

Cada `OpBin` empilha e desempilha exatamente um valor, então a pilha sempre
volta ao estado inicial. O esquema funciona para qualquer aninhamento e
tamanho de expressão, usando apenas `%rax`, `%rbx` (e `%rdx`, implícito no
`idiv`) além da pilha. Um programa que é só uma constante (ex.: `333`) gera
apenas `mov $333, %rax`.

O código da expressão é inserido no modelo completo do arquivo (o mesmo das
Atividades 02/03), que ao final chama as sub-rotinas `imprime_num` e `sair`
de `runtime.s`:

```asm
  .section .text
  .globl _start

_start:
  # <codigo gerado para a expressao>

  call imprime_num
  call sair

  .include "runtime.s"
```

### Semântica da divisão

A divisão inteira do EC1 é **truncada em direção a zero**, consistente com a
instrução `idiv` do hardware (estilo C). Isso difere do operador `//` do
Python, que arredonda para baixo: os dois divergem quando os operandos têm
sinais diferentes (algo possível em EC1 via subtração). Por exemplo,
`((0 - 7) / 2)` resulta em `-3` (truncado), e não `-4` (piso). O interpretador
(`avaliar()`) usa o auxiliar `div_trunc` para adotar a mesma semântica do
assembly gerado, garantindo que ambos concordem.

**Divisão por zero:** como todos os valores são constantes, ela é detectada em
**tempo de compilação** (avaliando a árvore). O compilador imprime um erro em
`stderr` e termina com código de saída diferente de zero, sem gerar assembly.

## Requisitos

- Python 3.8+ (sem dependências externas) para gerar o assembly.
- `binutils` (`as` e `ld`) para montar e linkar o `.s` em um executável Linux
  x86-64. Quem não estiver em Linux x86-64 pode usar o Dockerfile incluído.

> Todos os comandos abaixo assumem que você está dentro da pasta `atv6/`.

## Como compilar uma expressão

```sh
python3 compec1.py <arquivo.ec1> [-o saida.s] [--otimizar]
```

Por padrão o assembly é gravado em um arquivo com o mesmo nome do `.ec1` e
extensão `.s` (ou no caminho passado em `-o`). Com `-o -` o assembly é escrito
na saída padrão, sem nenhuma linha extra.

```sh
$ python3 compec1.py testes/v4_mult.ec1 -o prog.s
gerado: prog.s
```

### Como montar e executar

```sh
as --64 -o prog.o prog.s
ld -o prog prog.o
./prog        # imprime 42
```

### Opções auxiliares

- `--avaliar`: imprime apenas o valor inteiro da expressão (o interpretador),
  usado como oráculo de verificação nos testes.
  ```sh
  $ python3 compec1.py --avaliar testes/v11_grande.ec1
  2657
  ```
- `--otimizar`: aplica **propagação de constantes**. Como toda expressão EC1 é
  constante, o valor é calculado em tempo de compilação e o código gerado vira
  um único `mov $<resultado>, %rax`. O modo padrão (esquema de pilha) continua
  sendo o que demonstra a travessia da árvore.

### Erros

Caracteres fora do alfabeto geram `Erro lexico`; violações da gramática geram
`Erro sintatico`; divisão por zero gera `Erro de compilacao`. Em todos os
casos a mensagem vai para `stderr` e o programa termina com código diferente
de zero.

## Como rodar os testes

```sh
bash test.sh
```

São 13 casos válidos e 5 inválidos. Para cada caso válido, o script:

1. compila o `.ec1` para `.s` (léxico + sintático + geração de código);
2. compara o valor do interpretador do próprio compilador (`--avaliar`, o
   oráculo) com o golden output em `testes/esperado/`;
3. se houver um toolchain x86-64 funcional, monta, linka e executa o binário e
   compara sua saída com o oráculo (**verificação cruzada**: garante que o
   assembly gerado concorda com o interpretador).

Os casos inválidos devem ser rejeitados com código de saída diferente de zero.
Os casos cobrem constante simples, cada operador, aninhamento à direita e à
esquerda, ordem em subtração/divisão, resultado negativo, divisão truncada e
entradas inválidas (parêntese não fechado, operador ausente, caractere
inválido e divisão por zero).

Fora de um ambiente Linux x86-64 (por exemplo, em macOS), `as`/`ld` não geram
binários x86-64; o script detecta isso, pula a etapa de execução e ainda assim
verifica a geração do `.s` e o oráculo. Para a verificação cruzada completa,
use o Docker.

## Usando Docker

A imagem inclui `binutils` + `python3`, de modo que a suíte de testes roda por
inteiro (gera → monta → linka → executa) dentro do container.

```sh
docker build -t compec1 .
docker run --rm -v "$PWD":/app compec1                 # roda test.sh
```

Para compilar e executar uma expressão específica:

```sh
docker run --rm -v "$PWD":/app compec1 bash -c \
  "python3 compec1.py testes/v4_mult.ec1 -o prog.s && \
   as --64 -o prog.o prog.s && ld -o prog prog.o && ./prog"
```

> Em máquinas Apple Silicon (ARM), acrescente `--platform linux/amd64` aos
> comandos `docker build` e `docker run` para montar e executar x86-64 sob
> emulação.

## Arquivos do projeto

| Arquivo | Descrição |
| --- | --- |
| `compec1.py` | Compilador EC1: léxico, sintático, interpretador e gerador de código |
| `runtime.s` | Sub-rotinas `imprime_num` e `sair` (cópia idêntica da Atividade 03) |
| `test.sh` | Testes com verificação automática (gera → monta → linka → executa → compara) |
| `Dockerfile` | Ambiente em container com `binutils` + `python3` |
| `testes/*.ec1` | Entradas de teste (`v*` válidas, `e*` inválidas) |
| `testes/esperado/*.out` | Saídas esperadas (golden) dos casos válidos |
