# esperado: 6
fun mdc(a, b) {
    var r = 0;
    if b == 0 {
        r = a;
    } else {
        r = mdc(b, a - (a / b) * b);
    }
    return r;
}

main {
    return mdc(54, 24);
}
