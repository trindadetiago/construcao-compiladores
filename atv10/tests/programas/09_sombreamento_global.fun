# esperado: 1006
# parametro x deve esconder a variavel global x dentro da funcao abs
var x = 999;

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
    return abs(0 - 7) + x;
}
