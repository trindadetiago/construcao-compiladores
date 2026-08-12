# esperado: 55
# entrada: 10
# le n da entrada e soma de 1 ate n
n = 0;
s = 0;
i = 1;
{
    read n;
    while i <= n {
        s = s + i;
        i = i + 1;
    }
    return s;
}
