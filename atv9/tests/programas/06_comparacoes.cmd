# esperado: 47
# cada comparacao verdadeira soma um bit distinto
a = 3;
b = 5;
r = 0;
{
    if a < b { r = r + 1; } else { }
    if b > a { r = r + 2; } else { }
    if a == 3 { r = r + 4; } else { }
    if a <= 3 { r = r + 8; } else { }
    if b >= 6 { r = r + 16; } else { }
    if a != b { r = r + 32; } else { }
    return r;
}
