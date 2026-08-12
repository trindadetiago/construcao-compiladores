# esperado: 121
# chamadas de funcao aninhadas como parametros reais de outra chamada
fun soma3(a, b, c) {
    return a + b + c;
}

fun media(a, b) {
    return (a + b) / 2;
}

main {
    return soma3(media(10, 20), soma3(1, 2, 3), 100);
}
