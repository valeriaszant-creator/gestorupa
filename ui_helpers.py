"""
Componentes visuais compartilhados entre as páginas — sobretudo o selo de
origem do dado, exigido em toda tela pelo item 2 do documento de arquitetura:
"Nunca apresentar valor estimado como se fosse real."
"""
import streamlit as st

COR_REAL = "#1B7A43"
COR_ESTIMADO = "#B8860B"
COR_MISTO = "#4A5FBF"


def _badge_html(texto: str, cor: str) -> str:
    return (
        f'<span style="background-color:{cor}1A; color:{cor}; '
        f'border:1px solid {cor}; border-radius:6px; padding:2px 10px; '
        f'font-size:0.8rem; font-weight:600; margin-right:6px; white-space:nowrap;">{texto}</span>'
    )


def selo_legenda(itens: list[tuple[str, str]]):
    """
    Renderiza a legenda de origem dos dados no topo da página.
    `itens`: lista de tuplas (rótulo, origem) onde origem ∈ {"real", "estimado"}.
    Ex.: selo_legenda([("Cadastro de unidades", "real"), ("Custos", "estimado")])
    """
    mapa_cor = {"real": COR_REAL, "estimado": COR_ESTIMADO}
    mapa_rotulo = {"real": "DADO REAL", "estimado": "ESTIMATIVA METODOLÓGICA"}
    partes = []
    for label, origem in itens:
        cor = mapa_cor.get(origem, COR_MISTO)
        rotulo = mapa_rotulo.get(origem, origem.upper())
        partes.append(_badge_html(f"{label}: {rotulo}", cor))
    st.markdown(
        f'<div style="margin-bottom:1rem;">{"".join(partes)}</div>',
        unsafe_allow_html=True,
    )


def nota_rodape_transparencia():
    """Nota de rodapé fixa, reforçando a regra de transparência em toda página."""
    st.markdown("---")
    st.caption(
        "🔍 **Nota de transparência de dados:** este painel distingue explicitamente "
        "dado **real** (extraído da planilha oficial de repasses financeiros e do "
        "cadastro CNES/SESAB das unidades) de dado **estimado** (parâmetros de "
        "custeio, atendimentos, classificação de risco e capacidade — gerados por "
        "metodologia declarada, nunca números soltos). Veja a página **'Sobre os "
        "Dados'** no menu para o detalhamento completo da premissa de cada estimativa."
    )


def alerta_planilha_sem_atendimentos():
    st.info(
        "ℹ️ A planilha oficial fornecida para este projeto contém repasses "
        "financeiros reais, mas **não contém série de atendimentos por unidade**. "
        "Os números de atendimento exibidos abaixo são uma **estimativa "
        "metodológica** (±15% em torno de uma referência por porte da unidade), "
        "gerada apenas para viabilizar o funcionamento deste MVP acadêmico. "
        "Consulte a página 'Sobre os Dados' para a premissa completa.",
        icon="ℹ️",
    )
