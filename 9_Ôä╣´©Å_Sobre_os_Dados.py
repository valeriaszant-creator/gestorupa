import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from data.database import init_db
from data import repositorio as repo

st.set_page_config(page_title="Sobre os Dados — GestorUPA", page_icon="ℹ️", layout="wide")
init_db()

st.title("ℹ️ Sobre os Dados")

st.markdown("""
O GestorUPA foi projetado com uma regra inegociável de transparência: **todo
número mostrado no painel precisa deixar claro se é dado real ou estimativa
metodológica.** Esta página documenta, com o máximo de detalhe, a origem de
cada tabela do banco de dados.
""")

st.subheader("⚠️ Divergência entre a arquitetura original e a planilha oficial")
st.warning(
    "O documento de arquitetura deste projeto previa a importação de uma série "
    "de **atendimentos pediátricos por unidade** a partir de uma aba "
    "'Atendimentos por Bairro'. A planilha oficial efetivamente entregue "
    "(`base_upas_feira_de_santana.xlsx`) é, na verdade, um modelo de **repasses "
    "financeiros** (municipal/estadual/federal) às UPAs de Feira de Santana, "
    "sem nenhuma série de atendimentos. Por decisão explícita do usuário, a "
    "arquitetura original (8 páginas, KPIs de custo por atendimento, "
    "produtividade, ocupação etc.) foi mantida, e os dados de atendimento "
    "foram **100% simulados** para viabilizar o MVP — nunca apresentados como "
    "reais em nenhuma tela."
)

st.subheader("📋 Origem de cada tabela do banco de dados")
tabela_origem = [
    ("unidade", "Cadastro das UPAs (nome, bairro, natureza de gestão, CNES/CNPJ)", "REAL",
     "Aba dim_UPA da planilha oficial (fontes: CNES-DATASUS, SESAB, reportagens sobre contratos de gestão)."),
    ("unidade", "Porte, capacidade teórica e nº de profissionais (quando não confirmado no CNES)", "ESTIMADO",
     "Referência técnica por porte (Portaria GM/MS nº 3.134/2020), aplicada quando a planilha não confirma o dado."),
    ("repasse_financeiro (extra)", "Lançamentos financeiros efetivos", "REAL",
     "Aba Fato_Repasses da planilha oficial — apenas linhas com valor efetivamente localizado em fonte pública."),
    ("atendimento_mensal", "Quantidade de atendimentos por unidade/período", "ESTIMADO",
     "A planilha oficial não contém esta série. Gerado por função parametrizada (±15% em torno de referência por porte)."),
    ("parametro_custeio", "Custos de pessoal, medicamento, material, manutenção, administrativo", "ESTIMADO",
     "Valor-base por porte (estrutura típica de custeio de UPA 24h) com variação aleatória controlada de ±15%."),
    ("orcamento", "Valor orçado por unidade/período", "ESTIMADO",
     "Igual à soma dos parâmetros de custeio estimados do período, sem folga orçamentária adicional (premissa simplificadora do MVP)."),
    ("classificacao_risco", "Distribuição de atendimentos por categoria de risco", "ESTIMADO",
     "Proporções típicas do Protocolo de Manchester aplicadas sobre o volume estimado de atendimentos."),
]
st.table(
    [{"Tabela": t, "Campo(s)": c, "Origem": o, "Metodologia/Fonte": f} for t, c, o, f in tabela_origem]
)

st.subheader("📊 Situação atual do banco de dados")
unidades = repo.listar_unidades()
repasses = repo.obter_repasses_reais()
atendimentos = repo.obter_atendimentos()
st.metric("Unidades cadastradas (real)", len(unidades))
st.metric("Lançamentos financeiros reais importados", len(repasses))
st.metric("Registros de atendimento (100% estimados)", len(atendimentos))

st.caption(
    "Este projeto é um MVP acadêmico de Pós-Graduação em Contabilidade Gerencial. "
    "Nenhum dado de paciente individual, nome, CPF ou prontuário existe em "
    "qualquer tabela — o app trabalha exclusivamente com dados agregados por "
    "unidade/período/categoria."
)
