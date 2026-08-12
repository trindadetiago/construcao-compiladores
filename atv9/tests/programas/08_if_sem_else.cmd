# esperado: 30
# condicional sem o braco else
x = 10;
{
    if x > 5 {
        x = x + 20;
    }
    if x > 100 {
        x = 0;
    }
    return x;
}
