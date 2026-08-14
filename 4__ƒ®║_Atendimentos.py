import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.express as px
import streamlit as st

from data.database import init_db
from data import repositorio as repo
from data.ui_helpers import selo_legenda, nota_rodape_transparencia, alerta_planilha_sem_atendimentos

st.set_page_config(page_title="Atendimentos — GestorUPA", page_icon="🩺", layout="wide")
init_db()

st.title("🩺 Atendimentos")
selo_legenda([("Série de atendimentos", "estimado")])
alerta_planilha_sem_atendimentos()

unidades = repo.listar_unidades()
atendimentos = repo.obter_atendimentos()
if unidades.empty or atendimentos.empty:
    st.warning("Sem dados suficientes.")
    st.stop()

opcoes = ["Todas as unidades"] + unidades["nome"].tolist()
filtro = st.selectbox("Filtrar por unidade", opcoes)

base = atendimentos.merge(unidades[["id_unidade", "nome"]], on="id_unidade", how="left").sort_values("periodo")
if filtro != "Todas as unidades":
    base = base[base["nome"] == filtro]

fig = px.line(
    base, x="periodo", y="qtd_atendimentos", color="nome", markers=True,
    labels={"periodo": "Período", "qtd_atendimentos": "Atendimentos", "nome": "Unidade"},
    title="Série histórica de atendimentos",
)
st.plotly_chart(fig, width='stretch')

st.subheader("Tabela de dados")
tabela = base[["nome", "periodo", "qtd_atendimentos", "origem_dado"]].rename(columns={
    "nome": "Unidade", "periodo": "Período", "qtd_atendimentos": "Atendimentos", "origem_dado": "Origem do dado",
})
st.dataframe(tabela, width='stretch', hide_index=True)

st.warning(
    "⚠️ **Diferente do previsto originalmente na arquitetura do produto**, a série "
    "de atendimentos não pôde ser importada como dado real: a planilha oficial "
    "fornecida para este MVP contém repasses financeiros, não atendimentos por "
    "unidade. Todos os valores acima são estimativas metodológicas (ver coluna "
    "'Origem do dado' e a página 'Sobre os Dados')."
)

nota_rodape_transparencia()
