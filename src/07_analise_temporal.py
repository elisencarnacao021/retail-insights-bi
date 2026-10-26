
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 4.2 - ANÁLISE TEMPORAL DAS VENDAS
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Investigar a evolução mensal das vendas elegíveis,
# dos pedidos e do ticket médio.
#
# Entrada:
# dados/tratados/vendas_elegiveis.csv
#
# Saída:
# resultados/vendas_mensais.csv
#
# IMPORTANTE:
# A base tratada não será modificada.
# Os resultados serão calculados em libras esterlinas (GBP).
# ============================================================

from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DOS CAMINHOS
# ------------------------------------------------------------

CAMINHO_DADOS = Path(
    r"C:\Portfolio\Retail_Insights\dados\tratados\vendas_elegiveis.csv"
)

PASTA_RESULTADOS = Path(
    r"C:\Portfolio\Retail_Insights\resultados"
)


# ------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS TRATADOS
# ------------------------------------------------------------

def carregar_dados():

    # Confirma a existência do arquivo criado pela ETL.
    if not CAMINHO_DADOS.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {CAMINHO_DADOS}"
        )

    # Carrega os registros de vendas elegíveis.
    # InvoiceNo é texto porque identifica pedidos.
    df = pd.read_csv(
        CAMINHO_DADOS,
        sep=",",
        encoding="utf-8-sig",
        dtype={"InvoiceNo": "string"},
        parse_dates=["InvoiceDate"]
    )

    print(f"\nBase carregada: {len(df):,} registros")

    return df


# ------------------------------------------------------------
# 3. VALIDAÇÃO DAS INFORMAÇÕES
# ------------------------------------------------------------

def validar_dados(df):

    print("\n========== VALIDAÇÃO ==========")

    colunas = [
        "InvoiceNo",
        "InvoiceDate",
        "Quantity",
        "Valor_Linha_GBP",
        "Status_Transacao"
    ]

    # Verifica a existência das colunas necessárias.
    faltantes = [c for c in colunas if c not in df.columns]

    if faltantes:
        raise ValueError(
            f"Colunas ausentes: {faltantes}"
        )

    if df.empty:
        raise ValueError("A base está vazia.")

    # Verifica se todas as transações são elegíveis.
    assert df["Status_Transacao"].eq(
        "VENDA_VALIDA"
    ).all(), "Existem transações não elegíveis."

    # Confere se as informações essenciais estão completas.
    assert df[colunas].notna().all().all(), (
        "Existem valores ausentes em campos obrigatórios."
    )

    print("Integridade dos dados: OK")

    print(
        "Primeira transação elegível:",
        df["InvoiceDate"].min()
    )

    print(
        "Última transação elegível:",
        df["InvoiceDate"].max()
    )


# ------------------------------------------------------------
# 4. PREPARAÇÃO DO PERÍODO DE ANÁLISE
# ------------------------------------------------------------

def preparar_periodo(df):

    # Cria uma cópia para preservar o DataFrame carregado.
    dados = df.copy()

    # Extrai o período mensal no formato ano-mês.
    # O formato YYYY-MM mantém a ordem cronológica.
    dados["Ano_Mes"] = (
        dados["InvoiceDate"].dt.strftime("%Y-%m")
    )

    return dados


# ------------------------------------------------------------
# 5. AGRUPAMENTO DAS VENDAS POR MÊS
# ------------------------------------------------------------

def analisar_vendas_mensais(dados):

    print("\n========== VENDAS MENSAIS ==========")

    # Agrupa todos os registros pelo mês da transação.
    mensal = (
        dados.groupby("Ano_Mes", as_index=False)
        .agg(
            Valor_Vendas_GBP=("Valor_Linha_GBP", "sum"),
            Pedidos_Distintos=("InvoiceNo", "nunique"),
            Unidades_Vendidas=("Quantity", "sum"),
            Dias_Com_Vendas=("InvoiceDate", lambda x:
                            x.dt.normalize().nunique())
        )
    )

    # Calcula o valor médio por pedido em cada mês.
    mensal["Ticket_Medio_GBP"] = (
        mensal["Valor_Vendas_GBP"]
        / mensal["Pedidos_Distintos"]
    )

    # Mede a participação de cada mês no total analisado.
    total_vendas = mensal["Valor_Vendas_GBP"].sum()

    mensal["Participacao_Percentual"] = (
        mensal["Valor_Vendas_GBP"] / total_vendas * 100
    )

    # Organiza cronologicamente os períodos.
    mensal = mensal.sort_values("Ano_Mes")

    print(
        mensal.round(2).to_string(index=False)
    )

    return mensal


# ------------------------------------------------------------
# 6. IDENTIFICAÇÃO DOS MESES DE DESTAQUE
# ------------------------------------------------------------

def identificar_destaques(mensal):

    print("\n========== DESTAQUES TEMPORAIS ==========")

    # Localiza o mês de maior valor de vendas elegíveis.
    maior = mensal.loc[
        mensal["Valor_Vendas_GBP"].idxmax()
    ]

    # Localiza o mês de menor valor.
    menor = mensal.loc[
        mensal["Valor_Vendas_GBP"].idxmin()
    ]

    print(
        f"Maior valor mensal: {maior['Ano_Mes']} | "
        f"GBP {maior['Valor_Vendas_GBP']:,.2f}"
    )

    print(
        f"Menor valor mensal observado: {menor['Ano_Mes']} | "
        f"GBP {menor['Valor_Vendas_GBP']:,.2f}"
    )

    print(
        "\nAtenção: o último mês do conjunto é parcial."
    )
    print(
        "A comparação entre meses deve considerar "
        "a cobertura temporal dos dados."
    )


# ------------------------------------------------------------
# 7. VALIDAÇÃO E EXPORTAÇÃO
# ------------------------------------------------------------

def validar_e_salvar(df, mensal):

    print("\n========== CONFERÊNCIA DOS RESULTADOS ==========")

    # Compara a soma mensal com a soma da base analisada.
    total_original = df["Valor_Linha_GBP"].sum()
    total_mensal = mensal["Valor_Vendas_GBP"].sum()

    diferenca = abs(total_original - total_mensal)

    print(f"Total original (GBP): {total_original:,.2f}")
    print(f"Total mensal (GBP): {total_mensal:,.2f}")

    assert diferenca < 0.01, (
        "Os valores mensais não reconciliam com a base."
    )

    # Confere a quantidade total de unidades.
    assert mensal["Unidades_Vendidas"].sum() == (
        df["Quantity"].sum()
    ), "Divergência na quantidade de unidades."

    print("Reconciliação das vendas e unidades: OK")

    # Garante que a pasta de resultados exista.
    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho_saida = (
        PASTA_RESULTADOS / "vendas_mensais.csv"
    )

    # Registra os resultados mensais em CSV.
    mensal.to_csv(
        caminho_saida,
        index=False,
        encoding="utf-8-sig",
        float_format="%.4f"
    )

    print(f"\nArquivo gerado: {caminho_saida}")


# ------------------------------------------------------------
# 8. EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - EDA / ETAPA 4.2")
    print("=======================================")

    df = carregar_dados()

    validar_dados(df)

    dados = preparar_periodo(df)

    mensal = analisar_vendas_mensais(dados)

    identificar_destaques(mensal)

    validar_e_salvar(df, mensal)

    print("\n=======================================")
    print(" ANÁLISE TEMPORAL CONCLUÍDA")
    print("=======================================")


# Executa somente quando chamado diretamente.
if __name__ == "__main__":
    main()
