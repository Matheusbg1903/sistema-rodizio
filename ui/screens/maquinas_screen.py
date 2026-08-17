"""
Tela de Máquinas.

Além do CRUD básico (nome, crítica), esta tela resolve o caso de
máquinas compostas como "12-24": ao marcar "Máquina composta", aparece
uma lista de checkboxes com as máquinas já cadastradas, para escolher
quais entram como componentes.

Fluxo esperado de uso: primeiro cadastra as máquinas simples ("12",
"24"), depois cadastra a máquina composta ("12-24") marcando as duas
anteriores como componentes.
"""

import customtkinter as ctk
from tkinter import messagebox

from database import repository
from models.entities import Maquina


class MaquinasScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        self.editando_id = None
        # guarda as referências dos checkboxes de componentes: {maquina_id: CTkCheckBox}
        self.checkboxes_componentes = {}

        self._montar_formulario()
        self._montar_lista()
        self._atualizar_lista()

    # ---------- Formulário ----------

    def _montar_formulario(self):
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(form, text="Cadastro de Máquina", font=("", 16, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 15)
        )

        ctk.CTkLabel(form, text="Nome").grid(row=1, column=0, sticky="w", padx=10)
        self.entry_nome = ctk.CTkEntry(form, width=250)
        self.entry_nome.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        self.check_critica = ctk.CTkCheckBox(form, text="Máquina crítica")
        self.check_critica.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Área de componentes (dinâmica: refeita toda vez que a lista de
        # máquinas cadastradas muda, para não mostrar a própria máquina
        # em edição como opção de componente dela mesma).
        ctk.CTkLabel(form, text="Componentes (opcional)").grid(
            row=3, column=0, sticky="nw", padx=10, pady=5
        )
        self.frame_componentes = ctk.CTkScrollableFrame(form, height=100, width=250)
        self.frame_componentes.grid(row=3, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(
            form,
            text='Marque as máquinas que esta representa (ex: "12-24" = 12 + 24)',
            font=("", 10), text_color="gray50",
        ).grid(row=4, column=1, sticky="w", padx=10)

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.grid(row=5, column=0, columnspan=2, pady=(10, 15))

        self.btn_salvar = ctk.CTkButton(botoes, text="Salvar", command=self._salvar)
        self.btn_salvar.pack(side="left", padx=5)

        self.btn_cancelar = ctk.CTkButton(
            botoes, text="Cancelar edição", fg_color="gray40",
            command=self._cancelar_edicao,
        )
        self.btn_cancelar.pack_forget()

    def _montar_lista(self):
        ctk.CTkLabel(self, text="Máquinas cadastradas", font=("", 14, "bold")).pack(
            anchor="w", padx=20, pady=(10, 5)
        )
        self.lista_frame = ctk.CTkScrollableFrame(self, height=220)
        self.lista_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # ---------- Componentes (checklist dinâmico) ----------

    def _recarregar_checklist_componentes(self):
        """Reconstrói a lista de checkboxes com as máquinas disponíveis como componente."""
        for widget in self.frame_componentes.winfo_children():
            widget.destroy()
        self.checkboxes_componentes = {}

        todas = repository.listar_maquinas()
        # uma máquina não pode ser componente dela mesma
        candidatas = [m for m in todas if m.id != self.editando_id]

        if not candidatas:
            ctk.CTkLabel(
                self.frame_componentes, text="Nenhuma outra máquina cadastrada ainda."
            ).pack(anchor="w")
            return

        for maquina in candidatas:
            checkbox = ctk.CTkCheckBox(self.frame_componentes, text=maquina.nome)
            checkbox.pack(anchor="w", pady=2)
            self.checkboxes_componentes[maquina.id] = checkbox

    def _marcar_componentes_atuais(self, componentes_ids):
        for maquina_id, checkbox in self.checkboxes_componentes.items():
            if maquina_id in componentes_ids:
                checkbox.select()
            else:
                checkbox.deselect()

    def _componentes_selecionados(self):
        return [
            maquina_id
            for maquina_id, checkbox in self.checkboxes_componentes.items()
            if checkbox.get()
        ]

    # ---------- Ações ----------

    def _salvar(self):
        nome = self.entry_nome.get().strip()
        if not nome:
            messagebox.showwarning("Campo obrigatório", "Informe o nome da máquina.")
            return

        maquina = Maquina(
            id=self.editando_id,
            nome=nome,
            critica=bool(self.check_critica.get()),
        )

        if self.editando_id is None:
            novo_id = repository.criar_maquina(maquina)
            repository.definir_componentes(novo_id, self._componentes_selecionados())
        else:
            repository.atualizar_maquina(maquina)
            repository.definir_componentes(self.editando_id, self._componentes_selecionados())

        self._limpar_formulario()
        self._atualizar_lista()

    def _editar(self, maquina: Maquina):
        self.editando_id = maquina.id
        self.entry_nome.delete(0, "end")
        self.entry_nome.insert(0, maquina.nome)
        if maquina.critica:
            self.check_critica.select()
        else:
            self.check_critica.deselect()

        self._recarregar_checklist_componentes()
        self._marcar_componentes_atuais(maquina.componentes or [])

        self.btn_salvar.configure(text="Atualizar")
        self.btn_cancelar.pack(side="left", padx=5)

    def _excluir(self, maquina: Maquina):
        confirmar = messagebox.askyesno(
            "Confirmar exclusão",
            f"Excluir a máquina '{maquina.nome}'?\n\n"
            "Isso só é possível se ela nunca tiver sido usada em nenhum rodízio "
            "e não fizer parte de nenhuma máquina composta.",
        )
        if not confirmar:
            return

        try:
            if maquina.componentes:
                repository.definir_componentes(maquina.id, [])
            repository.excluir_maquina(maquina.id)
        except Exception:
            messagebox.showerror(
                "Não foi possível excluir",
                "Esta máquina já foi usada em algum rodízio, ou é componente de "
                "outra máquina composta, e por isso não pode ser excluída.",
            )
            return

        self._atualizar_lista()

    def _cancelar_edicao(self):
        self._limpar_formulario()

    def _limpar_formulario(self):
        self.editando_id = None
        self.entry_nome.delete(0, "end")
        self.check_critica.deselect()
        self._recarregar_checklist_componentes()
        self.btn_salvar.configure(text="Salvar")
        self.btn_cancelar.pack_forget()

    def _atualizar_lista(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        maquinas = repository.listar_maquinas()
        nomes_por_id = {m.id: m.nome for m in maquinas}

        # refaz o checklist do formulário também, para refletir cadastros novos
        self._recarregar_checklist_componentes()
        if self.editando_id is not None:
            atual = repository.buscar_maquina_por_id(self.editando_id)
            if atual:
                self._marcar_componentes_atuais(atual.componentes or [])

        if not maquinas:
            ctk.CTkLabel(self.lista_frame, text="Nenhuma máquina cadastrada ainda.").pack(
                anchor="w", padx=5, pady=5
            )
            return

        for maquina in maquinas:
            linha = ctk.CTkFrame(self.lista_frame)
            linha.pack(fill="x", pady=3)

            critica_label = " · Crítica" if maquina.critica else ""
            if maquina.componentes:
                nomes_componentes = ", ".join(
                    nomes_por_id.get(cid, "?") for cid in maquina.componentes
                )
                composta_label = f"  —  Componentes: {nomes_componentes}"
            else:
                composta_label = ""

            texto = f"{maquina.nome}{critica_label}{composta_label}"

            ctk.CTkLabel(linha, text=texto, anchor="w").pack(
                side="left", fill="x", expand=True, padx=10, pady=8
            )

            ctk.CTkButton(
                linha, text="Editar", width=70,
                command=lambda m=maquina: self._editar(m),
            ).pack(side="left", padx=5)

            ctk.CTkButton(
                linha, text="Excluir", width=70, fg_color="darkred", hover_color="red4",
                command=lambda m=maquina: self._excluir(m),
            ).pack(side="left", padx=5)
