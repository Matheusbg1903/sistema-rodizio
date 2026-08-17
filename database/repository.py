"""
Repository — camada de acesso a dados.

Responsabilidade única: converter entre as tabelas do SQLite e as
dataclasses de `models/entities.py`. Nenhuma outra parte do sistema
deve escrever SQL diretamente — sempre passar por aqui.

Toda função que escreve no banco (criar/atualizar/excluir) segue o
padrão:

    conn = get_connection()
    try:
        ...
        conn.commit()
    finally:
        conn.close()

Isso garante que a conexão seja fechada mesmo quando o SQLite recusa
a operação (ex: violação de FOREIGN KEY ao tentar excluir algo que
tem histórico vinculado). Sem o `finally`, uma exceção no meio da
operação deixa a conexão aberta e trava o banco para as chamadas
seguintes ("database is locked").
"""

from typing import List, Optional

from database.db import get_connection
from models.entities import Funcionario, Produto, Maquina


# ---------------------------------------------------------------------------
# Funcionários
# ---------------------------------------------------------------------------


def _row_to_funcionario(row) -> Funcionario:
    return Funcionario(
        id=row["id"],
        nome=row["nome"],
        turno=row["turno"],
        restricao=row["restricao"],
        ativo=bool(row["ativo"]),
    )


def criar_funcionario(funcionario: Funcionario) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO funcionarios (nome, turno, restricao, ativo)
            VALUES (?, ?, ?, ?)
            """,
            (funcionario.nome, funcionario.turno, funcionario.restricao, int(funcionario.ativo)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def listar_funcionarios(apenas_ativos: bool = False) -> List[Funcionario]:
    conn = get_connection()
    try:
        if apenas_ativos:
            rows = conn.execute(
                "SELECT * FROM funcionarios WHERE ativo = 1 ORDER BY nome"
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM funcionarios ORDER BY nome").fetchall()
        return [_row_to_funcionario(r) for r in rows]
    finally:
        conn.close()

def listar_funcionarios_turno(turno: int) -> List[Funcionario]:
    """
    Retorna todos os funcionários ativos de um turno.
    """
    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM funcionarios
            WHERE turno = ?
              AND ativo = 1
            ORDER BY nome
            """,
            (turno,),
        ).fetchall()

        return [_row_to_funcionario(row) for row in rows]

    finally:
        conn.close()

def buscar_funcionario_por_id(funcionario_id: int) -> Optional[Funcionario]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM funcionarios WHERE id = ?", (funcionario_id,)
        ).fetchone()
        return _row_to_funcionario(row) if row else None
    finally:
        conn.close()


def atualizar_funcionario(funcionario: Funcionario) -> None:
    if funcionario.id is None:
        raise ValueError("Não é possível atualizar um funcionário sem id.")

    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE funcionarios
            SET nome = ?, turno = ?, restricao = ?, ativo = ?
            WHERE id = ?
            """,
            (
                funcionario.nome,
                funcionario.turno,
                funcionario.restricao,
                int(funcionario.ativo),
                funcionario.id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def excluir_funcionario(funcionario_id: int) -> None:
    """
    Remove o funcionário definitivamente.

    O banco recusa (FOREIGN KEY) se ele já tiver alocações no histórico.
    Isso é intencional. Para afastar um funcionário sem perder histórico,
    o caminho correto é marcar `ativo = False`, não excluir.
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM funcionarios WHERE id = ?", (funcionario_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------


def _row_to_produto(row) -> Produto:
    return Produto(id=row["id"], nome=row["nome"], dificuldade=row["dificuldade"])


def criar_produto(produto: Produto) -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO produtos (nome, dificuldade) VALUES (?, ?)",
            (produto.nome, produto.dificuldade),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def listar_produtos() -> List[Produto]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM produtos ORDER BY nome").fetchall()
        return [_row_to_produto(r) for r in rows]
    finally:
        conn.close()


def buscar_produto_por_id(produto_id: int) -> Optional[Produto]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _row_to_produto(row) if row else None
    finally:
        conn.close()


def atualizar_produto(produto: Produto) -> None:
    if produto.id is None:
        raise ValueError("Não é possível atualizar um produto sem id.")

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE produtos SET nome = ?, dificuldade = ? WHERE id = ?",
            (produto.nome, produto.dificuldade, produto.id),
        )
        conn.commit()
    finally:
        conn.close()


