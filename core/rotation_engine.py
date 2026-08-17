"""
Motor de geração automática do rodízio.

Regra de negócio central (confirmada com o usuário do sistema):
funcionário com `restricao != 'nenhuma'` (gestante, física ou temporária)
NUNCA pode ser alocado em máquina `critica = True`. Em máquina não-crítica,
qualquer funcionário do turno pode entrar.

Estratégia do algoritmo — por que processar máquinas críticas primeiro:
o pool de funcionários "sem restrição" é o único que serve tanto para
máquinas críticas quanto não-críticas. Se distribuíssemos na ordem em
que a programação foi cadastrada, corremos o risco de gastar todos os
funcionários sem restrição em máquinas não-críticas (que também aceitariam
funcionários com restrição) e faltar gente sem restrição pra a máquina
crítica que vem depois na lista. Processar as críticas primeiro garante
que elas tenham prioridade sobre o recurso mais escasso.

Nenhum SQL é escrito aqui: toda leitura e escrita passa pelo repository.
"""

from database import repository


class RotationEngine:
    """
    Responsável por gerar automaticamente o rodízio de uma semana.

    Toda a lógica de negócio fica nesta classe.
    Nenhum SQL deve ser escrito aqui: todo acesso ao banco passa
    pelo repository.
    """

    def gerar(self, rodizio_id: int) -> dict:
        """
        Gera e SALVA todas as alocações de um rodízio.

        Não verifica se o rodízio já foi gerado antes — quem decide se é
        hora de gerar (ou de gerar de novo, limpando o que existia) é a
        tela, via `repository.rodizio_tem_alocacoes`. Isso mantém o
        engine focado só na lógica de distribuição.

        Retorna um resumo (dict) para a tela poder avisar o usuário sobre
        máquinas que ficaram com déficit de operadores:
            {
                "alocados_maquina": int,
                "alocados_kit": int,
                "deficits": [ {"maquina_nome": str, "faltaram": int}, ... ],
            }
        """
        rodizio = repository.buscar_rodizio_por_id(rodizio_id)
        if rodizio is None:
            raise ValueError("Rodízio não encontrado.")

        programacao = repository.listar_rodizio_maquinas(rodizio_id)
        funcionarios = repository.listar_funcionarios_turno(rodizio["turno"])

        # Dois grupos: quem não tem restrição pode ir para qualquer máquina;
        # quem tem restrição só pode ir para máquina não-crítica.
        sem_restricao = [f for f in funcionarios if f.restricao == "nenhuma"]
        com_restricao = [f for f in funcionarios if f.restricao != "nenhuma"]

        # Críticas primeiro: são as únicas que dependem exclusivamente do
        # pool "sem_restricao", então têm prioridade sobre esse recurso.
        programacao_ordenada = sorted(
            programacao, key=lambda item: not item["maquina_critica"]
        )

        deficits = []
        total_alocados_maquina = 0

        for item in programacao_ordenada:
            necessario = item["qtd_operadores"]

            if item["maquina_critica"]:
                candidatos = sem_restricao
            else:
                # não-crítica: prioriza quem tem restrição primeiro, para
                # preservar funcionários sem restrição disponíveis para
                # outras máquinas críticas ainda não processadas nesta
                # mesma rodada.
                candidatos = com_restricao + sem_restricao

            selecionados = candidatos[:necessario]

            for funcionario in selecionados:
                repository.criar_alocacao(
                    rodizio_id=rodizio_id,
                    rodizio_maquina_id=item["id"],
                    funcionario_id=funcionario.id,
                    destino="maquina",
                )
                # remove o funcionário alocado de QUALQUER pool em que ele
                # esteja, para não ser escalado duas vezes.
                if funcionario in sem_restricao:
                    sem_restricao.remove(funcionario)
                if funcionario in com_restricao:
                    com_restricao.remove(funcionario)

            total_alocados_maquina += len(selecionados)

            if len(selecionados) < necessario:
                deficits.append({
                    "maquina_nome": item["maquina_nome"],
                    "faltaram": necessario - len(selecionados),
                })

        # Quem sobrou (de qualquer pool) vai para o "kit" — excedente do
        # turno, sem máquina associada.
        excedente = sem_restricao + com_restricao
        for funcionario in excedente:
            repository.criar_alocacao(
                rodizio_id=rodizio_id,
                rodizio_maquina_id=None,
                funcionario_id=funcionario.id,
                destino="kit",
            )

        return {
            "alocados_maquina": total_alocados_maquina,
            "alocados_kit": len(excedente),
            "deficits": deficits,
        }