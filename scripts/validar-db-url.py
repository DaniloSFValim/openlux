#!/usr/bin/env python3
"""Diagnostica a forma de SUPABASE_DB_URL sem nunca imprimir a senha.

A CLI do Supabase recusa uma URL malformada com apenas "failed to parse
connection string", sem dizer o que esta errado — e o valor vem mascarado como
*** no log do Actions, entao nem da para inspecionar a olho. Este script reporta
so fatos estruturais, o suficiente para identificar a causa.
"""
import os
import sys
from urllib.parse import urlsplit

PRECISA_ENCODAR = "#@/?:[] %"

def main() -> int:
    bruto = os.environ.get("SUPABASE_DB_URL")
    if bruto is None:
        print("SUPABASE_DB_URL nao esta definida.", file=sys.stderr)
        return 1

    problemas = []
    print("Diagnostico de SUPABASE_DB_URL (a senha nunca e impressa):")
    print(f"  comprimento total: {len(bruto)} caracteres")

    limpo = bruto.strip()
    if limpo != bruto:
        antes = len(bruto) - len(bruto.lstrip())
        depois = len(bruto) - len(bruto.rstrip())
        problemas.append(
            f"ha espaco em branco nas pontas ({antes} antes, {depois} depois) — "
            "provavelmente uma nova linha colada junto com o valor"
        )
    if "\n" in limpo or "\r" in limpo:
        problemas.append("ha nova linha no MEIO do valor, nao apenas nas pontas")

    if not limpo.startswith(("postgresql://", "postgres://")):
        inicio = limpo[:12].split(":")[0] if limpo else "(vazio)"
        problemas.append(
            f"nao comeca com postgresql:// nem postgres:// (comeca com '{inicio}...')"
        )

    if "[" in limpo or "]" in limpo:
        problemas.append(
            "contem [ ou ] — o placeholder [YOUR-PASSWORD] ficou, ou sobraram "
            "colchetes em volta da senha"
        )

    if "#" in limpo:
        problemas.append(
            "contem # — uma URL de Postgres nao usa fragmento, entao esse # "
            "esta na senha e precisa virar %23 (ele faz o parser cortar a URL "
            "ali, por isso o erro da CLI e generico)"
        )

    arrobas = limpo.count("@")
    if arrobas == 0:
        problemas.append("nao tem @ separando credencial de host")
    elif arrobas > 1:
        problemas.append(
            f"tem {arrobas} caracteres @ — o separador e um, entao os outros "
            f"{arrobas - 1} estao na senha e precisam virar %40"
        )

    # Parse apenas para relatar host/porta. O ref do projeto ja e publico no
    # repositorio, entao isto nao expoe nada novo.
    try:
        p = urlsplit(limpo)
        print(f"  esquema: {p.scheme or '(ausente)'}")
        print(f"  host: {p.hostname or '(nao identificado)'}")
        print(f"  porta: {p.port if p.port else '(ausente)'}")
        print(f"  usuario: {p.username or '(ausente)'}")
        print(f"  caminho: {p.path or '(ausente)'}")
        senha = p.password
        if senha is None:
            problemas.append("nenhuma senha foi identificada na URL")
        else:
            print(f"  senha: presente, {len(senha)} caracteres")
            suspeitos = sorted({c for c in senha if c in PRECISA_ENCODAR})
            if suspeitos:
                legiveis = ", ".join(
                    "espaco" if c == " " else c for c in suspeitos
                )
                problemas.append(
                    f"a senha contem caractere que precisa de percent-encoding: "
                    f"{legiveis}"
                )
        if p.port is None:
            problemas.append("falta a porta (:5432 para o session pooler)")
        if p.path in ("", "/"):
            problemas.append("falta o nome do banco no fim (/postgres)")
    except ValueError as e:
        problemas.append(f"urlsplit recusou o valor: {e}")

    print()
    if problemas:
        print("PROBLEMAS ENCONTRADOS:", file=sys.stderr)
        for i, p_ in enumerate(problemas, 1):
            print(f"  {i}. {p_}", file=sys.stderr)
        return 1

    print("Nenhum problema estrutural encontrado.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
