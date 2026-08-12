# erro: semantico
fun ehpar(n) {
    var r = 0;
    if n == 0 {
        r = 1;
    } else {
        r = ehimpar(n - 1);
    }
    return r;
}
fun ehimpar(n) {
    var r = 0;
    if n == 0 {
        r = 0;
    } else {
        r = ehpar(n - 1);
    }
    return r;
}
main { return ehpar(10); }
