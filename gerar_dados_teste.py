"""
Script avulso, de uso único, para popular o banco com dados aleatórios
de teste: funcionários, produtos e máquinas — além de um rodízio de
exemplo já programado, pronto pra ir direto em "Resultado" e clicar em
"Gerar Rodízio".

Uso:
    python gerar_dados_teste.py

Depois de conferir que o fluxo funciona, pode apagar este arquivo e
os dados de teste (veja limpar_rodizio_teste.py para apagar o rodízio,
e as próprias telas de Funcionários/Produtos/Máquinas para apagar o
resto).
"""

from database.db import init_db
from database import repository
from models.entities import Funcionario, Produto, Maquina


def main():
    init_db()

    print("Cadastrando funcionários...")
    funcionarios = [
        ("Ana Silva", 1, "nenhuma"),
        ("Bruno Costa", 1, "nenhuma"),
        ("Carla Souza", 1, "gestante"),
        ("Diego Lima", 1, "nenhuma"),
        ("Elaine Rocha", 1, "fisica"),
        ("Fábio Alves", 2, "nenhuma"),
        ("Gabriela Dias", 2, "nenhuma"),
        ("Hugo Martins", 2, "temporaria"),
        ("Igor Pereira", 3, "nenhuma"),
        ("Julia Fernandes", 3, "nenhuma"),
    ]
    for nome, turno, restricao in funcionarios:
        repository.criar_funcionario(
            Funcionario(nome=nome, turno=turno, restricao=restricao)
        )
        print(f"  + {nome} (turno {turno}, restrição: {restricao})")

    print("\nCadastrando produtos...")
    produtos = [
        ("Peça A - Tampa", "facil"),
        ("Peça B - Suporte", "medio"),
        ("Peça C - Engrenagem", "dificil"),
        ("Peça D - Base", "medio"),
    ]
    produto_ids = {}
    for nome, dificuldade in produtos:
        pid = repository.criar_produto(Produto(nome=nome, dificuldade=dificuldade))
        produto_ids[nome] = pid
        print(f"  + {nome} (dificuldade: {dificuldade})")

    print("\nCadastrando máquinas...")
    maquinas = [
        ("Injetora 12", True),
        ("Injetora 24", True),
        ("Extrusora 3", False),
        ("Extrusora 7", False),
    ]
    maquina_ids = {}
    for nome, critica in maquinas:
        mid = repository.criar_maquina(Maquina(nome=nome, critica=critica))
        maquina_ids[nome] = mid
        print(f"  + {nome} (crítica: {critica})")

    print("\nCriando um rodízio de exemplo (Semana 1, Turno 1)...")
    rodizio_id = repository.criar_rodizio(semana=1, turno=1)
    programacao = [
        ("Injetora 12", "Peça C - Engrenagem", 1),
        ("Extrusora 3", "Peça A - Tampa", 2),
    ]
    for nome_maquina, nome_produto, qtd in programacao:
        repository.adicionar_rodizio_maquina(
            rodizio_id, maquina_ids[nome_maquina], produto_ids[nome_produto], qtd
        )
        print(f"  + {nome_maquina} / {nome_produto} / {qtd} operador(es)")

    print(
        f"\nPronto! Rodízio de exemplo criado: Semana 1, Turno 1 (id={rodizio_id}).\n"
        "Abra o app, vá em 'Resultado', selecione 'Semana 1 — Turno 1' e clique "
        "em 'Gerar Rodízio' para ver o resultado."
    )


if __name__ == "__main__":
    main()