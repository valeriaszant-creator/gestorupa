import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import plotly.express as px
import streamlit as st

from data.database import init_db
from data import repositorio as repo
from data.ui_helpers import selo_legenda, nota_rodape_transparencia, alerta_planilha_sem_atendimentos
from kpis import calculos as kpi

st.set_page_config(page_title="Produtividade e Capacidade — GestorUPA", page_icon="📈", layout="wide")
init_db()

st.title("📈 Produtividade e Capacidade")
selo_legenda([
    ("Nº de profissionais e capacidade teórica", "estimado"),
    ("Volume de atendimentos", "estimado"),
])
alerta_planilha_sem_atendimentos()

unidades = repo.listar_unidades()
atendimentos = repo.obter_atendimentos()
if unidades.empty or atendimentos.empty:
    st.warning("Sem dados suficientes.")
    st.stop()

base = atendimentos.merge(
    unidades[["id_unidade", "nome", "capacidade_teorica_mensal", "nro_profissionais"]],
    on="id_unidade", how="left",
)
base["produtividade_por_profissional"] = base.apply(
    lambda r: kpi.produtividade_por_profissional(r["qtd_atendimentos"], r["nro_profissionais"]), axis=1
)
base["taxa_ocupacao"] = base.apply(
    lambda r: kpi.taxa_ocupacao(r["qtd_atendimentos"], r["capacidade_teorica_mensal"]), axis=1
)

st.subheader("Atendimentos por profissional")
fig1 = px.bar(
    base, x="periodo", y="produtividade_por_profissional", color="nome", barmode="group",
    labels={"periodo": "Período", "produtividade_por_profissional": "Atendimentos / profissional", "nome": "Unidade"},
)
st.plotly_chart(fig1, width='stretch')

st.divider()
st.subheader("Taxa de ocupação / capacidade")
fig2 = px.line(
    base, x="periodo", y="taxa_ocupacao", color="nome", markers=True,
    labels={"periodo": "Período", "taxa_ocupacao": "Taxa de ocupação", "nome": "Unidade"},
)
fig2.update_yaxes(tickformat=".0%")
fig2.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Capacidade teórica (100%)")
st.plotly_chart(fig2, width='stretch')

st.divider()
st.subheader("Mês de pico de demanda (por unidade)")
picos = base.loc[base.groupby("nome")["qtd_atendimentos"].idxmax()][["nome", "periodo", "qtd_atendimentos"]]
picos.columns = ["Unidade", "Período de pico", "Atendimentos no pico"]
st.dataframe(picos, width='stretch', hide_index=True)
st.caption(
    "📎 Baseado na série de atendimentos disponível no banco (100% estimada nesta "
    "versão do MVP, ver nota abaixo). Em produção, com dado real de atendimentos, "
    "este cálculo passaria a refletir sazonalidade real de demanda."
)

nota_rodape_transparencia()
