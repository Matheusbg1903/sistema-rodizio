"""
Janela principal.

Sidebar de navegação: uma lista de botões à esquerda troca o frame
central. Cada tela é instanciada uma vez e fica "escondida" quando não
está em uso — evita recriar o formulário toda hora e perder posição de
scroll.

O visual (cores, fontes) vem do módulo ui.theme, para manter tudo
consistente e fácil de trocar num lugar só.
"""

import customtkinter as ctk

from ui import theme
from ui.screens.funcionarios_screen import FuncionariosScreen
from ui.screens.produtos_screen import ProdutosScreen
from ui.screens.maquinas_screen import MaquinasScreen
from ui.screens.nova_semana_screen import NovaSemanaScreen
from ui.screens.resultado_screen import ResultadoScreen


COR_SIDEBAR_FUNDO = "#FFFFFF"
COR_SIDEBAR_BOTAO = "#F1F2F6"
COR_SIDEBAR_BOTAO_ATIVO = theme.COR_MARCA_VERDE
COR_SIDEBAR_TEXTO = "#4B5563"
COR_SIDEBAR_TEXTO_ATIVO = "#FFFFFF"
COR_SIDEBAR_BORDA = "#E4E6EC"


class App(ctk.CTk):
    def __init__(self):
        theme.aplicar_tema()
        super().__init__()

        self.title("Sistema de Rodízio")
        self.geometry("1000x700")
        self.minsize(900, 600)

        self.botoes_sidebar = {}
        self.tela_atual = None

        self._montar_sidebar()
        self._montar_telas()
        self._mostrar_tela("Funcionários")

    def _montar_logo(self, sidebar):
        """
        Carrega assets/logo_plastilania.png e exibe no topo da sidebar,
        mantendo a proporção original da imagem. CTkImage (em vez de um
        PhotoImage puro do Tk) é o que o CustomTkinter recomenda, porque
        ele lida sozinho com telas de alta resolução (HiDPI).
        """
        from PIL import Image

        caminho_logo = theme.caminho_recurso("assets", "logo_plastilania.png")
        imagem_original = Image.open(caminho_logo)

        largura_alvo = 150
        proporcao = imagem_original.height / imagem_original.width
        altura_alvo = round(largura_alvo * proporcao)

        logo_ctk = ctk.CTkImage(
            light_image=imagem_original, dark_image=imagem_original,
            size=(largura_alvo, altura_alvo),
        )

        ctk.CTkLabel(sidebar, image=logo_ctk, text="").pack(padx=24, pady=(28, 6), anchor="w")

    def _montar_sidebar(self):
        sidebar = ctk.CTkFrame(
            self, width=200, corner_radius=0, fg_color=COR_SIDEBAR_FUNDO,
            border_width=0, border_color=COR_SIDEBAR_BORDA,
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # linha divisória fina entre a sidebar clara e o conteúdo escuro
        ctk.CTkFrame(sidebar, width=1, fg_color=COR_SIDEBAR_BORDA, border_width=0).place(
            relx=1.0, rely=0, relheight=1.0, anchor="ne"
        )

        self._montar_logo(sidebar)

        ctk.CTkLabel(
            sidebar, text="Sistema de Rodízio",
            font=theme.fonte_pequena(),
            text_color=COR_SIDEBAR_TEXTO,
        ).pack(padx=24, pady=(0, 30), anchor="w")

        for nome_tela in ["Funcionários", "Produtos", "Máquinas", "Nova Semana", "Resultado"]:
            botao = ctk.CTkButton(
                sidebar, text=nome_tela, anchor="w",
                font=theme.fonte_sidebar_botao(),
                corner_radius=8,
                height=40,
                fg_color=COR_SIDEBAR_BOTAO,
                hover_color=COR_SIDEBAR_BOTAO_ATIVO,
                text_color=COR_SIDEBAR_TEXTO,
                command=lambda n=nome_tela: self._mostrar_tela(n),
            )
            botao.pack(fill="x", padx=16, pady=4)
            self.botoes_sidebar[nome_tela] = botao

    def _montar_telas(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.container.pack(side="left", fill="both", expand=True)

        self.telas = {
            "Funcionários": FuncionariosScreen(self.container),
            "Produtos": ProdutosScreen(self.container),
            "Máquinas": MaquinasScreen(self.container),
            "Nova Semana": NovaSemanaScreen(self.container),
            "Resultado": ResultadoScreen(self.container),
        }

    def _mostrar_tela(self, nome_tela: str):
        for tela in self.telas.values():
            tela.pack_forget()

        # realce visual da aba ativa na sidebar
        for nome, botao in self.botoes_sidebar.items():
            if nome == nome_tela:
                botao.configure(fg_color=COR_SIDEBAR_BOTAO_ATIVO, text_color=COR_SIDEBAR_TEXTO_ATIVO)
            else:
                botao.configure(fg_color=COR_SIDEBAR_BOTAO, text_color=COR_SIDEBAR_TEXTO)

        tela_alvo = self.telas[nome_tela]
        if hasattr(tela_alvo, "atualizar_ao_exibir"):
            tela_alvo.atualizar_ao_exibir()
        tela_alvo.pack(fill="both", expand=True, padx=24, pady=24)
        self.tela_atual = nome_tela


def run():
    app = App()
    app.mainloop()