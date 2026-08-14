import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.database import init_db
from data import repositorio as repo
from data.ui_helpers import selo_legenda, nota_rodape_transparencia
from kpis import calculos as kpi

st.set_page_config(page_title="Comparativo entre UPAs — GestorUPA", page_icon="⚖️", layout="wide")
init_db()

st.title("⚖️ Comparativo entre UPAs")
selo_legenda([("Todos os KPIs comparados abaixo", "estimado")])

unidades = repo.listar_unidades()
atendimentos = repo.obter_atendimentos()
custeio = repo.obter_parametros_custeio()
orcamentos = repo.obter_orcamentos()

if unidades.empty or atendimentos.empty or custeio.empty:
    st.warning("Sem dados suficientes.")
    st.stop()

selecionadas = st.multiselect("Unidades para comparar", unidades["nome"].tolist(), default=unidades["nome"].tolist())
if len(selecionadas) < 2:
    st.info("Selecione ao menos duas unidades para comparar.")
    st.stop()

ids_sel = unidades.loc[unidades["nome"].isin(selecionadas), "id_unidade"].tolist()

custeio = custeio.copy()
custeio["custo_total"] = custeio.apply(
    lambda r: kpi.custo_total(
        r["custo_pessoal"], r["custo_medicamento"], r["custo_material"],
        r["custo_manutencao"], r["custo_administrativo"],
    ), axis=1,
)

base = custeio[custeio["id_unidade"].isin(ids_sel)].merge(
    atendimentos, on=["id_unidade", "periodo"], how="left"
).merge(
    unidades[["id_unidade", "nome", "capacidade_teorica_mensal", "nro_profissionais"]], on="id_unidade", how="left"
).merge(
    orcamentos[["id_unidade", "periodo", "valor_orcado"]], on=["id_unidade", "periodo"], how="left"
)

base["custo_por_atendimento"] = base.apply(lambda r: kpi.custo_por_atendimento(r["custo_total"], r["qtd_atendimentos"]), axis=1)
base["participacao_pessoal"] = base.apply(lambda r: kpi.participacao_custo_pessoal(r["custo_pessoal"], r["custo_total"]), axis=1)
base["produtividade"] = base.apply(lambda r: kpi.produtividade_por_profissional(r["qtd_atendimentos"], r["nro_profissionais"]), axis=1)
base["taxa_ocupacao"] = base.apply(lambda r: kpi.taxa_ocupacao(r["qtd_atendimentos"], r["capacidade_teorica_mensal"]), axis=1)
base["variacao_orcado"] = base.apply(lambda r: kpi.variacao_orcado_realizado(r["custo_total"], r["valor_orcado"]), axis=1)

agregado = base.groupby("nome", as_index=False).agg(
    custo_por_atendimento=("custo_por_atendimento", "mean"),
    participacao_pessoal=("participacao_pessoal", "mean"),
    produtividade=("produtividade", "mean"),
    taxa_ocupacao=("taxa_ocupacao", "mean"),
    variacao_orcado=("variacao_orcado", "mean"),
)

st.subheader("Tabela comparativa")
tabela = agregado.copy()
tabela["custo_por_atendimento"] = tabela["custo_por_atendimento"].apply(kpi.formatar_reais)
tabela["participacao_pessoal"] = tabela["participacao_pessoal"].apply(kpi.formatar_percentual)
tabela["produtividade"] = tabela["produtividade"].round(1)
tabela["taxa_ocupacao"] = tabela["taxa_ocupacao"].apply(kpi.formatar_percentual)
tabela["variacao_orcado"] = tabela["variacao_orcado"].apply(kpi.formatar_percentual)
tabela.columns = ["Unidade", "Custo/atendimento", "Participação custo pessoal", "Produtividade/profissional", "Taxa de ocupação", "Variação orçado x realizado"]
st.dataframe(tabela, width='stretch', hide_index=True)

st.divider()
st.subheader("Radar comparativo (KPIs normalizados 0-100)")

metricas = ["custo_por_atendimento", "participacao_pessoal", "produtividade", "taxa_ocupacao"]
rotulos = ["Custo/atend. (menor=melhor)", "Participação pessoal", "Produtividade", "Taxa de ocupação"]

norm = agregado.copy()
for m in metricas:
    minimo, maximo = norm[m].min(), norm[m].max()
    if pd.isna(minimo) or pd.isna(maximo) or maximo == minimo:
        norm[m + "_norm"] = 50.0
    else:
        norm[m + "_norm"] = (norm[m] - minimo) / (maximo - minimo) * 100
# custo por atendimento: menor é melhor -> inverte
norm["custo_por_atendimento_norm"] = 100 - norm["custo_por_atendimento_norm"]

fig = go.Figure()
for _, row in norm.iterrows():
    fig.add_trace(go.Scatterpolar(
        r=[row[m + "_norm"] for m in metricas],
        theta=rotulos,
        fill="toself",
        name=row["nome"],
    ))
fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
st.plotly_chart(fig, width='stretch')

nota_rodape_transparencia()
