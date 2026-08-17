"""
Entidades do domínio, representadas como dataclasses.

Por que dataclasses e não dicionários soltos:
- Autocomplete e checagem de tipos no editor.
- Se um campo mudar de nome no futuro, o erro aparece na hora de rodar,
  não escondido dentro de uma string de chave de dicionário.
- Deixa explícito, em um único lugar, o que é um "Funcionário" no sistema.

Essas classes não sabem nada sobre banco de dados ou interface.
Elas são apenas estruturas de dados puras.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Funcionario:
    nome: str
    turno: int  # 1, 2 ou 3
    restricao: str = "nenhuma"  # nenhuma | gestante | fisica | temporaria
    ativo: bool = True
    id: Optional[int] = None


@dataclass
class Produto:
    nome: str
    dificuldade: str  # facil | medio | dificil
    id: Optional[int] = None


@dataclass
class Maquina:
    nome: str
    critica: bool = False
    id: Optional[int] = None
    # IDs das máquinas componentes, quando esta máquina representa um
    # conjunto (ex: máquina "12-24" teria componentes = [id_da_12, id_da_24]).
    # Lista vazia significa máquina simples, sem componentes.
    componentes: Optional[list] = None
