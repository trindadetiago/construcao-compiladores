# esperado: 42
# exemplo do guia (secao 2): valor absoluto via funcao com if/else
fun abs(x) {
    var y = 0;
    if x < 0 {
        y = 0 - x;
    } else {
        y = x;
    }
    return y;
}

main {
    return abs(0 - 42);
}
