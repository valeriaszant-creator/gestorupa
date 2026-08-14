"""
GestorUPA — Painel de Custeio e Decisão
Página 1 — Visão Geral

"Cada atendimento tem um custo. Aqui você enxerga qual é — e o que fazer com isso."
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import plotly.express as px
import streamlit as st

from data.database import init_db
from data import repositorio as repo
from data.importacao import executar_importacao_completa
from data.ui_helpers import selo_legenda, nota_rodape_transparencia, alerta_planilha_sem_atendimentos
from kpis import calculos as kpi

st.set_page_config(
    page_title="GestorUPA — Painel de Custeio e Decisão",
    page_icon="🏥",
    layout="wide",
)

PLANILHA_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_upas_feira_de_santana.xlsx")


def garantir_banco_populado():
    init_db()
    if not repo.banco_populado():
        if os.path.exists(PLANILHA_PADRAO):
            with st.spinner("Primeira execução: importando dados reais e gerando estimativas..."):
                resultado = executar_importacao_completa(PLANILHA_PADRAO)
            st.toast(
                f"Base inicializada: {resultado['unidades_importadas']} unidades, "
                f"{resultado['repasses_reais_importados']} repasses reais, "
                f"{resultado['periodos_simulados']} períodos estimados.",
                icon="✅",
            )
        else:
            st.error(
                "Planilha oficial 'base_upas_feira_de_santana.xlsx' não encontrada na "
                "raiz do projeto. Coloque o arquivo ali e recarregue a página."
            )
            st.stop()


garantir_banco_populado()

st.title("🏥 GestorUPA — Painel de Custeio e Decisão")
st.caption("*Cada atendimento tem um custo. Aqui você enxerga qual é — e o que fazer com isso.*")

selo_legenda([
    ("Cadastro de unidades e repasses financeiros", "real"),
    ("Atendimentos, custeio, orçamento e classificação de risco", "estimado"),
])
alerta_planilha_sem_atendimentos()

# ----------------------------------------------------------------------------
# Carrega dados agregados
# ----------------------------------------------------------------------------
unidades = repo.listar_unidades()
atendimentos = repo.obter_atendimentos()
custeio = repo.obter_parametros_custeio()

if unidades.empty or atendimentos.empty or custeio.empty:
    st.warning("Sem dados suficientes para montar a visão geral.")
    st.stop()

custeio = custeio.copy()
custeio["custo_total"] = custeio.apply(
    lambda r: kpi.custo_total(
        r["custo_pessoal"], r["custo_medicamento"], r["custo_material"],
        r["custo_manutencao"], r["custo_administrativo"],
    ), axis=1,
)

base = custeio.merge(atendimentos, on=["id_unidade", "periodo"], how="left")
base = base.merge(unidades[["id_unidade", "nome", "porte", "capacidade_teorica_mensal", "nro_profissionais"]], on="id_unidade", how="left")
base["custo_por_atendimento"] = base.apply(
    lambda r: kpi.custo_por_atendimento(r["custo_total"], r["qtd_atendimentos"]), axis=1
)

# ----------------------------------------------------------------------------
# KPIs agregados da rede
# ----------------------------------------------------------------------------
custo_medio_rede = base["custo_por_atendimento"].mean()
total_atendimentos = int(base["qtd_atendimentos"].sum())
nro_unidades = unidades["id_unidade"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Custo médio por atendimento (rede)", kpi.formatar_reais(custo_medio_rede))
col2.metric("Total de atendimentos no período (estimado)", f"{total_atendimentos:,}".replace(",", "."))
col3.metric("Nº de unidades cadastradas", nro_unidades)

st.divider()

# ----------------------------------------------------------------------------
# Alertas automáticos: unidade com custo/atendimento > 1,5x a média da rede
# ----------------------------------------------------------------------------
st.subheader("⚠️ Alertas automáticos")
media_por_unidade = base.groupby("nome", as_index=False)["custo_por_atendimento"].mean()
limite = custo_medio_rede * 1.5
alertas = media_por_unidade[media_por_unidade["custo_por_atendimento"] > limite]

if alertas.empty:
    st.success("Nenhuma unidade acima de 1,5× o custo médio por atendimento da rede no recorte atual.")
else:
    for _, row in alertas.iterrows():
        st.error(
            f"**{row['nome']}** — custo por atendimento de {kpi.formatar_reais(row['custo_por_atendimento'])} "
            f"está acima do limite de alerta ({kpi.formatar_reais(limite)}, 1,5× a média da rede)."
        )

st.divider()

# ----------------------------------------------------------------------------
# Ranking resumido por índice de eficiência
# ----------------------------------------------------------------------------
st.subheader("🏆 Ranking de eficiência das UPAs")

agregado = base.groupby(["id_unidade", "nome"], as_index=False).agg(
    custo_por_atendimento=("custo_por_atendimento", "mean"),
    qtd_atendimentos=("qtd_atendimentos", "mean"),
    capacidade_teorica_mensal=("capacidade_teorica_mensal", "first"),
    nro_profissionais=("nro_profissionais", "first"),
)
agregado["produtividade"] = agregado.apply(
    lambda r: kpi.produtividade_por_profissional(r["qtd_atendimentos"], r["nro_profissionais"]), axis=1
)
agregado["taxa_ocupacao"] = agregado.apply(
    lambda r: kpi.taxa_ocupacao(r["qtd_atendimentos"], r["capacidade_teorica_mensal"]), axis=1
)

validos = agregado.dropna(subset=["custo_por_atendimento", "produtividade", "taxa_ocupacao"])
if not validos.empty:
    cmin, cmax = validos["custo_por_atendimento"].min(), validos["custo_por_atendimento"].max()
    pmin, pmax = validos["produtividade"].min(), validos["produtividade"].max()
    omin, omax = validos["taxa_ocupacao"].min(), validos["taxa_ocupacao"].max()

    agregado["indice_eficiencia"] = agregado.apply(
        lambda r: kpi.indice_eficiencia_composto(
            r["custo_por_atendimento"], r["produtividade"], r["taxa_ocupacao"],
            cmin, cmax, pmin, pmax, omin, omax,
        ) if pd.notna(r["custo_por_atendimento"]) and pd.notna(r["produtividade"]) and pd.notna(r["taxa_ocupacao"]) else None,
        axis=1,
    )
    ranking = agregado.sort_values("indice_eficiencia", ascending=False, na_position="last")
    ranking_exibicao = ranking[["nome", "indice_eficiencia", "custo_por_atendimento", "taxa_ocupacao"]].copy()
    ranking_exibicao["custo_por_atendimento"] = ranking_exibicao["custo_por_atendimento"].apply(kpi.formatar_reais)
    ranking_exibicao["taxa_ocupacao"] = ranking_exibicao["taxa_ocupacao"].apply(kpi.formatar_percentual)
    ranking_exibicao.columns = ["Unidade", "Índice de eficiência (0-100)", "Custo médio/atendimento", "Taxa de ocupação"]
    st.dataframe(ranking_exibicao, width='stretch', hide_index=True)

    fig = px.bar(
        ranking, x="nome", y="indice_eficiencia",
        labels={"nome": "Unidade", "indice_eficiencia": "Índice de eficiência (0-100)"},
        title="Índice de eficiência composto por unidade (maior = melhor)",
        color="indice_eficiencia", color_continuous_scale="Blues",
    )
    st.plotly_chart(fig, width='stretch')
else:
    st.info("Sem dados suficientes para calcular o ranking de eficiência.")

nota_rodape_transparencia()
