import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.express as px
import streamlit as st

from data.database import init_db
from data import repositorio as repo
from data.ui_helpers import selo_legenda, nota_rodape_transparencia
from kpis import calculos as kpi

st.set_page_config(page_title="Custos — GestorUPA", page_icon="💰", layout="wide")
init_db()

st.title("💰 Custos")
selo_legenda([
    ("Composição e evolução dos custos", "estimado"),
    ("Volume de atendimentos usado no cálculo", "estimado"),
])

unidades = repo.listar_unidades()
if unidades.empty:
    st.warning("Nenhuma unidade cadastrada.")
    st.stop()

col_a, col_b = st.columns(2)
nome_unidade = col_a.selectbox("Unidade", unidades["nome"].tolist())
id_unidade = int(unidades.loc[unidades["nome"] == nome_unidade, "id_unidade"].iloc[0])

periodos = repo.periodos_disponiveis()
periodo_sel = col_b.selectbox("Período", periodos, index=len(periodos) - 1 if periodos else 0)

custeio = repo.obter_parametros_custeio(id_unidade=id_unidade)
atendimentos = repo.obter_atendimentos(id_unidade=id_unidade)
risco = repo.obter_classificacao_risco(id_unidade=id_unidade)

if custeio.empty:
    st.info("Sem parâmetros de custeio para esta unidade.")
    st.stop()

custeio["custo_total"] = custeio.apply(
    lambda r: kpi.custo_total(
        r["custo_pessoal"], r["custo_medicamento"], r["custo_material"],
        r["custo_manutencao"], r["custo_administrativo"],
    ), axis=1,
)
custeio_periodo = custeio[custeio["periodo"] == periodo_sel]

st.divider()
st.subheader(f"Composição do custo por categoria — {nome_unidade}, {periodo_sel}")

if not custeio_periodo.empty:
    row = custeio_periodo.iloc[0]
    categorias = repo.CATEGORIAS_CUSTO
    df_comp = pd.DataFrame({
        "Categoria": [label for _, label in categorias],
        "Valor (R$)": [row[campo] for campo, _ in categorias],
    })
    fig_pizza = px.pie(df_comp, names="Categoria", values="Valor (R$)", hole=0.45,
                        title="Distribuição do custo total por categoria")
    st.plotly_chart(fig_pizza, width='stretch')

    st.caption(f"📎 Fonte/premissa da estimativa: {row['fonte']}")
else:
    st.info("Sem dado de custeio para o período selecionado.")

st.divider()
st.subheader("Custo por atendimento ao longo do tempo")

serie = custeio.merge(atendimentos, on=["id_unidade", "periodo"], how="left").sort_values("periodo")
serie["custo_por_atendimento"] = serie.apply(
    lambda r: kpi.custo_por_atendimento(r["custo_total"], r["qtd_atendimentos"]), axis=1
)
fig_linha = px.line(
    serie, x="periodo", y="custo_por_atendimento", markers=True,
    labels={"periodo": "Período", "custo_por_atendimento": "Custo por atendimento (R$)"},
)
st.plotly_chart(fig_linha, width='stretch')

st.divider()
st.subheader("Custo por classificação de risco")

if not risco.empty and not custeio_periodo.empty:
    risco_periodo = risco[risco["periodo"] == periodo_sel].copy()
    custo_total_periodo = custeio_periodo.iloc[0]["custo_total"]
    total_atend_categorias = risco_periodo["qtd_estimada"].sum()
    # Aloca o custo total do período proporcionalmente ao volume de cada categoria
    # de risco (premissa: custo acompanha volume de atendimento por categoria).
    risco_periodo["custo_alocado"] = risco_periodo["qtd_estimada"].apply(
        lambda q: kpi.custo_por_atendimento(custo_total_periodo, total_atend_categorias) * q
        if total_atend_categorias else None
    )
    risco_periodo["custo_por_atendimento_categoria"] = risco_periodo.apply(
        lambda r: kpi.custo_por_classificacao_risco(r["custo_alocado"], r["qtd_estimada"]), axis=1
    )
    fig_risco = px.bar(
        risco_periodo, x="categoria_risco", y="custo_por_atendimento_categoria",
        labels={"categoria_risco": "Classificação de risco", "custo_por_atendimento_categoria": "Custo por atendimento (R$)"},
        color="categoria_risco",
        color_discrete_map={"vermelho": "#C0392B", "amarelo": "#D4AC0D", "verde": "#1E8449", "azul": "#2E86C1"},
    )
    st.plotly_chart(fig_risco, width='stretch')
    st.caption(
        "📎 Premissa: o custo total do período é alocado proporcionalmente ao "
        "volume estimado de atendimentos de cada categoria de risco (protocolo "
        "de Manchester). Não há rastreio de custo direto por paciente/categoria."
    )
else:
    st.info("Sem dado de classificação de risco para o período selecionado.")

nota_rodape_transparencia()
