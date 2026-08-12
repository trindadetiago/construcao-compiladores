"""Geracao de codigo x86_64, sintaxe AT&T (GNU as)."""

from . import ast

SET_COMP = {
    "==": "setz",
    "!=": "setnz",
    "<": "setl",
    ">": "setg",
    "<=": "setle",
    ">=": "setge",
}


class Gerador:
    def __init__(self, tabela):
        self.tab = tabela
        self.linhas = []
        self.n = 0  # contador de rotulos

    # utilitarios

    def emite(self, s):
        self.linhas.append("    " + s)

    def rotulo(self, s):
        self.linhas.append(s + ":")

    def novo(self):
        self.n += 1
        return self.n - 1

    def simbolo(self, nome):
        return "v_" + nome

    # programa

    def gera(self, prog):
        self.cabecalho()
        for d in prog.decls:
            self.exp(d.exp)
            self.emite("movq %%rax, %s(%%rip)" % self.simbolo(d.nome))
        self.cmds(prog.cmds)
        self.exp(prog.resultado)
        self.rodape()
        return "\n".join(self.linhas) + "\n"

    def cabecalho(self):
        self.linhas.append("    .section .rodata")
        self.rotulo(".Lfmt_saida")
        self.emite('.string "%ld\\n"')
        self.rotulo(".Lfmt_entrada")
        self.emite('.string "%ld"')
        self.linhas.append("    .bss")
        for nome in self.tab:
            self.emite(".align 8")
            self.rotulo(self.simbolo(nome))
            self.emite(".zero 8")
        self.linhas.append("    .text")
        self.emite(".globl main")
        self.rotulo("main")
        self.emite("pushq %rbp")
        self.emite("movq %rsp, %rbp")

    def rodape(self):
        # resultado em RAX vai para printf
        self.emite("movq %rax, %rsi")
        self.emite("leaq .Lfmt_saida(%rip), %rdi")
        self.emite("xorl %eax, %eax")
        self.emite("call printf@PLT")
        self.emite("movq $0, %rax")
        self.emite("popq %rbp")
        self.emite("ret")

    # comandos

    def cmds(self, lista):
        for c in lista:
            self.cmd(c)

    def cmd(self, c):
        if isinstance(c, ast.Atrib):
            self.exp(c.exp)
            self.emite("movq %%rax, %s(%%rip)" % self.simbolo(c.nome))
        elif isinstance(c, ast.Leia):
            self.emite("leaq %s(%%rip), %%rsi" % self.simbolo(c.nome))
            self.emite("leaq .Lfmt_entrada(%rip), %rdi")
            self.emite("xorl %eax, %eax")
            self.emite("call scanf@PLT")
        elif isinstance(c, ast.Se):
            self.gera_se(c)
        elif isinstance(c, ast.Enquanto):
            self.gera_enquanto(c)
        else:
            raise TypeError("comando invalido: %r" % type(c).__name__)

    def gera_se(self, c):
        k = self.novo()
        falso, fim = "Lfalso%d" % k, "Lfim%d" % k
        self.exp(c.cond)
        self.emite("cmpq $0, %rax")
        self.emite("jz %s" % falso)
        self.cmds(c.entao)
        self.emite("jmp %s" % fim)
        self.rotulo(falso)
        self.cmds(c.senao)
        self.rotulo(fim)

    def gera_enquanto(self, c):
        k = self.novo()
        inicio, fim = "Linicio%d" % k, "Lfim%d" % k
        self.rotulo(inicio)
        self.exp(c.cond)
        self.emite("cmpq $0, %rax")
        self.emite("jz %s" % fim)
        self.cmds(c.corpo)
        self.emite("jmp %s" % inicio)
        self.rotulo(fim)

    # expressoes, resultado sempre em RAX

    def exp(self, e):
        if isinstance(e, ast.Num):
            self.emite("movq $%d, %%rax" % e.valor)
        elif isinstance(e, ast.Var):
            self.emite("movq %s(%%rip), %%rax" % self.simbolo(e.nome))
        elif isinstance(e, ast.BinOp):
            self.bin(e)
        elif isinstance(e, ast.Logico):
            self.logico(e)
        elif isinstance(e, ast.Nao):
            self.exp(e.exp)
            self.emite("xorq %rcx, %rcx")
            self.emite("cmpq $0, %rax")
            self.emite("setz %cl")
            self.emite("movq %rcx, %rax")
        else:
            raise TypeError("expressao invalida: %r" % type(e).__name__)

    def bin(self, e):
        # direito primeiro, empilha, depois esquerdo
        self.exp(e.dir)
        self.emite("pushq %rax")
        self.exp(e.esq)
        self.emite("popq %rbx")
        op = e.op
        if op == "+":
            self.emite("addq %rbx, %rax")
        elif op == "-":
            self.emite("subq %rbx, %rax")
        elif op == "*":
            self.emite("imulq %rbx, %rax")
        elif op == "/":
            self.emite("cqto")
            self.emite("idivq %rbx")
        elif op in SET_COMP:
            self.emite("xorq %rcx, %rcx")
            self.emite("cmpq %rbx, %rax")
            self.emite("%s %%cl" % SET_COMP[op])
            self.emite("movq %rcx, %rax")
        else:
            raise TypeError("operador invalido: %r" % op)

    def logico(self, e):
        # curto circuito, resultado normalizado em 0 ou 1
        k = self.novo()
        curto, fim = "Lcurto%d" % k, "Lfimlog%d" % k
        salto = "jz" if e.op == "and" else "jnz"
        self.exp(e.esq)
        self.emite("cmpq $0, %rax")
        self.emite("%s %s" % (salto, curto))
        self.exp(e.dir)
        self.emite("cmpq $0, %rax")
        self.emite("%s %s" % (salto, curto))
        self.emite("movq $%d, %%rax" % (1 if e.op == "and" else 0))
        self.emite("jmp %s" % fim)
        self.rotulo(curto)
        self.emite("movq $%d, %%rax" % (0 if e.op == "and" else 1))
        self.rotulo(fim)


def gerar(prog, tabela):
    return Gerador(tabela).gera(prog)
