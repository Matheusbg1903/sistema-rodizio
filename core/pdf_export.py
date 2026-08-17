"""
Geração do PDF de resultado do rodízio — para impressão e afixação no
mural da fábrica.

Não depende de nenhuma tela: recebe dados já prontos (a mesma estrutura
que vem de repository.listar_alocacoes_rodizio) e devolve o caminho do
PDF gerado. Isso mantém a lógica de exportação reaproveitável, caso no
futuro se queira gerar o PDF por outro caminho (ex: agendado, por
e-mail) sem depender da UI.
"""

from datetime import datetime
from pathlib import Path

from fpdf import FPDF


def gerar_pdf_resultado(semana: int, turno: int, alocacoes: list[dict], caminho_saida: str) -> str:
    """
    Gera um PDF com o resultado do rodízio, agrupado por máquina (igual
    à tela), pronto para impressão em papel A4.

    alocacoes: lista de dicts no formato de
        repository.listar_alocacoes_rodizio() — cada um com
        rodizio_maquina_id, maquina_nome, produto_nome, funcionario_nome,
        restricao, destino.

    Retorna o caminho final do arquivo gerado.
    """
    # agrupa por máquina, mesma lógica usada na tela
    grupos = {}
    ordem_grupos = []
    for aloc in alocacoes:
        chave = aloc["rodizio_maquina_id"]
        if chave not in grupos:
            grupos[chave] = []
            ordem_grupos.append(chave)
        grupos[chave].append(aloc)
    ordem_grupos.sort(key=lambda c: (c is None, c if c is not None else 0))

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Cabeçalho
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(31, 36, 48)
    pdf.cell(0, 10, "Resultado do Rodizio", ln=True)

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 7, f"Semana {semana}  -  Turno {turno}", ln=True)
    pdf.cell(0, 6, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(4)
    pdf.set_draw_color(228, 230, 236)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)

    for chave in ordem_grupos:
        itens = grupos[chave]

        if chave is None:
            titulo = f"Kit (excedente) - {len(itens)} funcionario(s)"
            cor_titulo = (107, 114, 128)
        else:
            primeiro = itens[0]
            titulo = f"{primeiro['maquina_nome']}  -  {primeiro['produto_nome']}  ({len(itens)} funcionario(s))"
            cor_titulo = (31, 36, 48)

        # evita começar um bloco colado no fim da página
        if pdf.get_y() > 260:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*cor_titulo)
        pdf.cell(0, 9, titulo, ln=True)

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(31, 36, 48)
        for aloc in itens:
            linha = f"    -  {aloc['funcionario_nome']}"
            if aloc["restricao"] != "nenhuma":
                linha += f"   ({aloc['restricao']})"
            pdf.cell(0, 7, linha, ln=True)

        pdf.ln(4)

    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)
    pdf.output(caminho_saida)
    return caminho_saida