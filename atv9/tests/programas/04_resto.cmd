# esperado: 2
# resto da divisao por subtracao sucessiva
m = 10;
n = 4;
{
    while m + 1 > n {
        m = m - n;
    }
    return m;
}
