# esperado: 10
# conta quantos primos existem abaixo de 30
n = 2;
total = 0;
d = 0;
primo = 0;
{
    while n < 30 {
        primo = 1;
        d = 2;
        while d * d <= n {
            if n / d * d == n {
                primo = 0;
            }
            d = d + 1;
        }
        if primo {
            total = total + 1;
        }
        n = n + 1;
    }
    return total;
}
