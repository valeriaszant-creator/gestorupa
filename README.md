# GestorUPA — Painel de Custeio e Decisão

> *"Cada atendimento tem um custo. Aqui você enxerga qual é — e o que fazer com isso."*

MVP de um aplicativo de Contabilidade Gerencial + BI para gestão de UPAs
(Unidades de Pronto Atendimento) públicas, desenvolvido como projeto acadêmico
de Pós-Graduação em Contabilidade Gerencial.

---

## ⚠️ Nota importante sobre a origem dos dados — leia antes de tudo

O documento de arquitetura original deste projeto previa a importação de uma
série de **atendimentos pediátricos por unidade**, a partir de uma planilha
com abas "Base de Dados" e "Atendimentos por Bairro".

A planilha oficial efetivamente fornecida (`base_upas_feira_de_santana.xlsx`)
é, na prática, um **modelo de repasses financeiros** (municipal/estadual/
federal) às UPAs de Feira de Santana/BA — um modelo estrela com `dim_UPA`,
`dim_Fonte_Recurso`, `dim_Bloco_Financiamento`, `dim_Categoria_Despesa` e
`Fato_Repasses`. Ela **não contém nenhuma série de atendimentos**, e a própria
aba "Leia-me" da planilha esclarece que a maior parte da tabela fato é um
**modelo para preenchimento manual futuro** pela equipe gestora — apenas 8
lançamentos têm valor real localizado em fontes públicas.

Diante dessa divergência, e por decisão explícita do solicitante, optou-se por:

1. **Manter a arquitetura original** (8 páginas, KPIs de custo por atendimento,
   produtividade, ocupação etc.);
2. **Importar como dado REAL** apenas o que a planilha de fato contém: o
   cadastro das 3 unidades (`dim_UPA`) e os 8 lançamentos financeiros
   efetivamente preenchidos (`Fato_Repasses`);
3. **Gerar como dado 100% ESTIMADO** (nunca apresentado como real) a série de
   atendimentos, os parâmetros de custeio, o orçamento e a classificação de
   risco — por função parametrizada, com variação aleatória controlada de
   ±15% em torno de referências por porte de unidade, documentadas em
   `data/config_estimativas.py`.

Essa distinção é sinalizada em **toda tela** do aplicativo por meio de selos
de origem do dado, e está detalhada na página **"Sobre os Dados"** do próprio
app. Veja também o cabeçalho de `data/models.py` e `data/importacao.py`.

---

## Como rodar localmente

### 1. Pré-requisitos
- Python 3.10 ou superior

### 2. Instalação

```bash
cd gestorupa
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Executar

```bash
streamlit run app.py
```

O app abre em `http://localhost:8501`. **Na primeira execução**, o banco
SQLite (`gestorupa.db`) é criado e populado automaticamente a partir da
planilha `base_upas_feira_de_santana.xlsx` (já incluída na raiz do projeto) —
não é necessário nenhum passo manual de importação.

Para forçar uma nova importação (ex.: após editar a planilha ou os parâmetros
de estimativa), apague `gestorupa.db` e recarregue a página, ou rode:

```bash
python -m data.importacao base_upas_feira_de_santana.xlsx
```

### 4. Rodar os testes

```bash
pytest tests/ -v
```

---

## Estrutura do projeto

```
gestorupa/
├── app.py                     # Página 1 — Visão Geral (entrada do Streamlit)
├── base_upas_feira_de_santana.xlsx   # Planilha oficial (dado real)
├── requirements.txt
├── .streamlit/config.toml     # Tema visual
├── data/
│   ├── database.py            # Engine/sessão SQLAlchemy (SQLite → Postgres/Supabase sem reescrever lógica)
│   ├── models.py               # Tabelas: unidade, atendimento_mensal, parametro_custeio,
│   │                           #   orcamento, classificacao_risco, repasse_financeiro (extra)
│   ├── config_estimativas.py  # Premissas declaradas de toda estimativa (nunca números soltos)
│   ├── importacao.py          # Importação real (unidades + repasses) + geração parametrizada do estimado
│   ├── repositorio.py         # Camada de consulta (DataFrames para as páginas)
│   └── ui_helpers.py          # Selo de origem do dado, nota de rodapé de transparência
├── kpis/
│   └── calculos.py            # As 10 fórmulas do documento de arquitetura, como funções puras testáveis
├── simulador/
│   └── cenarios.py            # Lógica do Simulador de Cenários (Página 7)
├── pages/
│   ├── 2_💰_Custos.py
│   ├── 3_📈_Produtividade_e_Capacidade.py
│   ├── 4_🩺_Atendimentos.py
│   ├── 5_⚖️_Comparativo_entre_UPAs.py
│   ├── 6_💵_Orcado_x_Realizado.py
│   ├── 7_🎛️_Simulador_de_Cenarios.py
│   ├── 8_📄_Relatorios.py
│   └── 9_ℹ️_Sobre_os_Dados.py   # Página extra: detalhamento completo da origem dos dados
└── tests/
    └── test_kpis.py            # 19 testes unitários das funções de KPI e do simulador
```

## Modelo de dados

Implementado exatamente conforme o documento de arquitetura (`unidade`,
`atendimento_mensal`, `parametro_custeio`, `orcamento`, `classificacao_risco`),
com uma tabela adicional `repasse_financeiro` para armazenar o dado financeiro
real da planilha oficial (usado na Página 6 — Orçado x Realizado). Toda tabela
que mistura dado real e estimado tem o campo `origem_dado`.

## Privacidade

Nenhum dado de paciente individual (nome, CPF, prontuário) existe em nenhuma
tabela ou tela — o app trabalha apenas com dados agregados por unidade,
período e categoria.

## Migração futura para Postgres/Supabase

Basta alterar `DATABASE_URL` em `data/database.py`. Nenhuma lógica de negócio
em `kpis/`, `pages/` ou `simulador/` depende do dialeto do banco, pois todo
acesso passa pela camada SQLAlchemy em `data/`.
