#!/usr/bin/env python3
"""Verificador da congruencia de Zeller.

Implementa a mesma formula do programa assembly (zeller.s) em Python, para
conferir os resultados produzidos pela versao em assembly.
"""

from __future__ import annotations

DIAS = [
    "sabado",
    "domingo",
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
]


def zeller(q: int, m: int, k: int, j: int) -> int:
    """Calcula h = (q + floor(13*(m+1)/5) + k + k/4 + j/4 - 2*j) mod 7."""
    return (q + (13 * (m + 1)) // 5 + k + k // 4 + j // 4 - 2 * j) % 7


def ajustar(dia: int, mes: int, ano: int) -> tuple[int, int, int, int]:
    """Converte (dia, mes, ano) do calendario para (q, m, k, j) da formula.

    Para janeiro e fevereiro, o ano e tratado como o ano anterior e o mes
    vira 13 ou 14.
    """
    if mes <= 2:
        mes += 12
        ano -= 1
    return dia, mes, ano % 100, ano // 100


def main() -> None:
    casos = [
        ("25/05/2026", 25, 5, 2026),
        ("01/01/2026", 1, 1, 2026),
        ("07/09/1822", 7, 9, 1822),
        ("21/04/1960", 21, 4, 1960),
        ("31/12/1999", 31, 12, 1999),
        ("29/02/2024", 29, 2, 2024),
    ]
    largura = max(len(rotulo) for rotulo, *_ in casos)
    for rotulo, d, mo, a in casos:
        q, m, k, j = ajustar(d, mo, a)
        h = zeller(q, m, k, j)
        print(
            f"{rotulo:<{largura}}  q={q:>2} m={m:>2} k={k:>2} j={j:>2}  "
            f"-> h={h} ({DIAS[h]})"
        )


if __name__ == "__main__":
    main()
