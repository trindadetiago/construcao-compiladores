# erro: sintatico
# return nao e comando, nao pode ficar dentro do if
x = 1;
{
    if x > 0 {
        return x;
    } else { }
    return 0;
}
