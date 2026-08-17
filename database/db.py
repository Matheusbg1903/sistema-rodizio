"""
Módulo de conexão e inicialização do banco de dados.

Responsabilidade única: abrir conexão com o SQLite e garantir que o
schema (tabelas) exista. Nenhuma regra de negócio entra aqui.
"""

import sqlite3
import sys
from pathlib import Path


def _resolver_pasta_base() -> Path:
    """
    Decide onde o rodizio.db deve morar.

    Rodando com `python main.py`: usa a raiz do projeto (duas pastas
    acima deste arquivo — database/db.py -> raiz).

    Rodando como .exe empacotado (PyInstaller, modo --onefile): o
    programa é extraído numa pasta TEMPORÁRIA a cada execução, que é
    apagada ao fechar. Se o banco fosse criado ali dentro, todo dado
    cadastrado sumiria ao fechar o programa. Por isso, nesse caso,
    salvamos ao lado do .exe (sys.executable), que é permanente.

    `sys.frozen` só existe quando o código foi empacotado pelo
    PyInstaller — é a forma padrão de detectar isso.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


# Banco fica na raiz do projeto (modo script) ou ao lado do .exe (modo empacotado)
DB_PATH = _resolver_pasta_base() / "rodizio.db"


def get_connection() -> sqlite3.Connection:
    """
    Abre e retorna uma conexão com o banco.

    PRAGMA foreign_keys = ON é obrigatório no SQLite: por padrão,
    integridade referencial (FK) vem desligada. Sem isso, seria possível
    cadastrar uma alocação apontando para um funcionário que não existe.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome (row["nome"])
    return conn


def init_db() -> None:
    """
    Cria todas as tabelas caso ainda não existam.

    Usa "CREATE TABLE IF NOT EXISTS" propositalmente: essa função pode
    ser chamada toda vez que o app abre, sem risco de apagar dados.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            turno INTEGER NOT NULL CHECK (turno IN (1, 2, 3)),
            restricao TEXT NOT NULL DEFAULT 'nenhuma'
                CHECK (restricao IN ('nenhuma', 'gestante', 'fisica', 'temporaria')),
            ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            dificuldade TEXT NOT NULL
                CHECK (dificuldade IN ('facil', 'medio', 'dificil'))
        );

        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            critica INTEGER NOT NULL DEFAULT 0 CHECK (critica IN (0, 1))
        );

        -- Resolve o caso de máquinas compostas (ex: "12-24").
        -- Cada linha diz: "a máquina composta X inclui a máquina componente Y".
        -- Uma máquina simples (sem componentes) simplesmente não tem linhas aqui.
        CREATE TABLE IF NOT EXISTS maquina_componentes (
            maquina_composta_id INTEGER NOT NULL REFERENCES maquinas(id),
            maquina_componente_id INTEGER NOT NULL REFERENCES maquinas(id),
            PRIMARY KEY (maquina_composta_id, maquina_componente_id)
        );

        -- Cabeçalho de cada geração de rodízio. Nunca é sobrescrito:
        -- toda vez que o usuário gera um rodízio, nasce um novo registro aqui.
        CREATE TABLE IF NOT EXISTS rodizios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semana INTEGER NOT NULL,
            turno INTEGER NOT NULL CHECK (turno IN (1, 2, 3)),
            data_geracao TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- A programação informada pelo PCP para aquela geração específica
        -- (máquina, produto, quantos operadores).
        CREATE TABLE IF NOT EXISTS rodizio_maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rodizio_id INTEGER NOT NULL REFERENCES rodizios(id),
            maquina_id INTEGER NOT NULL REFERENCES maquinas(id),
            produto_id INTEGER NOT NULL REFERENCES produtos(id),
            qtd_operadores INTEGER NOT NULL CHECK (qtd_operadores > 0)
        );

        -- Quem foi alocado para onde. destino='kit' representa o excedente.
        -- rodizio_maquina_id fica NULL quando destino é 'kit', porque
        -- nesse caso não há uma máquina/produto associado.
        --
        -- rodizio_id fica preenchido em TODAS as linhas (mesmo destino='kit').
        -- É redundante com rodizio_maquina_id quando destino='maquina' (dá pra
        -- chegar no rodízio via rodizio_maquinas), mas é a ÚNICA forma de saber
        -- de qual rodízio um funcionário do "kit" faz parte, já que nesse caso
        -- rodizio_maquina_id é NULL. Sem essa coluna, o excedente de rodízios
        -- diferentes ficaria misturado e impossível de separar na consulta.
        CREATE TABLE IF NOT EXISTS alocacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rodizio_id INTEGER NOT NULL REFERENCES rodizios(id),
            rodizio_maquina_id INTEGER REFERENCES rodizio_maquinas(id),
            funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id),
            destino TEXT NOT NULL CHECK (destino IN ('maquina', 'kit'))
        );
        """
    )

    conn.commit()

    # ------------------------------------------------------------------
    # Migração leve: bancos criados antes da coluna `rodizio_id` existir
    # em `alocacoes` não a ganham automaticamente com CREATE TABLE IF NOT
    # EXISTS (essa cláusula só cria a tabela se ela não existir — não
    # altera uma tabela já existente). Por isso checamos manualmente se a
    # coluna está lá e adicionamos com ALTER TABLE se não estiver.
    # Não é destrutivo: não apaga nem move dado nenhum.
    # ------------------------------------------------------------------
    colunas = [row["name"] for row in conn.execute("PRAGMA table_info(alocacoes)")]
    if "rodizio_id" not in colunas:
        conn.execute("ALTER TABLE alocacoes ADD COLUMN rodizio_id INTEGER REFERENCES rodizios(id)")
        conn.commit()

    conn.close()