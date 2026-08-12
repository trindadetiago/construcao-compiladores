# esperado: 7
# operadores booleanos com curto circuito
a = 1;
b = 0;
r = 0;
{
    if a and not b { r = r + 1; } else { }
    if b or a { r = r + 2; } else { }
    if not (a and b) { r = r + 4; } else { }
    if a and b { r = r + 8; } else { }
    return r;
}
