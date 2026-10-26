
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 4.1 - INDICADORES COMERCIAIS E ESTATÍSTICA DESCRITIVA
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Calcular e validar indicadores comerciais que apoiarão
# a análise exploratória e o dashboard Streamlit.
#
# Indicadores:
# 1. Valor bruto das vendas elegíveis
# 2. Quantidade de pedidos distintos
# 3. Quantidade total de itens vendidos
# 4. Ticket médio por pedido
# 5. Estatísticas descritivas dos pedidos
#
# IMPORTANTE:
# Não modifica a base tratada.
# Não gera gráficos nesta etapa.
# ============================================================

from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DOS CAMINHOS
# ------------------------------------------------------------

# Caminho da base produzida pela ETL.
CAMINHO_DADOS = Path(
    r"C:\Portfolio\Retail_Insights\dados\tratados\vendas_elegiveis.csv"
)

# Pasta para armazenar os resultados das análises.
PASTA_RESULTADOS = Path(
    r"C:\Portfolio\Retail_Insights\resultados"
)


# ------------------------------------------------------------
# 2. CARREGAMENTO DA BASE TRATADA
# ------------------------------------------------------------

def carregar_vendas():

    # Verifica a existência do arquivo tratado.
    if not CAMINHO_DADOS.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {CAMINHO_DADOS}"
        )

    # Lê o CSV gerado pelo script 05.
    # InvoiceNo e StockCode são identificadores,
    # portanto devem ser tratados como texto.
    vendas = pd.read_csv(
        CAMINHO_DADOS,
        sep=",",
        encoding="utf-8-sig",
        dtype={
            "InvoiceNo": "string",
            "StockCode": "string"
        },
        parse_dates=["InvoiceDate"]
    )

    print("\nBase tratada carregada com sucesso!")
    print(f"Registros: {len(vendas):,}")

    return vendas


# ------------------------------------------------------------
# 3. VALIDAÇÃO DA BASE PARA ANÁLISE
# ------------------------------------------------------------

def validar_base(vendas):

    print("\n========== VALIDAÇÃO DA BASE ==========")

    # Colunas necessárias para calcular os indicadores.
    colunas_obrigatorias = [
        "InvoiceNo",
        "Quantity",
        "UnitPrice",
        "InvoiceDate",
        "Valor_Linha_GBP",
        "Status_Transacao"
    ]

    # Verifica se todas as colunas estão disponíveis.
    ausentes = [
        coluna for coluna in colunas_obrigatorias
        if coluna not in vendas.columns
    ]

    if ausentes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {ausentes}"
        )

    # Verifica se existem dados disponíveis.
    if vendas.empty:
        raise ValueError("A base de vendas está vazia.")

    # Todas as transações precisam ser elegíveis.
    assert vendas["Status_Transacao"].eq(
        "VENDA_VALIDA"
    ).all(), "Existem transações não elegíveis."

    # Confirma quantidades e preços positivos.
    assert (vendas["Quantity"] > 0).all()
    assert (vendas["UnitPrice"] > 0).all()

    # Confirma ausência de campos essenciais nulos.
    assert vendas[
        ["InvoiceNo", "Quantity", "UnitPrice",
         "InvoiceDate", "Valor_Linha_GBP"]
    ].notna().all().all()

    # Confere o valor da linha com o cálculo da ETL.
    valor_calculado = (
        vendas["Quantity"] * vendas["UnitPrice"]
    )

    # Considera pequena tolerância para decimais.
    diferenca = (
        vendas["Valor_Linha_GBP"] - valor_calculado
    ).abs()

    assert (diferenca < 0.000001).all(), (
        "Existem divergências no valor das linhas."
    )

    print("Colunas obrigatórias: OK")
    print("Transações elegíveis: OK")
    print("Quantidades e preços: OK")
    print("Valores monetários: OK")


# ------------------------------------------------------------
# 4. CÁLCULO DOS INDICADORES COMERCIAIS
# ------------------------------------------------------------

