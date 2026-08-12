# esperado: 45
# soma dos inteiros de n ate m menos 1
n = 1;
m = 10;
soma = 0;
{
    while n < m {
        soma = soma + n;
        n = n + 1;
    }
    return soma;
}
