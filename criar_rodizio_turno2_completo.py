"""
Script avulso, de uso único: cria um rodízio novo para o turno 2 já com
a programação completa das 26 máquinas confirmadas (a mesma lista que
foi validada em conversa: máquina, produto e quantidade de operadores).

Não mexe em funcionários, máquinas nem produtos já cadastrados — só
cria o cabeçalho do rodízio (semana/turno) e a programação.

Uso:
    python criar_rodizio_turno2_completo.py
"""

from database.db import init_db
from database import repository
from models.entities import Produto


# máquina, produto, quantidade de operadores — lista confirmada
PROGRAMACAO_TURNO_2 = [
    ("1", "COPO 025", 2),
    ("2", "TAMPA MINI FORMA", 1),
    ("3/6", "FORMA GDE/TAMPA", 1),
    ("4", "PAZINHA", 1),
    ("7", "7", 2),
    ("9", "TAÇA 090", 1),
    ("11", "MEXEDOR CAFÉ GDE", 1),
    ("12", "COPO 040", 2),
    ("13", "TAÇA 180", 1),
    ("14", "TAMPA POTE 220", 1),
    ("16", "COLHER PIC 100", 1),
    ("17", "17", 1),
    ("18/30", "FORMAS A GRANEL", 1),
    ("19", "PRATO MASTER 015", 1),
    ("20", "POTE QUAD. 220", 2),
    ("21", "COLHER REF.", 3),
    ("22", "MEXEDOR CAFÉ", 2),
    ("24", "TAMPA FORMA GDE", 1),
    ("25", "TAMPA FORMA PQ", 1),
    ("26", "MINI FORMA", 1),
    ("32", "COLHER PICCOLO", 3),
    ("33", "GARFO SOBREMESA", 3),
    ("34", "GARFO MASTER", 2),
    ("EXTRUSORA", "EXTRUSORA", 3),
    ("TILT", "TILT", 9),
    ("MTF", "MTF", 6),
]


def garantir_produto_mtf():
    """Cria o produto MTF (dificuldade difícil) se ele ainda não existir."""
    for p in repository.listar_produtos():
        if p.nome.strip().upper() == "MTF":
            return
    repository.criar_produto(Produto(nome="MTF", dificuldade="dificil"))
    print("  + Produto 'MTF' criado (dificuldade: difícil)")


def main():
    init_db()

    semana = input("Número da semana (ex: 1): ").strip()
    if not semana.isdigit():
        print("Número de semana inválido. Cancelado.")
        return
    semana = int(semana)
    turno = 2

    # evita criar um rodízio duplicado sem querer, caso rode o script 2x
    ja_existe = any(
        r["semana"] == semana and r["turno"] == turno
        for r in repository.listar_rodizios()
    )
    if ja_existe:
        confirmar = input(
            f"Já existe um rodízio para Semana {semana} / Turno {turno}. "
            "Criar outro mesmo assim? (s/n): "
        ).strip().lower()
        if confirmar != "s":
            print("Cancelado.")
            return

    garantir_produto_mtf()

    rodizio_id = repository.criar_rodizio(semana=semana, turno=turno)
    print(f"\nRodízio criado: id={rodizio_id}, Semana {semana}, Turno {turno}\n")

    todas_maquinas = {m.nome: m.id for m in repository.listar_maquinas()}
    todos_produtos = {p.nome: p.id for p in repository.listar_produtos()}

    adicionadas = 0
    for nome_maquina, nome_produto, qtd in PROGRAMACAO_TURNO_2:
        if nome_maquina not in todas_maquinas:
            print(f"  ! ERRO: máquina '{nome_maquina}' não cadastrada. Pulando.")
            continue
        if nome_produto not in todos_produtos:
            print(f"  ! ERRO: produto '{nome_produto}' não cadastrado. Pulando.")
            continue

        repository.adicionar_rodizio_maquina(
            rodizio_id, todas_maquinas[nome_maquina], todos_produtos[nome_produto], qtd
        )
        print(f"  + {nome_maquina} / {nome_produto} / {qtd} operador(es)")
        adicionadas += 1

    total_vagas = sum(qtd for _, _, qtd in PROGRAMACAO_TURNO_2)
    print(
        f"\nPronto! {adicionadas}/{len(PROGRAMACAO_TURNO_2)} máquinas adicionadas ao rodízio id={rodizio_id}.\n"
        f"Total de vagas de operador: {total_vagas}.\n"
        "Agora é só abrir o app, ir em 'Resultado', selecionar este rodízio e clicar em 'Gerar Rodízio'."
    )


if __name__ == "__main__":
    main()