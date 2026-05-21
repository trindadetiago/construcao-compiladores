# Compilador CI

Compilador para a linguagem CI (Constantes Inteiras), referente a Atividade 02 da
disciplina de Compiladores.

## Equipe

| Nome | Curso | Matricula | E-mail |
| --- | --- | --- | --- |
| Tiago Trindade de Oliveira | Ciencia da Computacao/CI | 20220054982 | tto@academico.ufpb.br |
| Ralf Dewrich Ferreira | Engenharia da Computacao/CI | 20220060783 | ralf.ferreira@academico.ufpb.br |
| Yan Fabber Lima de Albuquerque | Ciencia da Computacao/CI | 20220070805 | yan.fabber@gmail.com |
| Daniel Victor Carneiro Brandao da Costa | Ciencia da Computacao/CI | 20230089678 | danielvictorcarneiro21@gmail.com |

A linguagem CI aceita programas que contem apenas uma constante inteira (um ou
mais digitos). O compilador gera um arquivo assembly x86-64 (sintaxe GNU
Assembler, Linux) que, depois de montado e linkado, imprime essa constante.

> Todos os comandos abaixo assumem que voce esta dentro da pasta `atv2/`.

## Requisitos

- Python 3.8+
- Para montar/linkar/executar o assembly gerado: `as` e `ld` do binutils
  (Linux x86-64). Quem estiver em outro sistema pode usar o Dockerfile incluido.

## Como compilar um programa CI

```sh
python3 compci.py p1.ci
```

Isso gera `p1.s` no mesmo diretorio. Para produzir o executavel e rodar:

```sh
as --64 -o p1.o p1.s
ld -o p1 p1.o
./p1
```

A saida deve ser a constante que estava em `p1.ci`.

## Como rodar os testes

```sh
bash test.sh
```

O script testa um programa valido (`p1.ci` com `42`) e um invalido (`erro.ci`
com `12abc`).

## Usando Docker

Para quem nao esta em Linux x86-64, o Dockerfile fornece um ambiente pronto.
Em maquinas ARM (Apple Silicon, etc.) inclua `--platform linux/amd64`:

```sh
docker build --platform linux/amd64 -t compci .
docker run --rm --platform linux/amd64 -v "$PWD":/app compci p1.ci
```

Para montar, linkar e executar dentro do container em um unico comando:

```sh
docker run --rm --platform linux/amd64 -v "$PWD":/app --entrypoint bash compci \
  -c "as --64 -o p1.o p1.s && ld -o p1 p1.o && ./p1"
```

## Arquivos do projeto

| Arquivo | Descricao |
| --- | --- |
| `compci.py` | Codigo-fonte do compilador. |
| `runtime.s` | Rotinas de apoio (`imprime_num`, `sair`) fornecidas pelo professor. |
| `p1.ci` | Teste valido contendo `42`. |
| `erro.ci` | Teste invalido contendo `12abc`. |
| `test.sh` | Script de testes. |
| `Dockerfile` | Ambiente em container com Python + binutils. |