def excluir_produto(produto_id: int) -> None:
    """
    Remove o produto definitivamente. O banco recusa (FOREIGN KEY) se ele
    já tiver sido usado em algum rodízio (`rodizio_maquinas`).
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Máquinas
# ---------------------------------------------------------------------------


def _buscar_componentes_ids(conn, maquina_id: int) -> List[int]:
    rows = conn.execute(
        "SELECT maquina_componente_id FROM maquina_componentes WHERE maquina_composta_id = ?",
        (maquina_id,),
    ).fetchall()
    return [r["maquina_componente_id"] for r in rows]


def _row_to_maquina(conn, row) -> Maquina:
    return Maquina(
        id=row["id"],
        nome=row["nome"],
        critica=bool(row["critica"]),
        componentes=_buscar_componentes_ids(conn, row["id"]),
    )


def criar_maquina(maquina: Maquina) -> int:
    """
    Cria a máquina. Os componentes (se houver) devem ser definidos
    depois, com `definir_componentes`, pois exigem que a máquina já
    tenha um id.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO maquinas (nome, critica) VALUES (?, ?)",
            (maquina.nome, int(maquina.critica)),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def definir_componentes(maquina_composta_id: int, componentes_ids: List[int]) -> None:
    """
    Substitui a lista de componentes de uma máquina composta.

    Apaga tudo e reinsere em vez de calcular um "diff" — a lista de
    componentes raramente muda, e quando muda é o usuário reeditando
    o cadastro inteiro. Simplicidade aqui vale mais que economizar
    alguns comandos SQL.
    """
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM maquina_componentes WHERE maquina_composta_id = ?",
            (maquina_composta_id,),
        )
        for componente_id in componentes_ids:
            conn.execute(
                """
                INSERT INTO maquina_componentes (maquina_composta_id, maquina_componente_id)
                VALUES (?, ?)
                """,
                (maquina_composta_id, componente_id),
            )
        conn.commit()
    finally:
        conn.close()


def listar_maquinas() -> List[Maquina]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM maquinas ORDER BY nome").fetchall()
        return [_row_to_maquina(conn, r) for r in rows]
    finally:
        conn.close()


def buscar_maquina_por_id(maquina_id: int) -> Optional[Maquina]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM maquinas WHERE id = ?", (maquina_id,)).fetchone()
        return _row_to_maquina(conn, row) if row else None
    finally:
        conn.close()

def listar_maquinas_equivalentes(maquina_id: int) -> List[int]:
    """
    Retorna todas as máquinas equivalentes para efeito de histórico.

    Se a máquina for composta, retorna ela própria + seus componentes.

    Exemplo:
        Máquina 12-24 -> [12, 24]

    Se não possuir componentes:
        Máquina 18 -> [18]
    """
    conn = get_connection()
    try:
        componentes = _buscar_componentes_ids(conn, maquina_id)

        if componentes:
            return [maquina_id] + componentes

        return [maquina_id]

    finally:
        conn.close()

def atualizar_maquina(maquina: Maquina) -> None:
    """
    Atualiza nome/crítica. Não mexe em componentes — quem chama esta
    função deve chamar `definir_componentes` separadamente se a lista
    de componentes mudou.
    """
    if maquina.id is None:
        raise ValueError("Não é possível atualizar uma máquina sem id.")

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE maquinas SET nome = ?, critica = ? WHERE id = ?",
            (maquina.nome, int(maquina.critica), maquina.id),
        )
        conn.commit()
    finally:
        conn.close()


