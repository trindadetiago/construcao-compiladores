# esperado: 1
# operadores logicos (extensao and/or/not) usados dentro de uma funcao
fun entre(x, lo, hi) {
    var ok = 0;
    if x > lo and x < hi {
        ok = 1;
    } else {
        ok = 0;
    }
    return ok;
}

main {
    return entre(5, 1, 10);
}
