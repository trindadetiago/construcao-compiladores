  #
  # Atividade 03 - Congruencia de Zeller em x86-64 (GAS, Linux)
  #
  # Formula:
  #   h = (q + (13*(m+1))/5 + k + k/4 + j/4 - 2*j) mod 7
  #
  # Convencao de entrada (definida no enunciado):
  #   R8  = q (dia do mes)
  #   R9  = m (mes ajustado: 3=marco ... 12=dezembro, 13=janeiro, 14=fevereiro)
  #   R10 = k (ano dentro do seculo)
  #   R11 = j (parte do seculo)
  #
  # Saida:
  #   RAX = h, com 0=sabado, 1=domingo, 2=segunda, ..., 6=sexta
  #
  # Registradores usados internamente:
  #   RAX, RDX = dividendo/resto da IDIV
  #   RBX      = divisor
  #   RCX      = acumulador da soma dentro dos parenteses
  #

  .section .text
  .globl _start

_start:
  # Teste padrao: 25/05/2026 (segunda-feira)
  # q=25, m=5, k=26, j=20 -> h esperado = 2 (segunda)
  mov $25, %r8
  mov $5,  %r9
  mov $26, %r10
  mov $20, %r11

  xor %rcx, %rcx          # rcx = 0 (acumulador)

  # rcx += q
  add %r8, %rcx

  # rcx += (13 * (m+1)) / 5
  mov %r9, %rax
  inc %rax                # rax = m + 1
  imul $13, %rax          # rax = 13 * (m+1)
  cqo                     # estende sinal para rdx:rax
  mov $5, %rbx
  idiv %rbx               # rax = (13*(m+1)) / 5
  add %rax, %rcx

  # rcx += k
  add %r10, %rcx

  # rcx += k / 4
  mov %r10, %rax
  cqo
  mov $4, %rbx
  idiv %rbx
  add %rax, %rcx

  # rcx += j / 4
  mov %r11, %rax
  cqo
  mov $4, %rbx
  idiv %rbx
  add %rax, %rcx

  # rcx -= 2*j
  mov %r11, %rax
  shl $1, %rax            # rax = 2*j
  sub %rax, %rcx

  # h = rcx mod 7, sempre em [0,6].
  # Como rcx pode ser pequeno/negativo, somamos 700 (multiplo de 7) antes
  # do IDIV para garantir dividendo positivo sem alterar o resto.
  add $700, %rcx
  mov %rcx, %rax
  cqo
  mov $7, %rbx
  idiv %rbx
  mov %rdx, %rax          # rax = resto = h

  call imprime_num
  call sair

  .include "runtime.s"
