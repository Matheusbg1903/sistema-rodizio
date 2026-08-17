"""
Tela de Produtos.

Mesmo padrão da tela de Funcionários: formulário + lista com
Editar/Excluir. Mantenho a estrutura repetida de propósito — telas de
cadastro simples (CRUD) não precisam de abstração genérica no MVP;
isso só adicionaria indireção sem ganho real neste tamanho de projeto.
"""

import customtkinter as ctk
from tkinter import messagebox

from database import repository
from models.entities import Produto

DIFICULDADES = {"Fácil": "facil", "Médio": "medio", "Difícil": "dificil"}
DIFICULDADES_INVERSO = {v: k for k, v in DIFICULDADES.items()}


class ProdutosScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.editando_id = None

        self._montar_formulario()
        self._montar_lista()
        self._atualizar_lista()

    def _montar_formulario(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(form, text="Cadastro de Produto", font=("", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 15)
        )

        ctk.CTkLabel(form, text="Nome").grid(row=1, column=0, sticky="w", padx=10)
        self.entry_nome = ctk.CTkEntry(form, width=250)
        self.entry_nome.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(form, text="Dificuldade").grid(row=2, column=0, sticky="w", padx=10)
        self.option_dificuldade = ctk.CTkOptionMenu(form, values=list(DIFICULDADES.keys()))
        self.option_dificuldade.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.grid(row=3, column=0, columnspan=2, pady=(10, 15))

        self.btn_salvar = ctk.CTkButton(botoes, text="Salvar", command=self._salvar)
        self.btn_salvar.pack(side="left", padx=5)

        self.btn_cancelar = ctk.CTkButton(
            botoes, text="Cancelar edição", fg_color="gray40",
            command=self._cancelar_edicao,
        )
        self.btn_cancelar.pack_forget()

    def _montar_lista(self):
        ctk.CTkLabel(self, text="Produtos cadastrados", font=("", 14, "bold")).pack(
            anchor="w", padx=20, pady=(10, 5)
        )
        self.lista_frame = ctk.CTkScrollableFrame(self, height=250)
        self.lista_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def _salvar(self):
        nome = self.entry_nome.get().strip()
        if not nome:
            messagebox.showwarning("Campo obrigatório", "Informe o nome do produto.")
            return

        produto = Produto(
            id=self.editando_id,
            nome=nome,
            dificuldade=DIFICULDADES[self.option_dificuldade.get()],
        )

        if self.editando_id is None:
            repository.criar_produto(produto)
        else:
            repository.atualizar_produto(produto)

        self._limpar_formulario()
        self._atualizar_lista()

    def _editar(self, produto: Produto):
        self.editando_id = produto.id
        self.entry_nome.delete(0, "end")
        self.entry_nome.insert(0, produto.nome)
        self.option_dificuldade.set(DIFICULDADES_INVERSO[produto.dificuldade])

        self.btn_salvar.configure(text="Atualizar")
        self.btn_cancelar.pack(side="left", padx=5)

    def _excluir(self, produto: Produto):
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Excluir o produto '{produto.nome}'?\n\n"
            "Isso só é possível se ele nunca tiver sido usado em nenhum rodízio.",
        )
        if not confirmar:
            return

        try:
            repository.excluir_produto(produto.id)
        except Exception:
            messagebox.showerror(
                "Não foi possível excluir",
                "Este produto já foi usado em algum rodízio e não pode ser excluído.",
            )
            return

        self._atualizar_lista()

    def _cancelar_edicao(self):
        self._limpar_formulario()

    def _limpar_formulario(self):
        self.editando_id = None
        self.entry_nome.delete(0, "end")
        self.option_dificuldade.set("Fácil")
        self.btn_salvar.configure(text="Salvar")
        self.btn_cancelar.pack_forget()

    def _atualizar_lista(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        produtos = repository.listar_produtos()

        if not produtos:
            ctk.CTkLabel(self.lista_frame, text="Nenhum produto cadastrado ainda.").pack(
                anchor="w", padx=5, pady=5
            )
            return

        for produto in produtos:
            linha = ctk.CTkFrame(self.lista_frame)
            linha.pack(fill="x", pady=3)

            dificuldade_label = DIFICULDADES_INVERSO[produto.dificuldade]
            texto = f"{produto.nome}  —  {dificuldade_label}"

            ctk.CTkLabel(linha, text=texto, anchor="w").pack(
                side="left", fill="x", expand=True, padx=10, pady=8
            )

            ctk.CTkButton(
                linha, text="Editar", width=70,
                command=lambda p=produto: self._editar(p),
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                linha, text="Excluir", width=70, fg_color="darkred", hover_color="red4",
                command=lambda p=produto: self._excluir(p),
            ).pack(side="left", padx=5)
