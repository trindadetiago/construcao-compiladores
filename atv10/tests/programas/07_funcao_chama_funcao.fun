# esperado: 1612
# uma funcao chama outra (nao recursiva), e o resultado alimenta variaveis globais
var g = 100;

fun dobro(x) {
    return x * 2;
}

fun quadruplo(x) {
    return dobro(dobro(x));
}

main {
    g = quadruplo(g);
    return quadruplo(g) + quadruplo(3);
}
