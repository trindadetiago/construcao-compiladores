# esperado: 3628800
# mesma funcao, mas com while (sem recursao) para comparar
fun fatorial(n) {
    var r = 1;
    var i = 1;
    while i < n + 1 {
        r = r * i;
        i = i + 1;
    }
    return r;
}

main {
    return fatorial(10);
}
