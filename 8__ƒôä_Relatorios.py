import io
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

from data.database import init_db
from data import repositorio as repo
from data.ui_helpers import selo_legenda, nota_rodape_transparencia
from kpis import calculos as kpi

st.set_page_config(page_title="Relatórios — GestorUPA", page_icon="📄", layout="wide")
init_db()

st.title("📄 Relatórios")
selo_legenda([("Relatório exportado", "misto")])
st.caption("O relatório inclui, sempre, a nota metodológica de origem dos dados (real vs. estimado).")

NOTA_METODOLOGICA = """NOTA METODOLÓGICA — ORIGEM DOS DADOS (GestorUPA)

DADO REAL:
- Cadastro das unidades (nome, endereço/bairro, natureza de gestão, CNES/CNPJ, porte quando confirmado):
  extraído da aba dim_UPA da planilha oficial, com base em fontes públicas (CNES-DATASUS, SESAB, reportagens
  sobre contratos de gestão publicados em Diário Oficial).
- Repasses financeiros: extraídos da aba Fato_Repasses da planilha oficial, apenas as linhas com valor
  efetivamente localizado em fontes públicas (razões contábeis da OSS gestora, Diário Oficial do Município).

DADO ESTIMADO (estimativa metodológica, nunca apresentado como real):
- Atendimentos mensais, parâmetros de custeio (pessoal, medicamento, material, manutenção, administrativo),
  orçamento mensal e classificação de risco: a planilha oficial fornecida para este projeto contém repasses
  financeiros, mas NÃO contém série de atendimentos por unidade. Esses valores foram gerados por função
  parametrizada (variação aleatória controlada de ±15% em torno de um valor de referência por porte da
  unidade, baseado na estrutura de custeio típica de UPA 24h / Portaria GM/MS nº 3.134/2020), exclusivamente
  para viabilizar o funcionamento deste MVP acadêmico de Contabilidade Gerencial + BI.

Esta distinção é sinalizada em toda tela do aplicativo por meio de selos de origem do dado.
Relatório gerado em: {data_geracao}
"""


def gerar_dataframe_resumo(id_unidade, periodo, nome_unidade):
    custeio = repo.obter_parametros_custeio(id_unidade=id_unidade, periodo=periodo)
    atendimentos = repo.obter_atendimentos(id_unidade=id_unidade, periodo=periodo)
    orcamento = repo.obter_orcamentos(id_unidade=id_unidade, periodo=periodo)
    risco = repo.obter_classificacao_risco(id_unidade=id_unidade, periodo=periodo)

    if custeio.empty:
        return None

    row = custeio.iloc[0]
    custo_total = kpi.custo_total(
        row["custo_pessoal"], row["custo_medicamento"], row["custo_material"],
        row["custo_manutencao"], row["custo_administrativo"],
    )
    qtd_atend = atendimentos.iloc[0]["qtd_atendimentos"] if not atendimentos.empty else None
    valor_orc = orcamento.iloc[0]["valor_orcado"] if not orcamento.empty else None

    linhas = [
        ("Unidade", nome_unidade, "-"),
        ("Período", periodo, "-"),
        ("Custo total do período", kpi.formatar_reais(custo_total), "estimado"),
        ("Custo por atendimento", kpi.formatar_reais(kpi.custo_por_atendimento(custo_total, qtd_atend)), "estimado"),
        ("Atendimentos no período", qtd_atend, "estimado"),
        ("Custo de pessoal", kpi.formatar_reais(row["custo_pessoal"]), "estimado"),
        ("Custo de medicamento", kpi.formatar_reais(row["custo_medicamento"]), "estimado"),
        ("Custo de material", kpi.formatar_reais(row["custo_material"]), "estimado"),
        ("Custo de manutenção", kpi.formatar_reais(row["custo_manutencao"]), "estimado"),
        ("Custo administrativo", kpi.formatar_reais(row["custo_administrativo"]), "estimado"),
        ("Participação do custo de pessoal", kpi.formatar_percentual(kpi.participacao_custo_pessoal(row["custo_pessoal"], custo_total)), "estimado"),
        ("Valor orçado", kpi.formatar_reais(valor_orc), "estimado"),
        ("Variação orçado x realizado", kpi.formatar_percentual(kpi.variacao_orcado_realizado(custo_total, valor_orc)), "estimado"),
    ]
    if not risco.empty:
        for _, r in risco.iterrows():
            linhas.append((f"Atendimentos estimados — risco {r['categoria_risco']}", r["qtd_estimada"], "estimado"))

    df = pd.DataFrame(linhas, columns=["Indicador", "Valor", "Origem do dado"])
    df["Valor"] = df["Valor"].astype(str)  # coluna mista (str/num) -> normaliza para exibição/Arrow
    return df


