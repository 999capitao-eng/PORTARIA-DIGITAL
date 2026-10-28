"""Gera visitantes e visitas FICTÍCIOS para demonstração.

Uso:
    python dados_ficticios.py
    python dados_ficticios.py --visitantes 15 --dias 10 --semente 7

Os CPFs são gerados com dígitos verificadores válidos e podem coincidir
com CPFs reais por acaso. Use apenas no laboratório.
"""

import argparse
import random
from datetime import datetime, timedelta

from portaria import servicos
from portaria.db import conectar, preparar_banco
from portaria.erros import RegraNegocioError

PRIMEIROS = ["Ana", "Bruno", "Carla", "Davi", "Elisa", "Fábio", "Gabi", "Hugo",
             "Iara", "João", "Luana", "Marcos", "Nina", "Otávio", "Paula"]
SOBRENOMES = ["Lima", "Sousa", "Nunes", "Rocha", "Prado", "Melo", "Torres",
              "Alves", "Campos", "Reis"]

def gerar_cpf(rng):
    digitos = [rng.randint(0, 9) for _ in range(9)]
    for posicao in (9, 10):
        soma = sum(digitos[i] * (posicao + 1 - i) for i in range(posicao))
        digitos.append((soma * 10) % 11 % 10)
    return "".join(map(str, digitos))

def formatar(momento):
    return momento.isoformat(sep=" ", timespec="seconds")

def popular(conn, visitantes=10, dias=5, semente=None):
    rng = random.Random(semente)

    cpfs = []
    for _ in range(visitantes):
        nome = f"{rng.choice(PRIMEIROS)} {rng.choice(SOBRENOMES)}"
        cpf = gerar_cpf(rng)
        try:
            servicos.cadastrar_visitante(conn, nome, cpf)
        except RegraNegocioError:
            pass  # CPF repetido: o cadastro já existe
        cpfs.append(cpf)

    setores = [s["id"] for s in conn.execute("SELECT id FROM setor WHERE ativo = 1")]
    hoje = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    criadas = 0
    for dia in range(dias, 0, -1):
        for cpf in rng.sample(cpfs, min(4, len(cpfs))):
            entrada = hoje - timedelta(days=dia) + timedelta(minutes=rng.randint(0, 480))
            saida = entrada + timedelta(minutes=rng.randint(10, 120))
            try:
                visita_id = servicos.registrar_entrada(
                    conn, cpf, rng.choice(setores), momento=formatar(entrada)
                )
                servicos.registrar_saida(conn, visita_id, momento=formatar(saida))
                criadas += 1
            except RegraNegocioError:
                pass  # lotação ou visitante já presente: a regra vale para os dados também
    return criadas

def main():
    parser = argparse.ArgumentParser(description="Gera dados fictícios da Portaria Digital.")
    parser.add_argument("--visitantes", type=int, default=10)
    parser.add_argument("--dias", type=int, default=5)
    parser.add_argument("--semente", type=int, default=None,
                        help="mesma semente gera os mesmos dados")
    args = parser.parse_args()

    conn = conectar()
    preparar_banco(conn)
    criadas = popular(conn, args.visitantes, args.dias, args.semente)
    conn.close()
    print(f"{criadas} visita(s) fictícia(s) gravada(s) em portaria.db")

if __name__ == "__main__":
    main()