"""
Tema visual do sistema — um lugar só para cores e fontes, para que todas
as telas fiquem consistentes e para trocar o visual inteiro do app
mexendo em um arquivo só, em vez de em cada tela separadamente.

Uso típico dentro de uma tela:
    from ui import theme
    ctk.CTkLabel(self, text="Título", font=theme.fonte_titulo())

As cores de status (CRITICA, RESTRICAO, KIT, SUCESSO, ALERTA) não fazem
parte do tema de cores do CustomTkinter (aquele carregado via
set_default_color_theme) porque são usadas em contextos específicos
(tarjas, textos de aviso), não em todos os widgets de um tipo — por
isso ficam aqui como constantes Python simples.
"""

import customtkinter as ctk


# ---------------------------------------------------------------------------
# Cores de status — usadas manualmente em pontos específicos da UI
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Cores de status — usadas manualmente em pontos específicos da UI
#
# A área de conteúdo (à direita) é escura, então estas são cores pensadas
# para texto/tarjas sobre fundo escuro (cards com fg_color escuro).
# A barra lateral é branca, mas suas cores são definidas à parte, direto
# em ui/app.py, porque são exclusivas dela.
# ---------------------------------------------------------------------------

COR_TEXTO_PRIMARIO = "#F3F4F6"
COR_TEXTO_SECUNDARIO = "#9CA3AF"
COR_TEXTO_CLARO = "#FFFFFF"

COR_CRITICA = "#D12421"       # vermelho da marca — faixa de máquina crítica

COR_RESTRICAO = "#FBBF24"          # âmbar claro — texto do badge de restrição
COR_RESTRICAO_FUNDO = "#3A2A10"    # âmbar escuro — fundo do badge (tom escuro combina com o card)

COR_KIT = "#6B7280"           # cinza — bloco de excedente

COR_SUCESSO = "#22C55E"
COR_ALERTA = "#FBBF24"

COR_BORDA = "#323848"                # borda sutil de card sobre fundo escuro
COR_SUPERFICIE_HOVER = "#242838"     # hover de botões "outline" sobre fundo escuro

# Cores da marca Plastilânia, extraídas diretamente da logo — reaproveitadas
# fora do tema de widgets (ex: fundo de badges, destaque da aba ativa).
COR_MARCA_VERDE = "#007336"
COR_MARCA_VERDE_ESCURO = "#00522A"
COR_MARCA_VERMELHO = "#D12421"


# ---------------------------------------------------------------------------
# Fontes — funções, não constantes de módulo, porque CTkFont só pode ser
# criada depois que a janela principal (CTk root) já existe.
# ---------------------------------------------------------------------------

def fonte_titulo() -> ctk.CTkFont:
    return ctk.CTkFont(size=20, weight="bold")


def fonte_subtitulo() -> ctk.CTkFont:
    return ctk.CTkFont(size=15, weight="bold")


def fonte_texto() -> ctk.CTkFont:
    return ctk.CTkFont(size=13)


def fonte_texto_bold() -> ctk.CTkFont:
    return ctk.CTkFont(size=13, weight="bold")


def fonte_pequena() -> ctk.CTkFont:
    return ctk.CTkFont(size=11)


def fonte_sidebar_marca() -> ctk.CTkFont:
    return ctk.CTkFont(size=19, weight="bold")


def fonte_sidebar_botao() -> ctk.CTkFont:
    return ctk.CTkFont(size=13)


def caminho_recurso(*partes: str) -> str:
    """
    Resolve o caminho de um arquivo de dados (ex: o JSON do tema, a
    logo) que precisa funcionar tanto rodando com `python main.py`
    quanto empacotado como .exe pelo PyInstaller.

    Empacotado (--onefile), o PyInstaller extrai os arquivos de dados
    (os que foram incluídos via --add-data) numa pasta temporária
    própria, disponível em tempo de execução como `sys._MEIPASS` — não
    no mesmo lugar que o `.py` original. Por isso não dá para usar só
    `__file__` como fazemos no modo script.
    """
    import os
    import sys

    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base, *partes)


def aplicar_tema():
    """
    Chamado uma vez, antes de criar a janela principal (App/CTk()).

    Usa o modo "dark" do CustomTkinter para toda a área de conteúdo
    (à direita) — cards, fundo, texto claro. A barra lateral é branca,
    mas isso é feito à parte, com cores fixas em ui/app.py, porque um
    CTkFrame com fg_color explícito ignora o modo claro/escuro global.
    """
    caminho_tema = caminho_recurso("assets", "tema_fabrica.json")
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme(caminho_tema)