unidades = repo.listar_unidades()
if unidades.empty:
    st.warning("Sem unidades cadastradas.")
    st.stop()

col_a, col_b = st.columns(2)
nome_unidade = col_a.selectbox("Unidade", unidades["nome"].tolist())
id_unidade = int(unidades.loc[unidades["nome"] == nome_unidade, "id_unidade"].iloc[0])
periodos = repo.periodos_disponiveis()
periodo_sel = col_b.selectbox("Período", periodos, index=len(periodos) - 1 if periodos else 0)

df_resumo = gerar_dataframe_resumo(id_unidade, periodo_sel, nome_unidade)

if df_resumo is None:
    st.info("Sem dado suficiente para gerar relatório desta combinação de unidade/período.")
    st.stop()

st.subheader("Pré-visualização do resumo")
st.dataframe(df_resumo, width='stretch', hide_index=True)

nota_formatada = NOTA_METODOLOGICA.format(data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M"))

col_excel, col_pdf = st.columns(2)

# --- Exportar Excel ---
with col_excel:
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
        df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
        pd.DataFrame({"Nota metodológica": nota_formatada.split("\n")}).to_excel(
            writer, sheet_name="Nota Metodológica", index=False
        )
    st.download_button(
        "⬇️ Baixar Excel (.xlsx)",
        data=buffer_excel.getvalue(),
        file_name=f"gestorupa_relatorio_{nome_unidade.replace(' ', '_')}_{periodo_sel}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch',
    )

# --- Exportar PDF ---
with col_pdf:
    try:
        from fpdf import FPDF, XPos, YPos

        def _pdf_safe(texto: str) -> str:
            """Fonte core do fpdf (Helvetica) só suporta latin-1: normaliza
            travessões/aspas tipográficas antes de decair para '?' no resto."""
            substituicoes = {
                "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
                "\u201c": '"', "\u201d": '"', "\u2026": "...",
            }
            for original, novo in substituicoes.items():
                texto = texto.replace(original, novo)
            return texto.encode("latin-1", "replace").decode("latin-1")

        def _linha(texto, h=6):
            """multi_cell não retorna o cursor X à margem esquerda sozinho;
            forçamos isso a cada linha para não 'comer' a largura da próxima."""
            pdf.multi_cell(0, h, _pdf_safe(texto))
            pdf.set_x(pdf.l_margin)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 14)
        _linha("GestorUPA - Relatório de Custeio e Decisão", h=8)
        pdf.set_font("Helvetica", "", 10)
        _linha(f"Unidade: {nome_unidade}  |  Período: {periodo_sel}")
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _pdf_safe("Resumo de indicadores"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        for _, r in df_resumo.iterrows():
            texto = f"{r['Indicador']}: {r['Valor']} ({r['Origem do dado']})"
            _linha(texto, h=5)
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _pdf_safe("Nota metodológica"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8)
        _linha(nota_formatada, h=4.5)

        pdf_bytes = pdf.output()

        st.download_button(
            "⬇️ Baixar PDF",
            data=bytes(pdf_bytes),
            file_name=f"gestorupa_relatorio_{nome_unidade.replace(' ', '_')}_{periodo_sel}.pdf",
            mime="application/pdf",
            width='stretch',
        )
    except ImportError:
        st.warning("Biblioteca `fpdf2` não instalada — instale com `pip install fpdf2` para habilitar exportação em PDF. A exportação em Excel funciona normalmente.")

st.divider()
with st.expander("📎 Ler a nota metodológica completa"):
    st.text(nota_formatada)

nota_rodape_transparencia()
