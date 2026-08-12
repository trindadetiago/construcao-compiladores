# esperado: 10946
# funcao diretamente recursiva, exemplo da secao 5.1 do guia
fun fib(n) {
    var res = 0;
    if n < 2 {
        res = 1;
    } else {
        res = fib(n - 1) + fib(n - 2);
    }
    return res;
}

main {
    return fib(20);
}
