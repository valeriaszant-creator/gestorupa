"""
Camada de consulta (repositório): funções que retornam pandas DataFrames
prontos para uso nas páginas Streamlit. Mantém toda query SQL fora de pages/,
para facilitar a futura migração de SQLite para Postgres/Supabase.
"""
import pandas as pd
from sqlalchemy import select

from data.database import get_session
from data.models import (
    Unidade, AtendimentoMensal, ParametroCusteio, Orcamento,
    ClassificacaoRisco, RepasseFinanceiro,
)

CATEGORIAS_CUSTO = [
    ("custo_pessoal", "Pessoal"),
    ("custo_medicamento", "Medicamento"),
    ("custo_material", "Material"),
    ("custo_manutencao", "Manutenção"),
    ("custo_administrativo", "Administrativo"),
]


def _df_from_query(session, query):
    result = session.execute(query).all()
    return result


def listar_unidades() -> pd.DataFrame:
    session = get_session()
    try:
        unidades = session.query(Unidade).all()
        return pd.DataFrame([{
            "id_unidade": u.id_unidade,
            "nome": u.nome,
            "tipo": u.tipo,
            "bairro": u.bairro,
            "natureza_gestao": u.natureza_gestao,
            "cnes": u.cnes,
            "funcionamento": u.funcionamento,
            "porte": u.porte,
            "capacidade_teorica_mensal": u.capacidade_teorica_mensal,
            "nro_profissionais": u.nro_profissionais,
            "origem_cadastro": u.origem_cadastro,
        } for u in unidades])
    finally:
        session.close()


def obter_atendimentos(id_unidade=None, periodo=None) -> pd.DataFrame:
    session = get_session()
    try:
        q = session.query(AtendimentoMensal)
        if id_unidade:
            q = q.filter(AtendimentoMensal.id_unidade == id_unidade)
        if periodo:
            q = q.filter(AtendimentoMensal.periodo == periodo)
        rows = q.all()
        return pd.DataFrame([{
            "id_unidade": r.id_unidade, "periodo": r.periodo,
            "qtd_atendimentos": r.qtd_atendimentos, "origem_dado": r.origem_dado,
        } for r in rows])
    finally:
        session.close()


def obter_parametros_custeio(id_unidade=None, periodo=None) -> pd.DataFrame:
    session = get_session()
    try:
        q = session.query(ParametroCusteio)
        if id_unidade:
            q = q.filter(ParametroCusteio.id_unidade == id_unidade)
        if periodo:
            q = q.filter(ParametroCusteio.periodo == periodo)
        rows = q.all()
        return pd.DataFrame([{
            "id_unidade": r.id_unidade, "periodo": r.periodo,
            "custo_pessoal": r.custo_pessoal, "custo_medicamento": r.custo_medicamento,
            "custo_material": r.custo_material, "custo_manutencao": r.custo_manutencao,
            "custo_administrativo": r.custo_administrativo,
            "tipo_custo_pessoal": r.tipo_custo_pessoal, "tipo_custo_medicamento": r.tipo_custo_medicamento,
            "tipo_custo_material": r.tipo_custo_material, "tipo_custo_manutencao": r.tipo_custo_manutencao,
            "tipo_custo_administrativo": r.tipo_custo_administrativo,
            "fonte": r.fonte,
        } for r in rows])
    finally:
        session.close()


def obter_orcamentos(id_unidade=None, periodo=None) -> pd.DataFrame:
    session = get_session()
    try:
        q = session.query(Orcamento)
        if id_unidade:
            q = q.filter(Orcamento.id_unidade == id_unidade)
        if periodo:
            q = q.filter(Orcamento.periodo == periodo)
        rows = q.all()
        return pd.DataFrame([{
            "id_unidade": r.id_unidade, "periodo": r.periodo,
            "valor_orcado": r.valor_orcado, "origem_dado": r.origem_dado,
        } for r in rows])
    finally:
        session.close()


def obter_classificacao_risco(id_unidade=None, periodo=None) -> pd.DataFrame:
    session = get_session()
    try:
        q = session.query(ClassificacaoRisco)
        if id_unidade:
            q = q.filter(ClassificacaoRisco.id_unidade == id_unidade)
        if periodo:
            q = q.filter(ClassificacaoRisco.periodo == periodo)
        rows = q.all()
        return pd.DataFrame([{
            "id_unidade": r.id_unidade, "periodo": r.periodo,
            "categoria_risco": r.categoria_risco, "qtd_estimada": r.qtd_estimada,
            "origem_dado": r.origem_dado,
        } for r in rows])
    finally:
        session.close()


def obter_repasses_reais(id_unidade=None) -> pd.DataFrame:
    session = get_session()
    try:
        q = session.query(RepasseFinanceiro)
        if id_unidade:
            q = q.filter(RepasseFinanceiro.id_unidade == id_unidade)
        rows = q.all()
        return pd.DataFrame([{
            "id_unidade": r.id_unidade, "ano": r.ano, "mes": r.mes, "esfera": r.esfera,
            "instrumento": r.instrumento, "valor_previsto": r.valor_previsto,
            "valor_repassado": r.valor_repassado, "valor_pago": r.valor_pago,
            "fonte_dado": r.fonte_dado, "origem_dado": r.origem_dado,
        } for r in rows])
    finally:
        session.close()


def periodos_disponiveis() -> list:
    df = obter_atendimentos()
    if df.empty:
        return []
    return sorted(df["periodo"].unique().tolist())


def banco_populado() -> bool:
    """Verifica rapidamente se o banco já foi importado/populado."""
    try:
        df = listar_unidades()
        return not df.empty
    except Exception:
        return False
