"""
Ponto de entrada da aplicação.

Garante que o banco existe e então abre a janela principal.
"""

from database.db import init_db
from ui.app import run


def main():
    init_db()
    run()


if __name__ == "__main__":
    main()