def excluir_maquina(maquina_id: int) -> None:
    """
    Remove a máquina definitivamente.

    O banco recusa (FOREIGN KEY) se essa máquina:
    - já foi usada em algum rodízio (`rodizio_maquinas`), ou
    - é componente de alguma máquina composta, ou
    - é ela própria uma composta com componentes cadastrados
      (nesse caso, limpar com `definir_componentes(id, [])` antes).
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM maquinas WHERE id = ?", (maquina_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Rodízios (cabeçalho semana/turno + programação informada pelo PCP)
# ---------------------------------------------------------------------------


def criar_rodizio(semana: int, turno: int) -> int:
    """
    Cria o cabeçalho de uma nova geração de rodízio (semana + turno).

    Não há verificação de duplicidade aqui de propósito: se o usuário
    gerar duas vezes para a mesma semana/turno (ex: para corrigir um
    erro de digitação), fica um novo registro no histórico em vez de
    sobrescrever o anterior. Ambos continuam consultáveis.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO rodizios (semana, turno) VALUES (?, ?)",
            (semana, turno),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def adicionar_rodizio_maquina(
    rodizio_id: int, maquina_id: int, produto_id: int, qtd_operadores: int
) -> int:
    """Registra uma linha da programação do PCP: uma máquina + produto + qtd de operadores."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO rodizio_maquinas (rodizio_id, maquina_id, produto_id, qtd_operadores)
            VALUES (?, ?, ?, ?)
            """,
            (rodizio_id, maquina_id, produto_id, qtd_operadores),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def listar_rodizio_maquinas(rodizio_id: int) -> List[dict]:
    """
    Retorna a programação de um rodízio, já com nomes de máquina e
    produto resolvidos (join), pronta para exibição — evita que a UI
    precise fazer lookup manual de id para nome.

    Também traz `maquina_critica`, já resolvida via join com `maquinas`,
    para que o RotationEngine não precise fazer uma consulta extra por
    máquina só para saber se ela é crítica.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT rm.id, rm.maquina_id, m.nome AS maquina_nome, m.critica AS maquina_critica,
                   rm.produto_id, p.nome AS produto_nome, p.dificuldade,
                   rm.qtd_operadores
            FROM rodizio_maquinas rm
            JOIN maquinas m ON m.id = rm.maquina_id
            JOIN produtos p ON p.id = rm.produto_id
            WHERE rm.rodizio_id = ?
            ORDER BY rm.id
            """,
            (rodizio_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def remover_rodizio_maquina(rodizio_maquina_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM rodizio_maquinas WHERE id = ?", (rodizio_maquina_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Rodízios (captura da programação semanal do PCP)
# ---------------------------------------------------------------------------

def buscar_rodizio_por_id(rodizio_id: int) -> Optional[dict]:
    """
    Busca o cabeçalho de um rodízio pelo id.
    """
    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT id, semana, turno
            FROM rodizios
            WHERE id = ?
            """,
            (rodizio_id,),
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()
        
def obter_ou_criar_rodizio(semana: int, turno: int) -> int:
    """
    Retorna o id do rodízio (semana, turno) se já existir, ou cria um novo.

    Por quê "obter ou criar" em vez de sempre criar: o usuário pode entrar
    na tela "Nova Semana", adicionar 2 máquinas, sair, voltar depois e
    adicionar mais 1 máquina para a mesma semana/turno. Sem esse
    get-or-create, cada visita geraria um novo cabeçalho de rodízio
    duplicado para a mesma semana/turno.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM rodizios WHERE semana = ? AND turno = ?", (semana, turno)
        ).fetchone()
        if row:
            return row["id"]

        cursor = conn.execute(
            "INSERT INTO rodizios (semana, turno) VALUES (?, ?)", (semana, turno)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Rodízios — listagem para seleção (usado pela ResultadoScreen)
# ---------------------------------------------------------------------------


def listar_rodizios() -> List[dict]:
    """
    Retorna todos os cabeçalhos de rodízio já salvos, mais recentes primeiro.
    Usado para popular o seletor "escolha um rodízio" da ResultadoScreen.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, semana, turno, data_geracao FROM rodizios ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Alocações
# ---------------------------------------------------------------------------


def criar_alocacao(
    rodizio_id: int,
    rodizio_maquina_id: Optional[int],
    funcionario_id: int,
    destino: str,
) -> int:
    """
    Cria uma alocação de um funcionário.

    destino:
        "maquina" -> rodizio_maquina_id deve possuir valor.
        "kit"     -> rodizio_maquina_id deve ser None (excedente sem máquina).

    rodizio_id é sempre obrigatório, mesmo com destino="kit" — é o único
    jeito de depois saber a que rodízio aquele "kit" pertence, já que
    nesse caso não há rodizio_maquina_id para chegar até lá.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO alocacoes (
                rodizio_id,
                rodizio_maquina_id,
                funcionario_id,
                destino
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                rodizio_id,
                rodizio_maquina_id,
                funcionario_id,
                destino,
            ),
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def rodizio_tem_alocacoes(rodizio_id: int) -> bool:
    """
    Diz se um rodízio já foi processado pelo RotationEngine.

    Usado pela ResultadoScreen antes de chamar `engine.gerar()`, para
    decidir entre "gerar agora" e "só exibir o que já existe" — sem essa
    checagem, gerar duas vezes duplicaria todas as alocações no banco.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM alocacoes WHERE rodizio_id = ? LIMIT 1", (rodizio_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def limpar_alocacoes_rodizio(rodizio_id: int) -> None:
    """
    Apaga todas as alocações de um rodízio, para permitir gerar de novo
    (ex: usuário cadastrou um funcionário a mais e quer refazer o rodízio).
    """
    conn = get_connection()
    try:
        conn.execute("DELETE FROM alocacoes WHERE rodizio_id = ?", (rodizio_id,))
        conn.commit()
    finally:
        conn.close()


def listar_alocacoes_rodizio(rodizio_id: int) -> List[dict]:
    """
    Retorna todas as alocações de um rodízio já geradas, prontas para
    exibição: nome do funcionário, e (quando destino='maquina') nome da
    máquina e do produto. Uma linha por funcionário alocado.

    Linhas com destino='kit' vêm com maquina_nome/produto_nome = None —
    a UI é quem decide como mostrar isso (ex: seção separada "Kit").
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT a.id, a.destino, a.rodizio_maquina_id,
                   f.id AS funcionario_id, f.nome AS funcionario_nome, f.restricao,
                   m.nome AS maquina_nome, m.critica AS maquina_critica,
                   p.nome AS produto_nome
            FROM alocacoes a
            JOIN funcionarios f ON f.id = a.funcionario_id
            LEFT JOIN rodizio_maquinas rm ON rm.id = a.rodizio_maquina_id
            LEFT JOIN maquinas m ON m.id = rm.maquina_id
            LEFT JOIN produtos p ON p.id = rm.produto_id
            WHERE a.rodizio_id = ?
            ORDER BY rm.id, f.nome
            """,
            (rodizio_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()