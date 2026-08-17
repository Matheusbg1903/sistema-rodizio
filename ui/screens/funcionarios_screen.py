"""
Tela de Funcionários.

Um formulário simples (nome, turno, restrição, ativo) + uma lista
com os funcionários já cadastrados, cada um com botões de Editar e
Excluir.

Essa tela não sabe SQL — toda persistência passa por
`database.repository`. Se o repository mudar de implementação, esta
tela não precisa ser tocada.
"""

import customtkinter as ctk
from tkinter import messagebox

from database import repository
from models.entities import Funcionario

RESTRICOES = {
    "Nenhuma": "nenhuma",
    "Gestante": "gestante",
    "Restrição Física": "fisica",
    "Restrição Temporária": "temporaria",
}
RESTRICOES_INVERSO = {v: k for k, v in RESTRICOES.items()}


class FuncionariosScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # id do funcionário em edição. None = modo "novo cadastro".
        self.editando_id = None

        self._montar_formulario()
        self._montar_lista()
        self._atualizar_lista()

    # ---------- Formulário ----------

    def _montar_formulario(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(form, text="Cadastro de Funcionário", font=("", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 15)
        )

        # Nome
        ctk.CTkLabel(form, text="Nome").grid(row=1, column=0, sticky="w", padx=10)
        self.entry_nome = ctk.CTkEntry(form, width=250)
        self.entry_nome.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Turno
        ctk.CTkLabel(form, text="Turno").grid(row=2, column=0, sticky="w", padx=10)
        self.option_turno = ctk.CTkOptionMenu(form, values=["1", "2", "3"])
        self.option_turno.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Restrição
        ctk.CTkLabel(form, text="Restrição").grid(row=3, column=0, sticky="w", padx=10)
        self.option_restricao = ctk.CTkOptionMenu(form, values=list(RESTRICOES.keys()))
        self.option_restricao.grid(row=3, column=1, sticky="w", padx=10, pady=5)

        # Ativo
        self.check_ativo = ctk.CTkCheckBox(form, text="Ativo")
        self.check_ativo.select()  # marcado por padrão em novo cadastro
        self.check_ativo.grid(row=4, column=1, sticky="w", padx=10, pady=5)

        # Botões
        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.grid(row=5, column=0, columnspan=2, pady=(10, 15))

        self.btn_salvar = ctk.CTkButton(botoes, text="Salvar", command=self._salvar)
        self.btn_salvar.pack(side="left", padx=5)

        self.btn_cancelar = ctk.CTkButton(
            botoes, text="Cancelar edição", fg_color="gray40",
            command=self._cancelar_edicao,
        )
        # só aparece quando estamos editando alguém
        self.btn_cancelar.pack_forget()

    def _montar_lista(self):
        ctk.CTkLabel(self, text="Funcionários cadastrados", font=("", 14, "bold")).pack(
            anchor="w", padx=20, pady=(10, 5)
        )
        self.lista_frame = ctk.CTkScrollableFrame(self, height=250)
        self.lista_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # ---------- Ações ----------

    def _salvar(self):
        nome = self.entry_nome.get().strip()
        if not nome:
            messagebox.showwarning("Campo obrigatório", "Informe o nome do funcionário.")
            return

        funcionario = Funcionario(
            id=self.editando_id,
            nome=nome,
            turno=int(self.option_turno.get()),
            restricao=RESTRICOES[self.option_restricao.get()],
            ativo=bool(self.check_ativo.get()),
        )

        if self.editando_id is None:
            repository.criar_funcionario(funcionario)
        else:
            repository.atualizar_funcionario(funcionario)

        self._limpar_formulario()
        self._atualizar_lista()

    def _editar(self, funcionario: Funcionario):
        self.editando_id = funcionario.id
        self.entry_nome.delete(0, "end")
        self.entry_nome.insert(0, funcionario.nome)
        self.option_turno.set(str(funcionario.turno))
        self.option_restricao.set(RESTRICOES_INVERSO[funcionario.restricao])
        if funcionario.ativo:
            self.check_ativo.select()
        else:
            self.check_ativo.deselect()

        self.btn_salvar.configure(text="Atualizar")
        self.btn_cancelar.pack(side="left", padx=5)

    def _excluir(self, funcionario: Funcionario):
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Excluir o funcionário '{funcionario.nome}'?\n\n"
            "Isso só é possível se ele nunca tiver sido alocado em nenhum rodízio.",
        )
        if not confirmar:
            return

        try:
            repository.excluir_funcionario(funcionario.id)
        except Exception:
            messagebox.showerror(
                "Não foi possível excluir",
                "Este funcionário já possui histórico de rodízio e não pode ser excluído.\n"
                "Em vez disso, desmarque a opção 'Ativo' para afastá-lo das próximas gerações.",
            )
            return

        self._atualizar_lista()

    def _cancelar_edicao(self):
        self._limpar_formulario()

    def _limpar_formulario(self):
        self.editando_id = None
        self.entry_nome.delete(0, "end")
        self.option_turno.set("1")
        self.option_restricao.set("Nenhuma")
        self.check_ativo.select()
        self.btn_salvar.configure(text="Salvar")
        self.btn_cancelar.pack_forget()

    def _atualizar_lista(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        funcionarios = repository.listar_funcionarios()

        if not funcionarios:
            ctk.CTkLabel(self.lista_frame, text="Nenhum funcionário cadastrado ainda.").pack(
                anchor="w", padx=5, pady=5
            )
            return

        for funcionario in funcionarios:
            linha = ctk.CTkFrame(self.lista_frame)
            linha.pack(fill="x", pady=3)

            status = "Ativo" if funcionario.ativo else "Inativo"
            restricao_label = RESTRICOES_INVERSO[funcionario.restricao]
            texto = f"{funcionario.nome}  —  Turno {funcionario.turno}  —  {restricao_label}  —  {status}"

            ctk.CTkLabel(linha, text=texto, anchor="w").pack(
                side="left", fill="x", expand=True, padx=10, pady=8
            )

            ctk.CTkButton(
                linha, text="Editar", width=70,
                command=lambda f=funcionario: self._editar(f),
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                linha, text="Excluir", width=70, fg_color="darkred", hover_color="red4",
                command=lambda f=funcionario: self._excluir(f),
            ).pack(side="left", padx=5)
