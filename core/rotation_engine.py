"""
Motor de geração automática do rodízio.

Regras de negócio (confirmadas com o usuário do sistema):

1. Funcionário com `restricao != 'nenhuma'` (gestante, física ou
   temporária) NUNCA pode ser alocado em máquina `critica = True`. Em
   máquina não-crítica, qualquer funcionário do turno pode entrar.

2. ROTAÇÃO / JUSTIÇA NA ESCALA: o sistema tem memória do que já foi
   gerado antes (consulta a tabela `alocacoes` de todos os rodízios
   anteriores). Ao escolher quem vai pra cada máquina:
     - Para máquinas CRÍTICAS: todo mundo elegível (sem restrição) é
       ordenado por "há quanto tempo não pega QUALQUER máquina crítica"
       — quem nunca pegou vai primeiro; entre quem já pegou, quem pegou
       há mais tempo vai na frente de quem pegou recentemente. Isso
       cria uma fila justa naturalmente: ninguém repete crítica duas
       vezes seguidas a não ser que literalmente não sobre mais
       ninguém elegível (situação real de escassez de pessoal).
     - Para máquinas NÃO-críticas: mesma lógica, mas por máquina
       específica — prioriza quem nunca trabalhou NAQUELA máquina, ou
       que trabalhou há mais tempo.

   Não existe um "banimento permanente" de repetir — com poucas pessoas
   elegíveis e muitas vagas críticas por rodízio, um "nunca mais"
   literal esgotaria a fila em 2-3 gerações e travaria o sistema. Por
   isso a prioridade é por RECÊNCIA (quem está há mais tempo sem
   passar), não uma regra rígida de "só uma vez na vida".

Nenhum SQL é escrito aqui: toda leitura e escrita passa pelo repository.
"""

from database import repository


# Funcionários que nunca apareceram no histórico recebem esta "data",
# que é anterior a qualquer timestamp real do banco — garante que eles
# fiquem sempre à frente na fila de prioridade (nunca pegaram = máxima
# prioridade para pegar agora).
NUNCA_ALOCADO = ""


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

        turno = rodizio["turno"]
        programacao = repository.listar_rodizio_maquinas(rodizio_id)
        funcionarios = repository.listar_funcionarios_turno(turno)

        # Histórico: quando cada funcionário passou por último em
        # QUALQUER máquina crítica, e em CADA máquina específica.
        # Consultado uma vez só, no início — não muda durante a geração
        # deste rodízio (o histórico é sempre de rodízios ANTERIORES).
        historico_critica = repository.historico_ultima_maquina_critica(turno)
        historico_por_maquina = repository.historico_ultima_vez_por_maquina(turno)

        # Dois grupos: quem não tem restrição pode ir para qualquer
        # máquina; quem tem restrição só pode ir para máquina não-crítica.
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
                candidatos = sorted(
                    sem_restricao,
                    key=lambda f: historico_critica.get(f.id, NUNCA_ALOCADO),
                )
            else:
                # não-crítica: prioriza quem tem restrição primeiro (para
                # preservar sem-restrição para outras críticas ainda não
                # processadas), mas dentro de cada grupo, ordena por
                # rotação — quem passou há mais tempo por ESTA máquina
                # específica (ou nunca passou) vai na frente.
                def chave_rotacao_maquina(funcionario):
                    return historico_por_maquina.get(
                        (funcionario.id, item["maquina_id"]), NUNCA_ALOCADO
                    )

                candidatos = sorted(com_restricao, key=chave_rotacao_maquina) + sorted(
                    sem_restricao, key=chave_rotacao_maquina
                )

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