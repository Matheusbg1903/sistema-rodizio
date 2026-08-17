"""
Tela Nova Semana.

Fluxo: usuário informa Semana + Turno, depois vai adicionando linhas
da programação enviada pelo PCP (Máquina, Produto, Qtd. Operadores).
Ao clicar em "Salvar Programação", tudo é persistido:
  1. um novo registro em `rodizios` (cabeçalho semana/turno)
  2. uma linha em `rodizio_maquinas` para cada item da lista

IMPORTANTE (escopo desta etapa): esta tela só CAPTURA e SALVA a
programação. Ela não gera o rodízio ainda — isso é o motor de
geração (`core/rotation_engine.py`), que entra na Etapa 6. Por isso
o botão final se chama "Salvar Programação da Semana", não "Gerar
Rodízio": seria enganoso prometer uma geração que ainda não existe.
"""

import customtkinter as ctk
from tkinter import messagebox

from database import repository


class NovaSemanaScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # lista em memória com os itens adicionados nesta sessão,
        # antes de salvar no banco. Cada item: {"maquina_id", "maquina_nome",
        # "produto_id", "produto_nome", "qtd_operadores"}
        self.itens_programacao = []

        self._montar_cabecalho()
        self._montar_form_item()
        self._montar_lista_itens()
        self._montar_acao_final()

    # ---------- Cabeçalho: semana + turno ----------

    def _montar_cabecalho(self):
        bloco = ctk.CTkFrame(self)
        bloco.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(bloco, text="Nova Semana", font=("", 16, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 15)
        )

        ctk.CTkLabel(bloco, text="Semana (nº)").grid(row=1, column=0, sticky="w", padx=10)
        self.entry_semana = ctk.CTkEntry(bloco, width=100)
        self.entry_semana.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 15))

        ctk.CTkLabel(bloco, text="Turno").grid(row=1, column=2, sticky="w", padx=10)
        self.option_turno = ctk.CTkOptionMenu(bloco, values=["1", "2", "3"])
        self.option_turno.grid(row=1, column=3, sticky="w", padx=10, pady=(0, 15))

    # ---------- Formulário para adicionar um item da programação ----------

    def _montar_form_item(self):
        bloco = ctk.CTkFrame(self)
        bloco.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(bloco, text="Adicionar item da programação (PCP)", font=("", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 10)
        )

        ctk.CTkLabel(bloco, text="Máquina").grid(row=1, column=0, sticky="w", padx=10)
        self.option_maquina = ctk.CTkOptionMenu(bloco, values=["—"], width=180)
        self.option_maquina.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

        ctk.CTkLabel(bloco, text="Produto").grid(row=1, column=1, sticky="w", padx=10)
        self.option_produto = ctk.CTkOptionMenu(bloco, values=["—"], width=180)
        self.option_produto.grid(row=2, column=1, sticky="w", padx=10, pady=(0, 10))

        ctk.CTkLabel(bloco, text="Qtd. Operadores").grid(row=1, column=2, sticky="w", padx=10)
        self.entry_qtd = ctk.CTkEntry(bloco, width=100)
        self.entry_qtd.grid(row=2, column=2, sticky="w", padx=10, pady=(0, 10))

        ctk.CTkButton(bloco, text="Adicionar à lista", command=self._adicionar_item).grid(
            row=2, column=3, sticky="w", padx=10, pady=(0, 10)
        )

        # os dropdowns de máquina/produto são recarregados sempre que a
        # tela aparece, para refletir cadastros feitos nas outras telas
        self._recarregar_opcoes()

    def _recarregar_opcoes(self):
        self.maquinas_cadastradas = repository.listar_maquinas()
        self.produtos_cadastrados = repository.listar_produtos()

        nomes_maquinas = [m.nome for m in self.maquinas_cadastradas] or ["—"]
        nomes_produtos = [p.nome for p in self.produtos_cadastrados] or ["—"]

        self.option_maquina.configure(values=nomes_maquinas)
        self.option_maquina.set(nomes_maquinas[0])

        self.option_produto.configure(values=nomes_produtos)
        self.option_produto.set(nomes_produtos[0])

    # ---------- Lista de itens já adicionados ----------

    def _montar_lista_itens(self):
        ctk.CTkLabel(self, text="Programação desta semana/turno", font=("", 14, "bold")).pack(
            anchor="w", padx=20, pady=(10, 5)
        )
        self.lista_frame = ctk.CTkScrollableFrame(self, height=180)
        self.lista_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._atualizar_lista_itens()

    def _adicionar_item(self):
        nome_maquina = self.option_maquina.get()
        nome_produto = self.option_produto.get()

        if nome_maquina == "—" or nome_produto == "—":
            messagebox.showwarning(
                "Cadastro necessário",
                "Cadastre pelo menos uma máquina e um produto antes de montar a programação.",
            )
            return

        qtd_texto = self.entry_qtd.get().strip()
        if not qtd_texto.isdigit() or int(qtd_texto) <= 0:
            messagebox.showwarning(
                "Quantidade inválida", "Informe uma quantidade de operadores válida (maior que zero)."
            )
            return

        maquina = next(m for m in self.maquinas_cadastradas if m.nome == nome_maquina)
        produto = next(p for p in self.produtos_cadastrados if p.nome == nome_produto)

        # regra: mesma máquina não pode aparecer duas vezes na mesma programação
        if any(item["maquina_id"] == maquina.id for item in self.itens_programacao):
            messagebox.showwarning(
                "Máquina já adicionada",
                f"A máquina '{maquina.nome}' já está na lista desta semana/turno. "
                "Remova o item existente antes de adicionar de novo.",
            )
            return

        self.itens_programacao.append({
            "maquina_id": maquina.id,
            "maquina_nome": maquina.nome,
            "produto_id": produto.id,
            "produto_nome": produto.nome,
            "qtd_operadores": int(qtd_texto),
        })

        self.entry_qtd.delete(0, "end")
        self._atualizar_lista_itens()

    def _remover_item(self, indice: int):
        self.itens_programacao.pop(indice)
        self._atualizar_lista_itens()

    def _atualizar_lista_itens(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        if not self.itens_programacao:
            ctk.CTkLabel(self.lista_frame, text="Nenhum item adicionado ainda.").pack(
                anchor="w", padx=5, pady=5
            )
            return

        for indice, item in enumerate(self.itens_programacao):
            linha = ctk.CTkFrame(self.lista_frame)
            linha.pack(fill="x", pady=3)

            texto = (
                f"{item['maquina_nome']}  —  {item['produto_nome']}  —  "
                f"{item['qtd_operadores']} operador(es)"
            )
            ctk.CTkLabel(linha, text=texto, anchor="w").pack(
                side="left", fill="x", expand=True, padx=10, pady=8
            )

            ctk.CTkButton(
                linha, text="Remover", width=70, fg_color="darkred", hover_color="red4",
                command=lambda i=indice: self._remover_item(i),
            ).pack(side="left", padx=5)

    # ---------- Salvar tudo ----------

    def _montar_acao_final(self):
        bloco = ctk.CTkFrame(self, fg_color="transparent")
        bloco.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            bloco, text="Salvar Programação da Semana",
            command=self._salvar_programacao,
        ).pack(anchor="w")

        ctk.CTkLabel(
            bloco,
            text="A geração automática do rodízio (escolha dos funcionários) será "
                 "adicionada na próxima etapa.",
            font=("", 10), text_color="gray50",
        ).pack(anchor="w", pady=(5, 0))

    def _salvar_programacao(self):
        semana_texto = self.entry_semana.get().strip()
        if not semana_texto.isdigit():
            messagebox.showwarning("Semana inválida", "Informe o número da semana.")
            return

        if not self.itens_programacao:
            messagebox.showwarning(
                "Programação vazia", "Adicione pelo menos uma máquina à programação antes de salvar."
            )
            return

        semana = int(semana_texto)
        turno = int(self.option_turno.get())

        rodizio_id = repository.criar_rodizio(semana=semana, turno=turno)
        for item in self.itens_programacao:
            repository.adicionar_rodizio_maquina(
                rodizio_id=rodizio_id,
                maquina_id=item["maquina_id"],
                produto_id=item["produto_id"],
                qtd_operadores=item["qtd_operadores"],
            )

        messagebox.showinfo(
            "Programação salva",
            f"Programação da Semana {semana}, Turno {turno} salva com sucesso.\n"
            "A geração automática do rodízio será feita na próxima etapa do sistema.",
        )

        self.itens_programacao = []
        self.entry_semana.delete(0, "end")
        self._atualizar_lista_itens()

    # ---------- Chamado pela sidebar toda vez que a tela é exibida ----------

    def atualizar_ao_exibir(self):
        """
        Recarrega os dropdowns de máquina/produto. Chamado pelo app.py
        sempre que o usuário navega para esta tela, para refletir
        cadastros feitos enquanto a tela estava em segundo plano.
        """
        self._recarregar_opcoes()
