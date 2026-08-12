# esperado: 6765
# vigesimo termo da sequencia de fibonacci
n = 20;
a = 0;
b = 1;
i = 0;
t = 0;
{
    while i < n {
        t = a + b;
        a = b;
        b = t;
        i = i + 1;
    }
    return a;
}
