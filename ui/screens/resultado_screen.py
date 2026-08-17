"""
Tela Resultado.

Fluxo: usuário escolhe um rodízio já salvo (Semana + Turno). Se esse
rodízio ainda não foi processado pelo RotationEngine, o botão diz
"Gerar Rodízio" e, ao clicar, o engine roda e salva as alocações. Se já
foi processado, a tela já mostra direto o resultado salvo (sem gerar de
novo — evitar duplicar alocações no banco é responsabilidade da tela,
não do engine, ver `repository.rodizio_tem_alocacoes`).

Também existe um botão "Gerar Novamente" (refazer do zero) e um botão
"Exportar PDF" (gera um PDF pronto pra imprimir e afixar na fábrica).
"""

import os
import subprocess
import sys
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from database import repository
from core.rotation_engine import RotationEngine
from core.pdf_export import gerar_pdf_resultado
from ui import theme


class ResultadoScreen(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent", border_width=0)

        self.engine = RotationEngine()

        # {texto_exibido_no_dropdown: rodizio_id}
        self.rodizios_por_texto = {}
        self.rodizio_selecionado_id = None
        self.rodizio_selecionado_semana = None
        self.rodizio_selecionado_turno = None

        self._montar_selecao_rodizio()
        self._montar_lista_resultado()

    # ---------- Seleção do rodízio ----------

    def _montar_selecao_rodizio(self):
        bloco = ctk.CTkFrame(self, border_width=1, border_color=theme.COR_BORDA)
        bloco.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            bloco, text="Resultado do Rodízio", font=theme.fonte_titulo()
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(20, 16))

        ctk.CTkLabel(
            bloco, text="Semana / Turno", font=theme.fonte_texto(),
            text_color=theme.COR_TEXTO_SECUNDARIO,
        ).grid(row=1, column=0, sticky="w", padx=20)

        self.option_rodizio = ctk.CTkOptionMenu(
            bloco, values=["—"], width=220, height=36,
            font=theme.fonte_texto(),
            command=self._ao_trocar_rodizio,
        )
        self.option_rodizio.grid(row=2, column=0, sticky="w", padx=20, pady=(4, 20))

        self.btn_gerar = ctk.CTkButton(
            bloco, text="Gerar Rodízio", height=36, font=theme.fonte_texto_bold(),
            command=self._gerar_ou_exibir,
        )
        self.btn_gerar.grid(row=2, column=1, sticky="w", padx=(0, 10), pady=(4, 20))

        self.btn_gerar_novamente = ctk.CTkButton(
            bloco, text="Gerar Novamente", height=36, font=theme.fonte_texto(),
            fg_color="transparent", border_width=1,
            border_color=theme.COR_BORDA, text_color=theme.COR_TEXTO_PRIMARIO,
            hover_color=theme.COR_SUPERFICIE_HOVER,
            command=self._gerar_novamente,
        )
        self.btn_gerar_novamente.grid(row=2, column=2, sticky="w", padx=(0, 10), pady=(4, 20))
        self.btn_gerar_novamente.grid_remove()

        self.btn_exportar = ctk.CTkButton(
            bloco, text="⬇  Exportar PDF", height=36, font=theme.fonte_texto(),
            fg_color="transparent", border_width=1,
            border_color=theme.COR_BORDA, text_color=theme.COR_TEXTO_PRIMARIO,
            hover_color=theme.COR_SUPERFICIE_HOVER,
            command=self._exportar_pdf,
        )
        self.btn_exportar.grid(row=2, column=3, sticky="w", pady=(4, 20))
        self.btn_exportar.grid_remove()

    def _recarregar_opcoes(self):
        """
        Recarrega a lista de rodízios salvos no dropdown. Chamado sempre
        que a tela é exibida, para refletir rodízios criados enquanto o
        usuário estava em outra tela (ex: acabou de salvar em "Nova
        Semana" e veio direto para cá).
        """
        rodizios = repository.listar_rodizios()

        self.rodizios_por_texto = {
            f"Semana {r['semana']} — Turno {r['turno']}": r["id"]
            for r in rodizios
        }

        textos = list(self.rodizios_por_texto.keys()) or ["—"]
        self.option_rodizio.configure(values=textos)

        # tenta preservar a seleção atual se ela ainda existir na lista;
        # senão volta pro primeiro item
        texto_atual = self.option_rodizio.get()
        if texto_atual not in self.rodizios_por_texto:
            self.option_rodizio.set(textos[0])

        self._ao_trocar_rodizio(self.option_rodizio.get())

    def _ao_trocar_rodizio(self, texto_selecionado: str):
        self.rodizio_selecionado_id = self.rodizios_por_texto.get(texto_selecionado)

        if self.rodizio_selecionado_id is not None:
            rodizio = repository.buscar_rodizio_por_id(self.rodizio_selecionado_id)
            self.rodizio_selecionado_semana = rodizio["semana"] if rodizio else None
            self.rodizio_selecionado_turno = rodizio["turno"] if rodizio else None

        self._atualizar_estado_botoes()
        self._atualizar_lista_resultado()

    def _atualizar_estado_botoes(self):
        if self.rodizio_selecionado_id is None:
            self.btn_gerar.configure(state="disabled")
            self.btn_gerar_novamente.grid_remove()
            self.btn_exportar.grid_remove()
            return

        self.btn_gerar.configure(state="normal")

        ja_gerado = repository.rodizio_tem_alocacoes(self.rodizio_selecionado_id)
        if ja_gerado:
            self.btn_gerar.configure(text="Já Gerado")
            self.btn_gerar.configure(state="disabled")
            self.btn_gerar_novamente.grid()
            self.btn_exportar.grid()
        else:
            self.btn_gerar.configure(text="Gerar Rodízio", state="normal")
            self.btn_gerar_novamente.grid_remove()
            self.btn_exportar.grid_remove()

    # ---------- Ação: gerar ----------

    def _gerar_ou_exibir(self):
        if self.rodizio_selecionado_id is None:
            return

        if repository.rodizio_tem_alocacoes(self.rodizio_selecionado_id):
            # já existe resultado salvo: só exibe, não gera de novo.
            self._atualizar_lista_resultado()
            return

        self._executar_geracao()

    def _gerar_novamente(self):
        if self.rodizio_selecionado_id is None:
            return

        confirmar = messagebox.askyesno(
            "Gerar novamente",
            "Isso vai apagar o resultado atual deste rodízio e recalcular "
            "a distribuição do zero. Deseja continuar?",
        )
        if not confirmar:
            return

        repository.limpar_alocacoes_rodizio(self.rodizio_selecionado_id)
        self._executar_geracao()

    def _executar_geracao(self):
        try:
            resumo = self.engine.gerar(self.rodizio_selecionado_id)
        except ValueError as erro:
            messagebox.showerror("Não foi possível gerar", str(erro))
            return

        if resumo["deficits"]:
            linhas = "\n".join(
                f"- {d['maquina_nome']}: faltaram {d['faltaram']} operador(es)"
                for d in resumo["deficits"]
            )
            messagebox.showwarning(
                "Rodízio gerado com déficit de pessoal",
                "O rodízio foi gerado, mas não havia funcionários suficientes "
                f"no turno para cobrir todas as máquinas:\n\n{linhas}",
            )
        else:
            messagebox.showinfo("Rodízio gerado", "Distribuição gerada e salva com sucesso.")

        self._atualizar_estado_botoes()
        self._atualizar_lista_resultado()

    # ---------- Ação: exportar PDF ----------

    def _exportar_pdf(self):
        if self.rodizio_selecionado_id is None:
            return

        alocacoes = repository.listar_alocacoes_rodizio(self.rodizio_selecionado_id)
        if not alocacoes:
            messagebox.showwarning("Nada para exportar", "Gere o rodízio antes de exportar.")
            return

        pasta_documentos = Path.home() / "Documents" / "Rodizios Gerados"
        nome_arquivo = f"rodizio_semana{self.rodizio_selecionado_semana}_turno{self.rodizio_selecionado_turno}.pdf"
        caminho_saida = pasta_documentos / nome_arquivo

        try:
            gerar_pdf_resultado(
                semana=self.rodizio_selecionado_semana,
                turno=self.rodizio_selecionado_turno,
                alocacoes=alocacoes,
                caminho_saida=str(caminho_saida),
            )
        except Exception as erro:
            messagebox.showerror("Erro ao exportar", f"Não foi possível gerar o PDF:\n{erro}")
            return

        resposta = messagebox.askyesno(
            "PDF gerado",
            f"Salvo em:\n{caminho_saida}\n\nDeseja abrir o arquivo agora?",
        )
        if resposta:
            self._abrir_arquivo(caminho_saida)

    def _abrir_arquivo(self, caminho: Path):
        """Abre o PDF no leitor padrão do sistema operacional."""
        try:
            if sys.platform.startswith("win"):
                os.startfile(caminho)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(caminho)], check=False)
            else:
                subprocess.run(["xdg-open", str(caminho)], check=False)
        except Exception:
            pass  # se não conseguir abrir automaticamente, o arquivo já está salvo

    # ---------- Lista de resultado ----------

    def _montar_lista_resultado(self):
        ctk.CTkLabel(
            self, text="Alocações", font=theme.fonte_subtitulo(),
        ).pack(anchor="w", pady=(0, 8))
        self.lista_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista_frame.pack(fill="both", expand=True)

    def _atualizar_lista_resultado(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        if self.rodizio_selecionado_id is None:
            ctk.CTkLabel(
                self.lista_frame,
                text="Cadastre uma programação em 'Nova Semana' primeiro.",
                font=theme.fonte_texto(), text_color=theme.COR_TEXTO_SECUNDARIO,
            ).pack(anchor="w", pady=5)
            return

        alocacoes = repository.listar_alocacoes_rodizio(self.rodizio_selecionado_id)

        if not alocacoes:
            ctk.CTkLabel(
                self.lista_frame,
                text="Este rodízio ainda não foi gerado. Clique em 'Gerar Rodízio'.",
                font=theme.fonte_texto(), text_color=theme.COR_TEXTO_SECUNDARIO,
            ).pack(anchor="w", pady=5)
            return

        # agrupa por máquina (rodizio_maquina_id), preservando a ordem em
        # que a programação foi cadastrada (chave None = kit, vai por último)
        grupos = {}
        ordem_grupos = []
        for aloc in alocacoes:
            chave = aloc["rodizio_maquina_id"]
            if chave not in grupos:
                grupos[chave] = []
                ordem_grupos.append(chave)
            grupos[chave].append(aloc)

        ordem_grupos.sort(key=lambda c: (c is None, c if c is not None else 0))

        for chave in ordem_grupos:
            itens_do_grupo = grupos[chave]
            eh_kit = chave is None
            eh_critica = (not eh_kit) and bool(itens_do_grupo[0].get("maquina_critica", 0))

            if eh_kit:
                cor_borda = theme.COR_KIT
            elif eh_critica:
                cor_borda = theme.COR_CRITICA
            else:
                cor_borda = theme.COR_BORDA

            bloco = ctk.CTkFrame(
                self.lista_frame, border_width=1, border_color=cor_borda,
                corner_radius=10,
            )
            bloco.pack(fill="x", pady=(0, 12))

            cabecalho = ctk.CTkFrame(bloco, fg_color="transparent", border_width=0)
            cabecalho.pack(fill="x", padx=16, pady=(14, 6))

            if eh_kit:
                titulo = f"Kit (excedente)"
            else:
                primeiro = itens_do_grupo[0]
                titulo = f"{primeiro['maquina_nome']}  —  {primeiro['produto_nome']}"

            ctk.CTkLabel(
                cabecalho, text=titulo, font=theme.fonte_subtitulo(),
                text_color=theme.COR_TEXTO_PRIMARIO,
            ).pack(side="left")

            if eh_critica:
                ctk.CTkLabel(
                    cabecalho, text="CRÍTICA", font=theme.fonte_pequena(),
                    text_color="#FFFFFF", fg_color=theme.COR_CRITICA,
                    corner_radius=6, padx=8, pady=2,
                ).pack(side="left", padx=(10, 0))

            ctk.CTkLabel(
                cabecalho, text=f"{len(itens_do_grupo)} funcionário(s)",
                font=theme.fonte_texto(), text_color=theme.COR_TEXTO_SECUNDARIO,
            ).pack(side="right")

            for aloc in itens_do_grupo:
                tem_restricao = aloc["restricao"] != "nenhuma"
                linha = ctk.CTkFrame(bloco, fg_color="transparent", border_width=0)
                linha.pack(fill="x", padx=16, pady=2)

                ctk.CTkLabel(
                    linha, text=f"•  {aloc['funcionario_nome']}",
                    font=theme.fonte_texto(), text_color=theme.COR_TEXTO_PRIMARIO,
                ).pack(side="left")

                if tem_restricao:
                    ctk.CTkLabel(
                        linha, text=aloc["restricao"], font=theme.fonte_pequena(),
                        text_color=theme.COR_RESTRICAO, fg_color=theme.COR_RESTRICAO_FUNDO,
                        corner_radius=6, padx=8, pady=1,
                    ).pack(side="left", padx=(8, 0))

            ctk.CTkFrame(bloco, height=8, fg_color="transparent", border_width=0).pack()

    # ---------- Chamado pela sidebar toda vez que a tela é exibida ----------

    def atualizar_ao_exibir(self):
        """
        Recarrega a lista de rodízios disponíveis e o resultado do
        rodízio atualmente selecionado, para refletir o que foi feito em
        'Nova Semana' enquanto esta tela estava em segundo plano.
        """
        self._recarregar_opcoes()