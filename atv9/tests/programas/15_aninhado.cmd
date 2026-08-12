# esperado: 75
# laco dentro de laco com condicional no meio
i = 1;
j = 1;
s = 0;
{
    while i <= 5 {
        j = 1;
        while j <= 5 {
            if i == j {
                s = s + i * j;
            } else {
                s = s + 1;
            }
            j = j + 1;
        }
        i = i + 1;
    }
    return s;
}
