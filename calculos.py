"""
Funções puras de cálculo de KPI (item 6 do documento de arquitetura).

Todas as funções:
  - recebem apenas números/estruturas simples (nada de sessão de banco aqui,
    para permanecerem 100% testáveis com pytest sem precisar de fixtures de DB);
  - tratam divisão por zero e valores ausentes retornando None, NUNCA lançando
    exceção para a tela (a camada de apresentação decide como exibir "sem dado
    suficiente").
"""
from typing import Optional


def _seguro(numerador: Optional[float], denominador: Optional[float]) -> Optional[float]:
    if numerador is None or denominador is None:
        return None
    if denominador == 0:
        return None
    return numerador / denominador


def custo_total(custo_pessoal=0, custo_medicamento=0, custo_material=0,
                 custo_manutencao=0, custo_administrativo=0) -> float:
    valores = [custo_pessoal, custo_medicamento, custo_material, custo_manutencao, custo_administrativo]
    return sum(v for v in valores if v is not None)


def custo_por_atendimento(custo_total_periodo: Optional[float], qtd_atendimentos: Optional[float]) -> Optional[float]:
    """Custo por atendimento = custo total do período ÷ nº de atendimentos."""
    return _seguro(custo_total_periodo, qtd_atendimentos)


def custo_por_hora_funcionamento(custo_total_periodo: Optional[float], horas_funcionamento: Optional[float]) -> Optional[float]:
    """Custo por hora de funcionamento = custo total do período ÷ horas de funcionamento no período."""
    return _seguro(custo_total_periodo, horas_funcionamento)


def custo_por_classificacao_risco(custo_alocado_categoria: Optional[float], atendimentos_categoria: Optional[float]) -> Optional[float]:
    """Custo por classificação de risco = custo alocado à categoria ÷ atendimentos daquela categoria."""
    return _seguro(custo_alocado_categoria, atendimentos_categoria)


def participacao_custo_pessoal(custo_pessoal: Optional[float], custo_total_periodo: Optional[float]) -> Optional[float]:
    """Participação do custo de pessoal = custo_pessoal ÷ custo total."""
    return _seguro(custo_pessoal, custo_total_periodo)


def produtividade_por_profissional(qtd_atendimentos: Optional[float], nro_profissionais: Optional[float]) -> Optional[float]:
    """Produtividade por profissional = atendimentos ÷ nº de profissionais."""
    return _seguro(qtd_atendimentos, nro_profissionais)


def taxa_ocupacao(atendimentos_realizados: Optional[float], capacidade_teorica: Optional[float]) -> Optional[float]:
    """Taxa de ocupação/capacidade = atendimentos realizados ÷ capacidade teórica."""
    return _seguro(atendimentos_realizados, capacidade_teorica)


def indice_eficiencia_composto(
    custo_por_atend: Optional[float],
    produtividade: Optional[float],
    taxa_ocup: Optional[float],
    custo_por_atend_min: float, custo_por_atend_max: float,
    produtividade_min: float, produtividade_max: float,
    taxa_ocup_min: float, taxa_ocup_max: float,
    peso_custo: float = 0.4, peso_produtividade: float = 0.3, peso_ocupacao: float = 0.3,
) -> Optional[float]:
    """
    Índice de eficiência composto = média ponderada normalizada (0-100) de:
      - custo/atendimento, invertido (menor custo = melhor);
      - produtividade por profissional;
      - taxa de ocupação/capacidade.

    Cada componente é normalizado min-max dentro do conjunto de unidades/períodos
    comparados (os limites min/max devem ser calculados pela camada de página,
    a partir do recorte de dados que está sendo exibido, e passados aqui).
    """
    if custo_por_atend is None or produtividade is None or taxa_ocup is None:
        return None

    def _normaliza(valor, minimo, maximo, inverter=False):
        if maximo == minimo:
            return 50.0  # sem variação no conjunto: nota neutra
        nota = (valor - minimo) / (maximo - minimo) * 100
        return 100 - nota if inverter else nota

    nota_custo = _normaliza(custo_por_atend, custo_por_atend_min, custo_por_atend_max, inverter=True)
    nota_produtividade = _normaliza(produtividade, produtividade_min, produtividade_max)
    nota_ocupacao = _normaliza(taxa_ocup, taxa_ocup_min, taxa_ocup_max)

    soma_pesos = peso_custo + peso_produtividade + peso_ocupacao
    if soma_pesos == 0:
        return None

    indice = (
        nota_custo * peso_custo + nota_produtividade * peso_produtividade + nota_ocupacao * peso_ocupacao
    ) / soma_pesos
    return round(indice, 1)


def variacao_orcado_realizado(custo_realizado: Optional[float], valor_orcado: Optional[float]) -> Optional[float]:
    """Variação orçado x realizado = (custo realizado − valor_orcado) ÷ valor_orcado."""
    if custo_realizado is None or valor_orcado is None:
        return None
    return _seguro(custo_realizado - valor_orcado, valor_orcado)


def custo_marginal_por_atendimento_adicional(soma_custos_variaveis: Optional[float], atendimentos_adicionais: Optional[float]) -> Optional[float]:
    """Custo marginal por atendimento adicional = soma dos custos variáveis ÷ atendimentos adicionais simulados."""
    return _seguro(soma_custos_variaveis, atendimentos_adicionais)


def ponto_equilibrio_operacional(
    custo_fixo_total: Optional[float],
    custo_medio_por_atendimento: Optional[float],
    custo_variavel_medio_por_atendimento: Optional[float],
) -> Optional[float]:
    """Ponto de equilíbrio operacional = custo fixo total do período ÷
    (custo médio por atendimento − custo variável médio por atendimento)."""
    if custo_medio_por_atendimento is None or custo_variavel_medio_por_atendimento is None:
        return None
    margem = custo_medio_por_atendimento - custo_variavel_medio_por_atendimento
    return _seguro(custo_fixo_total, margem)


def separar_custos_fixos_variaveis(parametro_custeio_row: dict) -> dict:
    """
    Dado um registro de parametro_custeio (dict com custo_* e tipo_custo_*),
    retorna {"fixo": soma, "variavel": soma} — usado pelo ponto de equilíbrio
    e pelo custo marginal.
    """
    mapa = {
        "custo_pessoal": "tipo_custo_pessoal",
        "custo_medicamento": "tipo_custo_medicamento",
        "custo_material": "tipo_custo_material",
        "custo_manutencao": "tipo_custo_manutencao",
        "custo_administrativo": "tipo_custo_administrativo",
    }
    fixo, variavel = 0.0, 0.0
    for campo_custo, campo_tipo in mapa.items():
        valor = parametro_custeio_row.get(campo_custo) or 0
        tipo = parametro_custeio_row.get(campo_tipo)
        if tipo == "fixo":
            fixo += valor
        elif tipo == "variável":
            variavel += valor
    return {"fixo": fixo, "variavel": variavel}


def formatar_reais(valor: Optional[float]) -> str:
    if valor is None:
        return "sem dado suficiente"
    return f"R$ {valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def formatar_percentual(valor: Optional[float], casas: int = 1) -> str:
    if valor is None:
        return "sem dado suficiente"
    return f"{valor * 100:.{casas}f}%"
