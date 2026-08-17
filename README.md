# Sistema de Rodízio — MVP em desenvolvimento

## Como rodar
1. Instale as dependências:
   pip install -r requirements.txt
2. Rode o app:
   python3 main.py

Isso abre a janela principal com as telas já prontas: Funcionários,
Produtos, Máquinas e Nova Semana.

## Ver o fluxo de dados sem abrir a interface
python3 demo_fluxo_completo.py

Esse script simula um cadastro completo e a criação de uma semana,
usando as mesmas funções que a interface gráfica chama. Útil para
conferir a lógica sem precisar clicar em nada.

## Progresso
Etapas 1 a 5 concluídas (banco de dados, CRUD de Funcionários,
Produtos e Máquinas, e a tela Nova Semana que captura a programação
do PCP). A Etapa 6 — motor de geração automática do rodízio — ainda
não foi implementada.
