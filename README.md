# Sistema de Rodízio de Funcionários

Aplicação desktop que gera automaticamente a escala semanal de operadores entre as máquinas de uma fábrica de plásticos, respeitando restrições dos funcionários e distribuindo as máquinas críticas de forma justa.

Em uso na Plastilânia: o rodízio de cerca de 300 funcionários, que levava **2 horas por ciclo** para ser montado, passou a levar **30 minutos**.

<!-- Adicione aqui um print da tela de Resultado, por exemplo: ![Tela de resultado](docs/resultado.png) -->

## Funcionalidades

- Cadastro de **funcionários** (turno e restrição), **produtos** (nível de dificuldade) e **máquinas** (críticas ou não, incluindo máquinas compostas, como "12-24")
- **Programação semanal** do PCP: quais máquinas vão rodar, com qual produto e quantos operadores
- **Geração automática** do rodízio por turno, com aviso quando faltam operadores para alguma máquina
- **Exportação em PDF** (A4), pronta para imprimir e afixar no mural da fábrica
- **Executável para Windows** (.exe), sem precisar instalar Python

## Como o rodízio é gerado

1. Funcionários com restrição (gestante, física ou temporária) **nunca** são alocados em máquinas críticas.
2. As máquinas críticas são preenchidas primeiro, priorizando quem está **há mais tempo sem pegar uma máquina crítica**.
3. Nas máquinas não críticas, a prioridade é de quem está há mais tempo sem passar **por aquela máquina específica**.
4. Quem sobra no turno vai para o "kit" (excedente, sem máquina).

O sistema guarda o histórico de todos os rodízios anteriores. A prioridade é por tempo desde a última vez, e não por uma proibição rígida de repetir: com poucos funcionários elegíveis, uma regra de "nunca repetir" travaria a escala em poucas semanas.

## Arquitetura

O código é separado em camadas, e cada uma só conversa com a de baixo:

```
ui/  (telas em CustomTkinter)
 └── core/rotation_engine.py   regras de negócio do rodízio, sem nenhum SQL
      └── database/repository.py   todas as consultas ao banco
           └── database/db.py      criação das tabelas (SQLite)
models/entities.py   entidades do domínio (dataclasses)
core/pdf_export.py   geração do PDF, independente da interface
```

## Tecnologias

Python 3 · SQLite · CustomTkinter · fpdf2 · PyInstaller

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

O banco `rodizio.db` é criado automaticamente na primeira execução.

**Dados de exemplo** (funcionários, máquinas e uma semana já programada):

```bash
python -m scripts.gerar_dados_teste
```

**Gerar o executável** (Windows): rode `build_exe.bat`. O arquivo sai em `dist/SistemaRodizio.exe`.
