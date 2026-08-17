"""
Script avulso, de uso único, para apagar um rodízio de teste (e tudo que
depende dele: alocações e a programação de máquinas/produtos) — para
liberar máquinas/produtos que estão travados por FOREIGN KEY.

Uso:
    python limpar_rodizio_teste.py

Depois de usar, pode apagar este arquivo — ele não faz parte do app.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "rodizio.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rodizios = conn.execute(
        "SELECT id, semana, turno, data_geracao FROM rodizios ORDER BY id"
    ).fetchall()

    if not rodizios:
        print("Nenhum rodízio salvo no banco.")
        return

    print("Rodízios salvos:")
    for r in rodizios:
        n_maquinas = conn.execute(
            "SELECT COUNT(*) FROM rodizio_maquinas WHERE rodizio_id = ?", (r["id"],)
        ).fetchone()[0]
        n_alocacoes = conn.execute(
            "SELECT COUNT(*) FROM alocacoes WHERE rodizio_id = ?", (r["id"],)
        ).fetchone()[0]
        print(
            f"  id={r['id']}  |  Semana {r['semana']} - Turno {r['turno']}  |  "
            f"{n_maquinas} máquina(s) programada(s)  |  {n_alocacoes} alocação(ões)"
        )

    escolha = input("\nDigite o id do rodízio que deseja APAGAR (ou ENTER para cancelar): ").strip()
    if not escolha:
        print("Cancelado.")
        return

    rodizio_id = int(escolha)

    confirmar = input(
        f"Isso vai apagar PERMANENTEMENTE o rodízio id={rodizio_id}, sua programação "
        f"de máquinas e as alocações geradas. Digite SIM para confirmar: "
    ).strip()
    if confirmar != "SIM":
        print("Cancelado.")
        return

    conn.execute("DELETE FROM alocacoes WHERE rodizio_id = ?", (rodizio_id,))
    conn.execute("DELETE FROM rodizio_maquinas WHERE rodizio_id = ?", (rodizio_id,))
    conn.execute("DELETE FROM rodizios WHERE id = ?", (rodizio_id,))
    conn.commit()
    conn.close()

    print(
        f"\nRodízio id={rodizio_id} apagado. "
        "Agora vá em 'Máquinas' e 'Produtos' no app e exclua normalmente — "
        "eles não devem mais estar bloqueados."
    )


if __name__ == "__main__":
    main()