def calcular_indicadores(vendas):

    print("\n========== INDICADORES COMERCIAIS ==========")

    # Soma o valor de todas as linhas elegíveis.
    valor_bruto = vendas["Valor_Linha_GBP"].sum()

    # Conta notas distintas, evitando contar cada item
    # de uma mesma nota como se fosse um pedido novo.
    total_pedidos = vendas["InvoiceNo"].nunique()

    # Soma a quantidade de unidades vendidas.
    total_itens = vendas["Quantity"].sum()

    # Calcula o valor médio por pedido.
    ticket_medio = valor_bruto / total_pedidos

    print(f"Valor bruto (GBP): {valor_bruto:,.2f}")
    print(f"Pedidos distintos: {total_pedidos:,}")
    print(f"Unidades vendidas: {total_itens:,}")
    print(f"Ticket médio (GBP): {ticket_medio:,.2f}")

    # Organiza os valores em uma tabela reutilizável.
    indicadores = pd.DataFrame({
        "Indicador": [
            "Valor bruto das vendas elegíveis (GBP)",
            "Quantidade de pedidos distintos",
            "Quantidade de unidades vendidas",
            "Ticket médio por pedido (GBP)"
        ],
        "Valor": [
            valor_bruto,
            total_pedidos,
            total_itens,
            ticket_medio
        ]
    })

    return indicadores


# ------------------------------------------------------------
# 5. ESTATÍSTICAS DESCRITIVAS DOS PEDIDOS
# ------------------------------------------------------------

def analisar_pedidos(vendas):

    print("\n========== ESTATÍSTICAS DOS PEDIDOS ==========")

    # Agrupa as linhas por número da nota fiscal.
    # Cada pedido terá um valor monetário consolidado.
    pedidos = (
        vendas.groupby("InvoiceNo", as_index=False)
        .agg(
            Valor_Pedido_GBP=("Valor_Linha_GBP", "sum"),
            Quantidade_Itens=("Quantity", "sum")
        )
    )

    # Calcula medidas estatísticas dos valores dos pedidos.
    estatisticas = (
        pedidos["Valor_Pedido_GBP"]
        .describe()
        .rename("Valor_GBP")
    )

    print("\nDistribuição dos valores por pedido:")
    print(estatisticas.round(2).to_string())

    # A mediana ajuda a identificar o valor central,
    # reduzindo a influência de pedidos muito altos.
    print(
        f"\nMediana por pedido (GBP): "
        f"{pedidos['Valor_Pedido_GBP'].median():,.2f}"
    )

    # Verifica a reconciliação entre pedidos e vendas.
    valor_pedidos = pedidos["Valor_Pedido_GBP"].sum()
    valor_vendas = vendas["Valor_Linha_GBP"].sum()

    assert abs(valor_pedidos - valor_vendas) < 0.01, (
        "Divergência entre o valor dos pedidos e das vendas."
    )

    print("Reconciliação dos valores: OK")

    return pedidos, estatisticas


# ------------------------------------------------------------
# 6. EXPORTAÇÃO DOS RESULTADOS
# ------------------------------------------------------------

def salvar_resultados(indicadores, pedidos, estatisticas):

    # Cria a pasta de resultados, se necessário.
    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    # Salva indicadores para conferência e documentação.
    indicadores.to_csv(
        PASTA_RESULTADOS / "indicadores_comerciais.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # Salva a análise agregada por pedido.
    pedidos.to_csv(
        PASTA_RESULTADOS / "pedidos_agregados.csv",
        index=False,
        encoding="utf-8-sig"
    )

    # Salva as estatísticas descritivas.
    estatisticas.to_csv(
        PASTA_RESULTADOS / "estatisticas_pedidos.csv",
        header=True,
        encoding="utf-8-sig"
    )

    print("\nArquivos de resultados gerados com sucesso!")


# ------------------------------------------------------------
# 7. EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - EDA / ETAPA 4.1")
    print("=======================================")

    # Carrega os dados tratados pela ETL.
    vendas = carregar_vendas()

    # Confere a integridade antes dos cálculos.
    validar_base(vendas)

    # Calcula os principais indicadores comerciais.
    indicadores = calcular_indicadores(vendas)

    # Calcula as estatísticas agregadas por pedido.
    pedidos, estatisticas = analisar_pedidos(vendas)

    # Registra os resultados em arquivos CSV.
    salvar_resultados(indicadores, pedidos, estatisticas)

    print("\n=======================================")
    print(" ANÁLISE DE INDICADORES CONCLUÍDA")
    print("=======================================")


# Executa o script somente quando chamado diretamente.
if __name__ == "__main__":
    main()
