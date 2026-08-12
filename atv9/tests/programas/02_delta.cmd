# esperado: 8
# valor absoluto do discriminante de uma equacao de segundo grau
a = 1;
b = 2;
c = 3;
delta = b * b - 4 * a * c;
{
    if delta < 0 {
        delta = 0 - delta;
    } else {
        delta = delta;
    }
    return delta;
}
