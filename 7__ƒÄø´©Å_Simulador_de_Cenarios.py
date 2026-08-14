import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from data.database import init_db
from data import repositorio as repo
from data.ui_helpers import selo_legenda, nota_rodape_transparencia
from kpis import calculos as kpi
from simulador.cenarios import EstadoCusteio, aplicar_cenario, resumo_estado, custo_marginal_cenario

st.set_page_config(page_title="Simulador de Cenários — GestorUPA", page_icon="🎛️", layout="wide")
init_db()

st.title("🎛️ Simulador de Cenários")
selo_legenda([("Base de partida (estimada) + variações aplicadas pelo usuário", "estimado")])
st.caption(
    "Este simulador projeta cenários hipotéticos a partir da base estimada de "
    "custeio. Os resultados são simulações gerenciais, não previsões oficiais."
)

unidades = repo.listar_unidades()
custeio = repo.obter_parametros_custeio()
atendimentos = repo.obter_atendimentos()

if unidades.empty or custeio.empty or atendimentos.empty:
    st.warning("Sem dados suficientes.")
    st.stop()

col_a, col_b = st.columns(2)
nome_unidade = col_a.selectbox("Unidade", unidades["nome"].tolist())
id_unidade = int(unidades.loc[unidades["nome"] == nome_unidade, "id_unidade"].iloc[0])
nro_profissionais_base = unidades.loc[unidades["id_unidade"] == id_unidade, "nro_profissionais"].iloc[0] or 1

periodos = repo.periodos_disponiveis()
periodo_sel = col_b.selectbox("Período-base", periodos, index=len(periodos) - 1 if periodos else 0)

linha_custeio = custeio[(custeio["id_unidade"] == id_unidade) & (custeio["periodo"] == periodo_sel)]
linha_atend = atendimentos[(atendimentos["id_unidade"] == id_unidade) & (atendimentos["periodo"] == periodo_sel)]

if linha_custeio.empty or linha_atend.empty:
    st.info("Sem dado-base para esta combinação de unidade/período.")
    st.stop()

lc = linha_custeio.iloc[0]
la = linha_atend.iloc[0]

estado_antes = EstadoCusteio(
    qtd_atendimentos=la["qtd_atendimentos"],
    custo_pessoal=lc["custo_pessoal"],
    custo_medicamento=lc["custo_medicamento"],
    custo_material=lc["custo_material"],
    custo_manutencao=lc["custo_manutencao"],
    custo_administrativo=lc["custo_administrativo"],
    nro_profissionais=nro_profissionais_base,
)

st.divider()
st.subheader("Alavancas do cenário")
c1, c2, c3 = st.columns(3)
var_demanda = c1.slider("Variação % de demanda", -50, 100, 0, step=5)
var_profissionais = c2.slider("Variação no nº de profissionais (%)", -50, 100, 0, step=5)
var_custo_insumos = c3.slider("Variação % no custo de medicamentos/materiais", -50, 100, 0, step=5)

estado_depois = aplicar_cenario(estado_antes, var_demanda, var_profissionais, var_custo_insumos)

resumo_antes = resumo_estado(estado_antes)
resumo_depois = resumo_estado(estado_depois)
marginal = custo_marginal_cenario(estado_antes, estado_depois)

st.divider()
st.subheader("Antes x Depois")
col_antes, col_depois = st.columns(2)

with col_antes:
    st.markdown("### 📍 Cenário atual")
    st.metric("Custo total", kpi.formatar_reais(resumo_antes["custo_total"]))
    st.metric("Custo por atendimento", kpi.formatar_reais(resumo_antes["custo_por_atendimento"]))
    st.metric("Atendimentos", f"{resumo_antes['qtd_atendimentos']:,.0f}".replace(",", "."))

with col_depois:
    st.markdown("### 🔮 Cenário simulado")
    delta_custo = resumo_depois["custo_total"] - resumo_antes["custo_total"]
    delta_cpa = (resumo_depois["custo_por_atendimento"] or 0) - (resumo_antes["custo_por_atendimento"] or 0)
    st.metric("Custo total", kpi.formatar_reais(resumo_depois["custo_total"]), delta=kpi.formatar_reais(delta_custo))
    st.metric("Custo por atendimento", kpi.formatar_reais(resumo_depois["custo_por_atendimento"]), delta=kpi.formatar_reais(delta_cpa))
    st.metric("Atendimentos", f"{resumo_depois['qtd_atendimentos']:,.0f}".replace(",", "."))

st.divider()
st.subheader("Custo marginal do cenário")
if marginal is None:
    st.info(
        "Custo marginal: sem dado suficiente (a demanda simulada não aumentou em "
        "relação ao cenário atual)."
    )
else:
    st.metric("Custo marginal por atendimento adicional", kpi.formatar_reais(marginal))

nota_rodape_transparencia()
