"""
Lógica do Simulador de Cenários (Página 7).

Funções puras: recebem o estado "antes" (atendimentos e parâmetros de
custeio de um período/unidade) e os percentuais de variação escolhidos nos
sliders, e devolvem o estado "depois" recalculado, usando as mesmas fórmulas
de kpis/calculos.py.
"""
from dataclasses import dataclass
from typing import Optional

from kpis import calculos as kpi


@dataclass
class EstadoCusteio:
    qtd_atendimentos: float
    custo_pessoal: float
    custo_medicamento: float
    custo_material: float
    custo_manutencao: float
    custo_administrativo: float
    nro_profissionais: float


def aplicar_cenario(
    estado: EstadoCusteio,
    variacao_demanda_pct: float,
    variacao_profissionais_pct: float,
    variacao_custo_medicamento_material_pct: float,
) -> EstadoCusteio:
    """
    Aplica as três alavancas do simulador sobre o estado atual:
      (a) variação % de demanda -> altera qtd_atendimentos
      (b) variação no nº de profissionais -> altera nro_profissionais
      (c) variação % no custo de medicamentos/materiais -> altera essas duas categorias
    Custos de pessoal, manutenção e administrativo permanecem fixos no cenário
    (coerente com a classificação fixo/variável adotada no MVP).
    """
    novo_atendimentos = max(0, estado.qtd_atendimentos * (1 + variacao_demanda_pct / 100))
    novo_profissionais = max(0, estado.nro_profissionais * (1 + variacao_profissionais_pct / 100))
    novo_medicamento = max(0, estado.custo_medicamento * (1 + variacao_custo_medicamento_material_pct / 100))
    novo_material = max(0, estado.custo_material * (1 + variacao_custo_medicamento_material_pct / 100))

    return EstadoCusteio(
        qtd_atendimentos=novo_atendimentos,
        custo_pessoal=estado.custo_pessoal,
        custo_medicamento=novo_medicamento,
        custo_material=novo_material,
        custo_manutencao=estado.custo_manutencao,
        custo_administrativo=estado.custo_administrativo,
        nro_profissionais=novo_profissionais,
    )


def resumo_estado(estado: EstadoCusteio) -> dict:
    """Calcula os indicadores derivados de um EstadoCusteio para exibição lado a lado."""
    ct = kpi.custo_total(
        estado.custo_pessoal, estado.custo_medicamento, estado.custo_material,
        estado.custo_manutencao, estado.custo_administrativo,
    )
    custo_variavel = estado.custo_medicamento + estado.custo_material + estado.custo_administrativo
    custo_fixo = estado.custo_pessoal + estado.custo_manutencao

    custo_atend = kpi.custo_por_atendimento(ct, estado.qtd_atendimentos)
    custo_var_medio = kpi.custo_por_atendimento(custo_variavel, estado.qtd_atendimentos)

    return {
        "custo_total": ct,
        "custo_fixo": custo_fixo,
        "custo_variavel": custo_variavel,
        "qtd_atendimentos": estado.qtd_atendimentos,
        "custo_por_atendimento": custo_atend,
        "custo_variavel_medio": custo_var_medio,
        "produtividade_por_profissional": kpi.produtividade_por_profissional(
            estado.qtd_atendimentos, estado.nro_profissionais
        ),
    }


def custo_marginal_cenario(estado_antes: EstadoCusteio, estado_depois: EstadoCusteio) -> Optional[float]:
    """Custo marginal por atendimento adicional entre o cenário 'antes' e 'depois'."""
    resumo_depois = resumo_estado(estado_depois)
    atendimentos_adicionais = estado_depois.qtd_atendimentos - estado_antes.qtd_atendimentos
    if atendimentos_adicionais <= 0:
        return None
    return kpi.custo_marginal_por_atendimento_adicional(
        resumo_depois["custo_variavel"], atendimentos_adicionais
    )
