# Atividade 08 - Compilador da linguagem EV

Compilador completo para a linguagem EV (Expressoes com Variaveis), referente
a Atividade 08 da disciplina de Compiladores. Esta entrega parte do compilador
EC2 da Atividade 07 e adiciona declaracoes de variaveis, analise semantica com
tabela de simbolos e geracao de codigo com uma secao `.bss`.

## Equipe

| Nome | Curso | Matricula | E-mail |
| --- | --- | --- | --- |
| Tiago Trindade de Oliveira | Ciencia da Computacao/CI | 20220054982 | tto@academico.ufpb.br |
| Ralf Dewrich Ferreira | Engenharia da Computacao/CI | 20220060783 | ralf.ferreira@academico.ufpb.br |
| Yan Fabber Lima de Albuquerque | Ciencia da Computacao/CI | 20220070805 | yan.fabber@gmail.com |
| Daniel Victor Carneiro Brandao da Costa | Ciencia da Computacao/CI | 20230089678 | danielvictorcarneiro21@gmail.com |

## A linguagem EV

Um programa EV tem zero ou mais declaracoes de variaveis, seguidas de uma
expressao final iniciada por `=`:

```text
l = 30;
c = 40;
= l + l + c + c
```

A gramatica implementada e:

```text
<programa> ::= <decl>* <result>
<decl>     ::= <ident> '=' <exp> ';'
<ident>    ::= <letra><letra_digito>*
<result>   ::= '=' <exp>
<exp>      ::= <exp_m> (('+' | '-') <exp_m>)*
<exp_m>    ::= <prim> (('*' | '/') <prim>)*
<prim>     ::= <num> | <ident> | '(' <exp> ')'
<num>      ::= <digito><digito>*
```

Identificadores usam letras ASCII maiusculas/minusculas e digitos, mas devem
comecar por letra. Uma sequencia como `237axy` e rejeitada como erro lexico.

## Arquitetura

| Camada | Classe/funcao | Descricao |
| --- | --- | --- |
| Analise lexica | `Lexer` | Reconhece numeros, identificadores, `=`, `;`, parenteses e operadores |
| Analise sintatica | `Parser` | Produz a AST `Programa`, com declaracoes e expressao final |
| Analise semantica | `verificar_semantica` | Garante que variaveis so sejam usadas depois de declaradas |
| Interpretacao | `Programa.avaliar()` | Calcula o resultado inteiro, usado como oraculo dos testes |
| Geracao de codigo | `gerar_assembly()` | Emite assembly x86-64 com variaveis em `.bss` |

Na geracao de assembly, variaveis do programa fonte recebem prefixo interno
`ev_var_` para evitar colisao com rotulos do runtime. Por exemplo, a variavel
fonte `x` e armazenada no simbolo assembly `ev_var_x`.

## Como usar

Todos os comandos abaixo assumem que voce esta dentro da pasta `atv8/`.

```sh
python3 compev.py <arquivo.ev> [-o saida.s] [--otimizar]
```

Por padrao, o assembly e gravado em um arquivo com o mesmo nome da entrada e
extensao `.s`. Com `-o -`, o assembly e escrito na saida padrao sem linhas
extras.

```sh
$ python3 compev.py testes/v4_dependencias.ev -o prog.s
gerado: prog.s
```

Opcoes auxiliares:

- `--avaliar`: imprime apenas o valor inteiro do programa.
  ```sh
  $ python3 compev.py --avaliar testes/v3_perimetro.ev
  140
  ```
- `--otimizar`: calcula o resultado em tempo de compilacao e emite um unico
  `mov $<resultado>, %rax`.

## Montar e executar o assembly

Em Linux x86-64 com `as` e `ld` disponiveis:

```sh
as --64 -o prog.o prog.s
ld -o prog prog.o
./prog
```

## Erros

- `Erro lexico`: caractere fora do alfabeto ou identificador comecando por
  digito.
- `Erro sintatico`: violacao da gramatica EV.
- `Erro semantico`: uso de variavel que ainda nao foi declarada.
- `Erro de compilacao`: divisao por zero detectada em tempo de compilacao.

Todas as mensagens vao para `stderr` e o programa termina com codigo diferente
de zero.

## Como rodar os testes

```sh
bash test.sh
```

A suite contem casos validos com variaveis, precedencia, associatividade,
identificadores com digitos e zero declaracoes. Tambem contem casos invalidos
para variavel nao declarada, identificador invalido, erro sintatico, operador
unario e divisao por zero.

Para cada caso valido, o script gera assembly, compara `--avaliar` com o golden
output e, se houver toolchain x86-64 funcional, monta, linka e executa o
binario para comparar a saida real com o oraculo.

## Usando Docker

A imagem inclui `binutils` e `python3`, permitindo rodar a suite completa em um
ambiente Linux x86-64:

```sh
docker build -t compev .
docker run --rm -v "$PWD":/app compev
```

## Arquivos do projeto

| Arquivo | Descricao |
| --- | --- |
| `compev.py` | Compilador EV: lexico, sintatico, semantico, interpretador e gerador |
| `runtime.s` | Sub-rotinas `imprime_num` e `sair` |
| `test.sh` | Testes automaticos com oraculo e verificacao cruzada |
| `Dockerfile` | Ambiente em container com `binutils` e `python3` |
| `testes/*.ev` | Entradas de teste validas e invalidas |
| `testes/esperado/*.out` | Saidas esperadas dos casos validos |
