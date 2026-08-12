# esperado: 131714583
# funcao com varias variaveis locais, exemplo da secao 6.1.4 do guia
fun f(x) {
    var y = x * x + 7;
    var z = y * x - 9;
    return y * z;
}

main {
    return f(42);
}
