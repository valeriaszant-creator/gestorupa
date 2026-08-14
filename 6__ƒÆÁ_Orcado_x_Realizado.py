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

st.set_page_config(page_title="Orçado x Realizado — GestorUPA", page_icon="💵", layout="wide")
init_db()

st.title("💵 Orçado x Realizado")
selo_legenda([
    ("Orçamento e custo realizado (modelo de custeio)", "estimado"),
    ("Repasses financeiros efetivos", "real"),
])

unidades = repo.listar_unidades()
custeio = repo.obter_parametros_custeio()
orcamentos = repo.obter_orcamentos()
repasses = repo.obter_repasses_reais()

if unidades.empty or custeio.empty or orcamentos.empty:
    st.warning("Sem dados suficientes.")
    st.stop()

nome_unidade = st.selectbox("Unidade", unidades["nome"].tolist())
id_unidade = int(unidades.loc[unidades["nome"] == nome_unidade, "id_unidade"].iloc[0])

st.subheader("Modelo de custeio: orçado x custo realizado (estimado)")
custeio_u = custeio[custeio["id_unidade"] == id_unidade].copy()
custeio_u["custo_total"] = custeio_u.apply(
    lambda r: kpi.custo_total(
        r["custo_pessoal"], r["custo_medicamento"], r["custo_material"],
        r["custo_manutencao"], r["custo_administrativo"],
    ), axis=1,
)
orc_u = orcamentos[orcamentos["id_unidade"] == id_unidade]
comp = custeio_u.merge(orc_u[["periodo", "valor_orcado"]], on="periodo", how="left").sort_values("periodo")
comp["variacao"] = comp.apply(lambda r: kpi.variacao_orcado_realizado(r["custo_total"], r["valor_orcado"]), axis=1)

comp_long = comp.melt(id_vars=["periodo", "variacao"], value_vars=["valor_orcado", "custo_total"],
                       var_name="tipo", value_name="valor")
comp_long["tipo"] = comp_long["tipo"].map({"valor_orcado": "Orçado", "custo_total": "Realizado (estimado)"})

fig = px.bar(comp_long, x="periodo", y="valor", color="tipo", barmode="group",
             labels={"periodo": "Período", "valor": "R$", "tipo": ""})
st.plotly_chart(fig, width='stretch')

st.subheader("Percentual de variação (realizado vs. orçado)")
for _, row in comp.iterrows():
    variacao = row["variacao"]
    texto = kpi.formatar_percentual(variacao)
    if variacao is None:
        st.write(f"**{row['periodo']}**: sem dado suficiente")
    elif variacao <= 0:
        st.success(f"**{row['periodo']}**: {texto} — dentro do orçado")
    else:
        st.error(f"**{row['periodo']}**: +{texto} — acima do orçado")

st.divider()
st.subheader("Repasses financeiros reais registrados")
repasses_u = repasses[repasses["id_unidade"] == id_unidade] if not repasses.empty else pd.DataFrame()

if repasses_u.empty:
    st.info(
        "Não há lançamentos financeiros reais registrados para esta unidade na "
        "planilha oficial fornecida (a maior parte da aba Fato_Repasses é um "
        "modelo a ser preenchido manualmente pela equipe gestora, conforme a "
        "aba 'Leia-me' da planilha)."
    )
else:
    exibicao = repasses_u.copy()
    exibicao["competencia"] = exibicao["ano"].astype(str) + "-" + exibicao["mes"].astype(str).str.zfill(2)
    exibicao = exibicao[["competencia", "esfera", "instrumento", "valor_previsto", "valor_repassado", "valor_pago", "fonte_dado"]]
    exibicao.columns = ["Competência", "Esfera", "Instrumento", "Valor Previsto", "Valor Repassado", "Valor Pago", "Fonte do dado"]
    st.dataframe(exibicao, width='stretch', hide_index=True)
    st.caption(
        "📎 Estes valores são REAIS, extraídos de razões contábeis públicas e "
        "reportagens sobre publicações no Diário Oficial (ver coluna 'Fonte do "
        "dado'). Não confundir com o modelo de custeio estimado acima: o repasse "
        "financeiro é o que efetivamente entrou no caixa da unidade/OSS, enquanto "
        "o 'custo realizado' do gráfico é uma estimativa do custeio operacional."
    )

nota_rodape_transparencia()
