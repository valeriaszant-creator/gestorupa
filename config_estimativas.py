"""
Premissas e parâmetros-base para geração de dados ESTIMADOS.

Todo valor aqui é uma premissa declarada (não um número solto). Sempre que um
gerador usa um destes valores-base, ele grava em `fonte`/`fonte_dado` a
premissa efetivamente usada, para auditoria.

Metodologia declarada:
- Custos mensais de referência por Porte de UPA, com base na estrutura de
  custeio típica de UPA 24h descrita na Portaria GM/MS nº 3.134/2020 (parâmetros
  de porte e habilitação de UPA) e em relatórios de gestão de OSS de saúde
  publicados no período 2023-2025. Os valores abaixo são ESTIMATIVAS DIDÁTICAS
  para fins do MVP acadêmico — não substituem o custeio real informado pela
  unidade — e recebem variação aleatória controlada de ±15% por período.
- Capacidade teórica mensal: Porte II com capacidade declarada de até 4.500
  atendimentos/mês (fonte: dim_UPA da planilha oficial, UPA Queimadinha).
  Para portes sem valor declarado, aplica-se a referência técnica de portaria
  (Porte I ≈ 2.900/mês, Porte II ≈ 4.500/mês, Porte III ≈ 6.750/mês).
"""

VARIACAO_PADRAO = 0.15  # ±15%, conforme item 5 do documento de arquitetura

# Custo mensal-base (R$) por categoria, por porte da unidade — premissa didática.
CUSTO_BASE_POR_PORTE = {
    "Porte I": {
        "custo_pessoal": 480_000.0,
        "custo_medicamento": 90_000.0,
        "custo_material": 70_000.0,
        "custo_manutencao": 25_000.0,
        "custo_administrativo": 60_000.0,
    },
    "Porte II": {
        "custo_pessoal": 780_000.0,
        "custo_medicamento": 150_000.0,
        "custo_material": 115_000.0,
        "custo_manutencao": 40_000.0,
        "custo_administrativo": 95_000.0,
    },
    "Porte III": {
        "custo_pessoal": 1_150_000.0,
        "custo_medicamento": 230_000.0,
        "custo_material": 175_000.0,
        "custo_manutencao": 60_000.0,
        "custo_administrativo": 140_000.0,
    },
}

# Classificação fixo/variável por categoria de custo — premissa contábil padrão
# de custeio hospitalar (pessoal e manutenção predial tratados como fixos no
# curto prazo; medicamento, material e administrativo variam com o volume).
TIPO_CUSTO = {
    "custo_pessoal": "fixo",
    "custo_medicamento": "variável",
    "custo_material": "variável",
    "custo_manutencao": "fixo",
    "custo_administrativo": "variável",
}

# Capacidade teórica mensal de referência por porte (atendimentos/mês),
# conforme parâmetros técnicos de habilitação de UPA (Portaria GM/MS nº 3.134/2020).
CAPACIDADE_TEORICA_POR_PORTE = {
    "Porte I": 2_900,
    "Porte II": 4_500,  # confirmado na planilha oficial para UPA Queimadinha
    "Porte III": 6_750,
}

# Atendimentos/mês de referência (valor-base p/ geração simulada), coerente
# com a capacidade teórica de cada porte, assumindo ocupação típica de 70-85%.
ATENDIMENTOS_BASE_POR_PORTE = {
    "Porte I": 2_200,
    "Porte II": 3_400,
    "Porte III": 5_200,
}

# Número de profissionais de referência por porte (equipe assistencial +
# administrativa em escala, premissa didática baseada em dimensionamento
# habitual de UPA 24h por porte).
PROFISSIONAIS_POR_PORTE = {
    "Porte I": 45,
    "Porte II": 70,
    "Porte III": 100,
}

# Distribuição de classificação de risco (protocolo de Manchester) — premissa
# padrão de literatura de triagem em UPAs: maioria em amarelo/verde, minoria
# em vermelho (emergência) e azul (não-urgente).
DISTRIBUICAO_RISCO = {
    "vermelho": 0.03,
    "amarelo": 0.27,
    "verde": 0.55,
    "azul": 0.15,
}

PERIODOS_SIMULADOS = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]

FONTE_CUSTEIO_PADRAO = (
    "Estimativa metodológica GestorUPA: valor-base por porte (ref. estrutura de "
    "custeio de UPA 24h / Portaria GM/MS nº 3.134/2020) com variação aleatória "
    "controlada de ±15% por período. Não é valor de execução orçamentária real."
)

FONTE_ATENDIMENTO_PADRAO = (
    "Estimativa metodológica GestorUPA: a planilha oficial fornecida não contém "
    "série de atendimentos por unidade (contém apenas repasses financeiros). "
    "Valor gerado a partir de referência de capacidade por porte, com variação "
    "aleatória controlada de ±15% por período, apenas para viabilizar o MVP."
)

FONTE_RISCO_PADRAO = (
    "Estimativa metodológica GestorUPA: distribuição de classificação de risco "
    "baseada em proporções típicas do Protocolo de Manchester para UPAs, aplicada "
    "sobre o volume estimado de atendimentos do período."
)

FONTE_ORCAMENTO_PADRAO = (
    "Estimativa metodológica GestorUPA: orçamento mensal de referência = soma dos "
    "parâmetros de custeio estimados do período, sem folga orçamentária adicional."
)
