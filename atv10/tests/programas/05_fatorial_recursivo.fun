# esperado: 3628800
fun fatorial(n) {
    var r = 0;
    if n < 2 {
        r = 1;
    } else {
        r = n * fatorial(n - 1);
    }
    return r;
}

main {
    return fatorial(10);
}
