# esperado: 3628800
# fatorial de n por repeticao
n = 10;
r = 1;
i = 1;
{
    while i <= n {
        r = r * i;
        i = i + 1;
    }
    return r;
}
