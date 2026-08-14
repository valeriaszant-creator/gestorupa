"""Testes das funções puras de kpis/calculos.py. Rodar com: pytest tests/"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kpis import calculos as kpi
from simulador.cenarios import EstadoCusteio, aplicar_cenario, resumo_estado


def test_custo_por_atendimento_normal():
    assert kpi.custo_por_atendimento(100_000, 500) == 200.0


def test_custo_por_atendimento_divisao_por_zero():
    assert kpi.custo_por_atendimento(100_000, 0) is None


def test_custo_por_atendimento_none():
    assert kpi.custo_por_atendimento(None, 500) is None


def test_participacao_custo_pessoal():
    assert kpi.participacao_custo_pessoal(50_000, 200_000) == 0.25


def test_taxa_ocupacao():
    assert kpi.taxa_ocupacao(900, 1000) == 0.9


def test_taxa_ocupacao_zero_capacidade():
    assert kpi.taxa_ocupacao(900, 0) is None


def test_variacao_orcado_realizado_acima():
    assert round(kpi.variacao_orcado_realizado(120_000, 100_000), 4) == 0.2


def test_variacao_orcado_realizado_abaixo():
    assert round(kpi.variacao_orcado_realizado(80_000, 100_000), 4) == -0.2


def test_variacao_orcado_realizado_orcamento_zero():
    assert kpi.variacao_orcado_realizado(80_000, 0) is None


def test_custo_marginal():
    assert kpi.custo_marginal_por_atendimento_adicional(30_000, 100) == 300.0


def test_custo_marginal_sem_atendimentos_adicionais():
    assert kpi.custo_marginal_por_atendimento_adicional(30_000, 0) is None


def test_ponto_equilibrio():
    # custo fixo 100_000; custo médio 500; custo variável médio 200 -> margem 300
    resultado = kpi.ponto_equilibrio_operacional(100_000, 500, 200)
    assert round(resultado, 2) == round(100_000 / 300, 2)


def test_ponto_equilibrio_margem_zero():
    assert kpi.ponto_equilibrio_operacional(100_000, 300, 300) is None


def test_indice_eficiencia_composto_extremos():
    # unidade com o menor custo, maior produtividade e maior ocupação -> nota máxima
    nota = kpi.indice_eficiencia_composto(
        custo_por_atend=100, produtividade=50, taxa_ocup=1.0,
        custo_por_atend_min=100, custo_por_atend_max=200,
        produtividade_min=10, produtividade_max=50,
        taxa_ocup_min=0.5, taxa_ocup_max=1.0,
    )
    assert nota == 100.0


def test_separar_custos_fixos_variaveis():
    row = {
        "custo_pessoal": 100, "tipo_custo_pessoal": "fixo",
        "custo_medicamento": 50, "tipo_custo_medicamento": "variável",
        "custo_material": 30, "tipo_custo_material": "variável",
        "custo_manutencao": 10, "tipo_custo_manutencao": "fixo",
        "custo_administrativo": 20, "tipo_custo_administrativo": "variável",
    }
    resultado = kpi.separar_custos_fixos_variaveis(row)
    assert resultado == {"fixo": 110, "variavel": 100}


def test_formatar_reais_none():
    assert kpi.formatar_reais(None) == "sem dado suficiente"


def test_formatar_reais_valor():
    assert kpi.formatar_reais(1234.5) == "R$ 1.234,50"


def test_simulador_aumento_demanda_aumenta_custo_variavel():
    estado = EstadoCusteio(
        qtd_atendimentos=1000, custo_pessoal=100_000, custo_medicamento=20_000,
        custo_material=15_000, custo_manutencao=5_000, custo_administrativo=10_000,
        nro_profissionais=50,
    )
    depois = aplicar_cenario(estado, variacao_demanda_pct=10, variacao_profissionais_pct=0,
                              variacao_custo_medicamento_material_pct=20)
    assert depois.qtd_atendimentos == 1100
    assert depois.custo_medicamento == 24_000
    assert depois.custo_material == 18_000
    assert depois.custo_pessoal == estado.custo_pessoal  # inalterado


def test_resumo_estado_calcula_custo_por_atendimento():
    estado = EstadoCusteio(
        qtd_atendimentos=1000, custo_pessoal=100_000, custo_medicamento=20_000,
        custo_material=15_000, custo_manutencao=5_000, custo_administrativo=10_000,
        nro_profissionais=50,
    )
    resumo = resumo_estado(estado)
    assert resumo["custo_total"] == 150_000
    assert resumo["custo_por_atendimento"] == 150.0
    assert resumo["produtividade_por_profissional"] == 20.0
