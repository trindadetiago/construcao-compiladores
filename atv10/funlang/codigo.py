"""Geracao de codigo x86_64, sintaxe AT&T (GNU as).

Reaproveita o esquema de traducao de expressoes e comandos da linguagem
Cmd. A parte nova e' a convencao de chamada descrita na secao 6.1 do
guia: parametros empilhados em ordem inversa antes do CALL, RBP como
frame pointer do registro de ativacao, variaveis locais e parametros
acessados como deslocamento(%rbp), e resultado sempre devolvido em RAX.

O bloco principal do programa (main da linguagem Fun) continua sendo
compilado para o rotulo `main` do assembly, para ser montado direto pelo
gcc como um programa C normal (mesma escolha da atividade 9). Cada
funcao da linguagem Fun vira um rotulo `f_<nome>` no assembly, para não
colidir com simbolos de biblioteca.
"""

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

    def rotulo_funcao(self, nome):
        return "f_" + nome

    # programa

    def gera(self, prog):
        self.cabecalho()
        for d in prog.decls:
            if isinstance(d, ast.Decl):
                self.exp(d.exp, None)
                self.emite("movq %%rax, %s(%%rip)" % self.simbolo(d.nome))
        self.cmds(prog.cmds, None)
        self.exp(prog.resultado, None)
        self.rodape()
        for d in prog.decls:
            if isinstance(d, ast.FunDecl):
                self.gera_funcao(d)
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

    # funcoes definidas pelo usuario (secao 6.1 do guia)

    def gera_funcao(self, d):
        escopo = self.tab.escopo_de(d.nome)
        l = escopo.nlocais()
        self.rotulo(self.rotulo_funcao(d.nome))
        self.emite("pushq %rbp")
        if l > 0:
            self.emite("subq $%d, %%rsp" % (8 * l))
        self.emite("movq %rsp, %rbp")
        for vd in d.vardecls:
            self.exp(vd.exp, escopo)
            self.emite("movq %%rax, %d(%%rbp)" % escopo.offset(vd.nome))
        self.cmds(d.cmds, escopo)
        self.exp(d.resultado, escopo)
        if l > 0:
            self.emite("addq $%d, %%rsp" % (8 * l))
        self.emite("popq %rbp")
        self.emite("ret")

    # comandos

    def cmds(self, lista, escopo):
        for c in lista:
            self.cmd(c, escopo)

    def cmd(self, c, escopo):
        if isinstance(c, ast.Atrib):
            self.exp(c.exp, escopo)
            self.emite("movq %%rax, %s" % self.endereco(c.nome, escopo))
        elif isinstance(c, ast.Leia):
            self.emite("leaq %s, %%rsi" % self.endereco_lea(c.nome, escopo))
            self.emite("leaq .Lfmt_entrada(%rip), %rdi")
            self.emite("xorl %eax, %eax")
            self.emite("call scanf@PLT")
        elif isinstance(c, ast.Se):
            self.gera_se(c, escopo)
        elif isinstance(c, ast.Enquanto):
            self.gera_enquanto(c, escopo)
        else:
            raise TypeError("comando invalido: %r" % type(c).__name__)

    def gera_se(self, c, escopo):
        k = self.novo()
        falso, fim = "Lfalso%d" % k, "Lfim%d" % k
        self.exp(c.cond, escopo)
        self.emite("cmpq $0, %rax")
        self.emite("jz %s" % falso)
        self.cmds(c.entao, escopo)
        self.emite("jmp %s" % fim)
        self.rotulo(falso)
        self.cmds(c.senao, escopo)
        self.rotulo(fim)

    def gera_enquanto(self, c, escopo):
        k = self.novo()
        inicio, fim = "Linicio%d" % k, "Lfim%d" % k
        self.rotulo(inicio)
        self.exp(c.cond, escopo)
        self.emite("cmpq $0, %rax")
        self.emite("jz %s" % fim)
        self.cmds(c.corpo, escopo)
        self.emite("jmp %s" % inicio)
        self.rotulo(fim)

    # acesso a variaveis: local (RBP+deslocamento) ou global (RIP-relativo)

    def endereco(self, nome, escopo):
        if escopo is not None and escopo.existe(nome):
            return "%d(%%rbp)" % escopo.offset(nome)
        return "%s(%%rip)" % self.simbolo(nome)

    def endereco_lea(self, nome, escopo):
        # para LEA nao se usa %rip da mesma forma quando o operando ja'
        # e' um deslocamento de RBP (RBP+desloc ja' e' um endereco).
        if escopo is not None and escopo.existe(nome):
            return "%d(%%rbp)" % escopo.offset(nome)
        return "%s(%%rip)" % self.simbolo(nome)

    # expressoes, resultado sempre em RAX

    def exp(self, e, escopo):
        if isinstance(e, ast.Num):
            self.emite("movq $%d, %%rax" % e.valor)
        elif isinstance(e, ast.Var):
            self.emite("movq %s, %%rax" % self.endereco(e.nome, escopo))
        elif isinstance(e, ast.BinOp):
            self.bin(e, escopo)
        elif isinstance(e, ast.Logico):
            self.logico(e, escopo)
        elif isinstance(e, ast.Nao):
            self.exp(e.exp, escopo)
            self.emite("xorq %rcx, %rcx")
            self.emite("cmpq $0, %rax")
            self.emite("setz %cl")
            self.emite("movq %rcx, %rax")
        elif isinstance(e, ast.Chamada):
            self.chamada(e, escopo)
        else:
            raise TypeError("expressao invalida: %r" % type(e).__name__)

    def bin(self, e, escopo):
        # direito primeiro, empilha, depois esquerdo
        self.exp(e.dir, escopo)
        self.emite("pushq %rax")
        self.exp(e.esq, escopo)
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

    def logico(self, e, escopo):
        # curto circuito, resultado normalizado em 0 ou 1
        k = self.novo()
        curto, fim = "Lcurto%d" % k, "Lfimlog%d" % k
        salto = "jz" if e.op == "and" else "jnz"
        self.exp(e.esq, escopo)
        self.emite("cmpq $0, %rax")
        self.emite("%s %s" % (salto, curto))
        self.exp(e.dir, escopo)
        self.emite("cmpq $0, %rax")
        self.emite("%s %s" % (salto, curto))
        self.emite("movq $%d, %%rax" % (1 if e.op == "and" else 0))
        self.emite("jmp %s" % fim)
        self.rotulo(curto)
        self.emite("movq $%d, %%rax" % (0 if e.op == "and" else 1))
        self.rotulo(fim)

    def chamada(self, e, escopo):
        # empilha os parametros em ordem inversa (secao 6.1.1 do guia)
        for arg in reversed(e.args):
            self.exp(arg, escopo)
            self.emite("pushq %rax")
        self.emite("call %s" % self.rotulo_funcao(e.nome))
        if e.args:
            self.emite("addq $%d, %%rsp" % (8 * len(e.args)))


def gerar(prog, tabela):
    return Gerador(tabela).gera(prog)
