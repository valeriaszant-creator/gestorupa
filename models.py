"""
Modelo de dados do GestorUPA.

Implementa exatamente as tabelas especificadas no documento de arquitetura
(unidade, atendimento_mensal, parametro_custeio, orcamento, classificacao_risco),
mais uma tabela adicional (repasse_financeiro) que armazena os dados FINANCEIROS
REAIS localizados na planilha oficial (aba Fato_Repasses) — dados que a planilha
efetivamente contém, diferentemente de atendimentos, que a planilha não contém.

NOTA IMPORTANTE DE TRANSPARÊNCIA (ver README.md e página "Sobre os Dados"):
A planilha oficial fornecida para este projeto (base_upas_feira_de_santana.xlsx)
é um modelo de REPASSES FINANCEIROS (estrela: dim_UPA, dim_Fonte_Recurso,
dim_Bloco_Financiamento, dim_Categoria_Despesa, Fato_Repasses), e não uma base de
atendimentos pediátricos como assumido inicialmente no documento de arquitetura.
Por decisão do usuário, a arquitetura original (8 páginas, KPIs por atendimento)
foi mantida, e a tabela atendimento_mensal é 100% SIMULADA (origem_dado='estimado')
para viabilizar o funcionamento do MVP. Isso é sinalizado em toda tela do app.
"""
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from data.database import Base


class Unidade(Base):
    __tablename__ = "unidade"

    id_unidade = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # "UPA" | "Hospital"
    bairro = Column(String, nullable=True)
    natureza_gestao = Column(String, nullable=True)  # "Público/SUS" | "Privado" | "Filantrópico/SUS"
    cnes = Column(String, nullable=True)
    funcionamento = Column(String, nullable=True)  # ex.: "24h"

    # Campos auxiliares (necessários para os KPIs do documento de arquitetura;
    # sempre com origem estimada quando não houver CNES/porte oficial confirmado)
    porte = Column(String, nullable=True)  # "Porte I" | "Porte II" | "Porte III"
    capacidade_teorica_mensal = Column(Integer, nullable=True)  # atendimentos/mês
    nro_profissionais = Column(Integer, nullable=True)
    origem_cadastro = Column(String, nullable=False, default="real")  # real | estimado

    atendimentos = relationship("AtendimentoMensal", back_populates="unidade", cascade="all, delete-orphan")
    parametros_custeio = relationship("ParametroCusteio", back_populates="unidade", cascade="all, delete-orphan")
    orcamentos = relationship("Orcamento", back_populates="unidade", cascade="all, delete-orphan")
    classificacoes_risco = relationship("ClassificacaoRisco", back_populates="unidade", cascade="all, delete-orphan")
    repasses = relationship("RepasseFinanceiro", back_populates="unidade", cascade="all, delete-orphan")


class AtendimentoMensal(Base):
    __tablename__ = "atendimento_mensal"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    periodo = Column(String, nullable=False)  # "AAAA-MM"
    qtd_atendimentos = Column(Integer, nullable=True)
    origem_dado = Column(String, nullable=False)  # "real" | "estimado"

    unidade = relationship("Unidade", back_populates="atendimentos")

    __table_args__ = (UniqueConstraint("id_unidade", "periodo", name="uq_atendimento_unidade_periodo"),)


class ParametroCusteio(Base):
    __tablename__ = "parametro_custeio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    periodo = Column(String, nullable=False)

    custo_pessoal = Column(Float, nullable=True)
    custo_medicamento = Column(Float, nullable=True)
    custo_material = Column(Float, nullable=True)
    custo_manutencao = Column(Float, nullable=True)
    custo_administrativo = Column(Float, nullable=True)

    tipo_custo_pessoal = Column(String, nullable=True)        # "fixo" | "variável"
    tipo_custo_medicamento = Column(String, nullable=True)
    tipo_custo_material = Column(String, nullable=True)
    tipo_custo_manutencao = Column(String, nullable=True)
    tipo_custo_administrativo = Column(String, nullable=True)

    fonte = Column(String, nullable=True)

    unidade = relationship("Unidade", back_populates="parametros_custeio")

    __table_args__ = (UniqueConstraint("id_unidade", "periodo", name="uq_custeio_unidade_periodo"),)


class Orcamento(Base):
    __tablename__ = "orcamento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    periodo = Column(String, nullable=False)
    valor_orcado = Column(Float, nullable=True)
    origem_dado = Column(String, nullable=False, default="estimado")  # real | estimado

    unidade = relationship("Unidade", back_populates="orcamentos")

    __table_args__ = (UniqueConstraint("id_unidade", "periodo", name="uq_orcamento_unidade_periodo"),)


class ClassificacaoRisco(Base):
    __tablename__ = "classificacao_risco"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    periodo = Column(String, nullable=False)
    categoria_risco = Column(String, nullable=False)  # vermelho | amarelo | verde | azul
    qtd_estimada = Column(Integer, nullable=True)
    origem_dado = Column(String, nullable=False, default="estimado")

    unidade = relationship("Unidade", back_populates="classificacoes_risco")


class RepasseFinanceiro(Base):
    """
    Tabela EXTRA (não prevista no documento original) que guarda os lançamentos
    financeiros REAIS extraídos da aba Fato_Repasses da planilha oficial.
    Usada na Página 6 (Orçado x Realizado) para mostrar dado genuinamente real
    ao lado do orçamento (que permanece estimado onde não há repasse aprovado).
    """
    __tablename__ = "repasse_financeiro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"), nullable=False)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    esfera = Column(String, nullable=True)  # Municipal | Estadual | Federal
    instrumento = Column(String, nullable=True)
    valor_previsto = Column(Float, nullable=True)
    valor_repassado = Column(Float, nullable=True)
    valor_pago = Column(Float, nullable=True)
    fonte_dado = Column(String, nullable=True)
    origem_dado = Column(String, nullable=False, default="real")

    unidade = relationship("Unidade", back_populates="repasses")
