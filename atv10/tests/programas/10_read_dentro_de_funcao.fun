# esperado: 105
# entrada: 100
# comando read (extensao) usado dentro do corpo de uma funcao
fun dobro_mais_lido(x) {
    var y = 0;
    read y;
    return x + y;
}

main {
    return dobro_mais_lido(5);
}
