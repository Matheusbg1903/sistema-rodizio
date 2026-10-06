"""
Script de demonstração — NÃO faz parte do app, é só para mostrar o
fluxo funcionando de ponta a ponta sem precisar abrir a interface
gráfica (útil aqui no ambiente de desenvolvimento, que não tem tela).

Simula exatamente o exemplo do briefing original:
  Máquina 20 -> 4 operadores -> Produto A
  Máquina 14 -> 2 operadores -> Produto B
  Máquina Ext. -> 3 operadores -> Produto C

Cada chamada abaixo é a mesma função que a tela CustomTkinter chama
quando você clica em "Salvar" nos formulários reais.
"""

import os

from database.db import init_db, DB_PATH
from database import repository
from models.entities import Funcionario, Produto, Maquina


def linha():
    print("-" * 60)


def main():
    # zera o banco pra essa demonstração ficar sempre igual
    if DB_PATH.exists():
        os.remove(DB_PATH)
    init_db()

    print("1) CADASTRANDO FUNCIONÁRIOS (tela Funcionários)")
    linha()
    nomes = [
        ("João Silva", 1, "nenhuma"),
        ("Maria Souza", 1, "gestante"),
        ("Carlos Lima", 1, "nenhuma"),
        ("Pedro Alves", 1, "fisica"),
        ("Ana Costa", 1, "nenhuma"),
        ("Bruno Rocha", 1, "nenhuma"),
        ("Fernanda Dias", 1, "nenhuma"),
        ("Rafael Nunes", 1, "nenhuma"),
        ("Juliana Melo", 1, "nenhuma"),
    ]
    for nome, turno, restricao in nomes:
        repository.criar_funcionario(Funcionario(nome=nome, turno=turno, restricao=restricao))
    for f in repository.listar_funcionarios():
        marca = f" [{f.restricao}]" if f.restricao != "nenhuma" else ""
        print(f"   + {f.nome} — Turno {f.turno}{marca}")
    print()

    print("2) CADASTRANDO PRODUTOS (tela Produtos)")
    linha()
    produtos = [("Produto A", "dificil"), ("Produto B", "facil"), ("Produto C", "medio")]
    for nome, dificuldade in produtos:
        repository.criar_produto(Produto(nome=nome, dificuldade=dificuldade))
    for p in repository.listar_produtos():
        print(f"   + {p.nome} — dificuldade: {p.dificuldade}")
    print()

    print("3) CADASTRANDO MÁQUINAS, incluindo uma composta (tela Máquinas)")
    linha()
    id_12 = repository.criar_maquina(Maquina(nome="12"))
    id_24 = repository.criar_maquina(Maquina(nome="24"))
    id_20 = repository.criar_maquina(Maquina(nome="20"))
    id_14 = repository.criar_maquina(Maquina(nome="14"))
    id_ext = repository.criar_maquina(Maquina(nome="Ext.", critica=True))
    id_composta = repository.criar_maquina(Maquina(nome="12-24"))
    repository.definir_componentes(id_composta, [id_12, id_24])

    todas_maquinas = repository.listar_maquinas()
    nomes_por_id = {m.id: m.nome for m in todas_maquinas}
    for m in todas_maquinas:
        tags = []
        if m.critica:
            tags.append("crítica")
        if m.componentes:
            nomes_componentes = ", ".join(nomes_por_id[cid] for cid in m.componentes)
            tags.append(f"composta de: {nomes_componentes}")
        sufixo = f"  [{' | '.join(tags)}]" if tags else ""
        print(f"   + Máquina {m.nome}{sufixo}")
    print()

    print("4) NOVA SEMANA — programação enviada pelo PCP (tela Nova Semana)")
    linha()
    produtos_cadastrados = {p.nome: p.id for p in repository.listar_produtos()}

    rodizio_id = repository.criar_rodizio(semana=32, turno=1)
    programacao = [
        (id_20, "Produto A", 4),
        (id_14, "Produto B", 2),
        (id_ext, "Produto C", 3),
    ]
    for maquina_id, produto_nome, qtd in programacao:
        repository.adicionar_rodizio_maquina(
            rodizio_id=rodizio_id,
            maquina_id=maquina_id,
            produto_id=produtos_cadastrados[produto_nome],
            qtd_operadores=qtd,
        )

    print(f"   Semana 32, Turno 1 salva (rodizio_id={rodizio_id}). Itens:")
    for item in repository.listar_rodizio_maquinas(rodizio_id):
        print(
            f"   - Máquina {item['maquina_nome']:<6} | {item['produto_nome']} "
            f"({item['dificuldade']}) | {item['qtd_operadores']} operador(es)"
        )
    print()

    print("5) O QUE AINDA FALTA (Etapa 6, próxima etapa)")
    linha()
    print("   A programação acima já está salva no banco, mas ninguém foi")
    print("   alocado ainda. O motor de geração vai pegar esses dados e decidir")
    print("   QUAIS funcionários vão para cada máquina, aplicando:")
    print("     - exclusão de Maria (gestante) e Pedro (restrição física) do Produto A (difícil)")
    print("     - prioridade para quem está há mais tempo sem usar aquela máquina")
    print("     - envio dos excedentes para o Kit")
    print()
    print(f"   Banco de dados desta demonstração: {DB_PATH}")


if __name__ == "__main__":
    main()
