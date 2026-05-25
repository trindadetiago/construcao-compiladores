# Atividade 03 - Congruencia de Zeller

Programa em assembly x86-64 que calcula o dia da semana de uma data usando
a congruencia de Zeller, mais um verificador em Python e as respostas das
perguntas teoricas da Parte 2.

## Equipe

| Nome | Curso | Matricula | E-mail |
| --- | --- | --- | --- |
| Tiago Trindade de Oliveira | Ciencia da Computacao/CI | 20220054982 | tto@academico.ufpb.br |
| Ralf Dewrich Ferreira | Engenharia da Computacao/CI | 20220060783 | ralf.ferreira@academico.ufpb.br |
| Yan Fabber Lima de Albuquerque | Ciencia da Computacao/CI | 20220070805 | yan.fabber@gmail.com |
| Daniel Victor Carneiro Brandao da Costa | Ciencia da Computacao/CI | 20230089678 | danielvictorcarneiro21@gmail.com |

## Formula

    h = (q + (13*(m+1))/5 + k + k/4 + j/4 - 2*j) mod 7

- `q` = dia do mes
- `m` = mes ajustado (3=marco ... 12=dezembro, 13=janeiro, 14=fevereiro do ano seguinte)
- `k` = ano dentro do seculo (para janeiro/fevereiro, usar o ano anterior)
- `j` = parte do seculo
- `h` = dia da semana: 0=sabado, 1=domingo, 2=segunda, ..., 6=sexta

## Convencao de registradores (definida no enunciado)

| Registrador | Significado |
| --- | --- |
| R8  | q |
| R9  | m |
| R10 | k |
| R11 | j |

O resultado final fica em RAX e e impresso por `imprime_num` (mesmo runtime
da Atividade 02).

## Como rodar

Os comandos abaixo assumem que voce esta dentro da pasta `atv3/`.

### Linux x86-64 (binutils nativo)

```sh
bash test.sh
```

ou manualmente:

```sh
as --64 -o zeller.o zeller.s
ld -o zeller zeller.o
./zeller
```

### Outros sistemas (Docker)

Em maquinas ARM (Apple Silicon, etc.) inclua `--platform linux/amd64`:

```sh
docker build --platform linux/amd64 -t zeller .
docker run --rm --platform linux/amd64 -v "$PWD":/app zeller
```

### Verificador em Python

```sh
python3 zeller.py
```

O verificador imprime o resultado de varios casos de teste (incluindo o
default do `zeller.s`, 25/05/2026 = segunda-feira = 2).

## Arquivos

| Arquivo | Descricao |
| --- | --- |
| `zeller.s` | Programa assembly que calcula a congruencia (Parte 1). |
| `runtime.s` | Rotinas `imprime_num` e `sair` (mesmo arquivo da atv2). |
| `zeller.py` | Verificador em Python (linguagem de alto nivel) que confere os resultados. |
| `respostas_parte2.txt` | Respostas das 3 perguntas da Parte 2. |
| `test.sh` | Monta, linka, executa e compara com o valor esperado. |
| `Dockerfile` | Ambiente Debian + binutils para quem nao esta em Linux x86-64. |

## Como testar uma data diferente

Edite os quatro `mov` no inicio de `_start` em `zeller.s` para refletir os
valores de q, m, k, j da data desejada (lembrando do ajuste para janeiro e
fevereiro). Depois rode `bash test.sh` ou os comandos do `as`/`ld`/run
manualmente.
