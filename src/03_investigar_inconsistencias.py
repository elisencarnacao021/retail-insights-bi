
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 3.2 - INVESTIGAÇÃO DAS INCONSISTÊNCIAS
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Investigar registros que precisam de tratamento antes
# de calcular indicadores comerciais.
#
# IMPORTANTE:
# Nenhum registro será alterado ou excluído.
# ============================================================

from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DO CAMINHO
# ------------------------------------------------------------

# Caminho do arquivo original no computador.
CAMINHO_ARQUIVO = Path(
    r"C:\Portfolio\Retail_Insights\dados\originais\Online Retail.xlsx"
)


# ------------------------------------------------------------
# 2. EXTRAÇÃO - CARREGAMENTO DOS DADOS
# ------------------------------------------------------------

def carregar_dados():

    # Verifica se o arquivo está disponível.
    if not CAMINHO_ARQUIVO.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {CAMINHO_ARQUIVO}"
        )

    # Lê a planilha, mantendo a base original intacta.
    df = pd.read_excel(
        CAMINHO_ARQUIVO,
        sheet_name="Online Retail",
        engine="openpyxl"
    )

    print(f"\nBase carregada: {len(df):,} registros")

    return df


# ------------------------------------------------------------
# 3. INVESTIGAÇÃO DOS CANCELAMENTOS
# ------------------------------------------------------------

def investigar_cancelamentos(df):

    print("\n========== CANCELAMENTOS ==========")

    # Identifica notas fiscais iniciadas pela letra C.
    notas = df["InvoiceNo"].astype("string").str.strip()

    canceladas = notas.str.upper().str.startswith(
        "C", na=False
    )

    # Identifica quantidades negativas.
    negativas = df["Quantity"] < 0

    print(
        "Cancelamentos com quantidade negativa:",
        (canceladas & negativas).sum()
    )

    print(
        "Cancelamentos com quantidade positiva:",
        (canceladas & (df["Quantity"] > 0)).sum()
    )

    print(
        "Quantidade negativa sem nota de cancelamento:",
        (~canceladas & negativas).sum()
    )

    # Mostra exemplos para auxiliar a interpretação.
    colunas = [
        "InvoiceNo", "StockCode", "Description",
        "Quantity", "UnitPrice"
    ]

    print("\nExemplos de quantidades negativas:")
    print(
        df.loc[negativas, colunas]
        .head(10)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# 4. INVESTIGAÇÃO DOS PREÇOS
# ------------------------------------------------------------

def investigar_precos(df):

    print("\n========== PREÇOS INCONSISTENTES ==========")

    colunas = [
        "InvoiceNo", "StockCode", "Description",
        "Quantity", "UnitPrice"
    ]

    # Investiga preços negativos.
    negativos = df["UnitPrice"] < 0

    print("\nRegistros com preço negativo:")
    print(
        df.loc[negativos, colunas]
        .to_string(index=False)
    )

    # Investiga preços iguais a zero.
    zerados = df["UnitPrice"] == 0

    print(f"\nRegistros com preço zero: {zerados.sum():,}")

    print("\nExemplos de preços zerados:")
    print(
        df.loc[zerados, colunas]
        .head(10)
        .to_string(index=False)
    )


# ------------------------------------------------------------
# 5. INVESTIGAÇÃO DAS DESCRIÇÕES AUSENTES
# ------------------------------------------------------------

def investigar_descricoes(df):

    print("\n========== DESCRIÇÕES AUSENTES ==========")

    ausentes = df["Description"].isna()

    print(f"Descrições ausentes: {ausentes.sum():,}")

    colunas = [
        "InvoiceNo", "StockCode", "Description",
        "Quantity", "UnitPrice"
    ]

    print("\nExemplos:")
    print(
        df.loc[ausentes, colunas]
        .head(10)
        .to_string(index=False)
    )

    # Verifica quantos registros sem descrição
    # também possuem preço unitário igual a zero.
    print(
        "\nSem descrição e com preço zero:",
        (ausentes & (df["UnitPrice"] == 0)).sum()
    )


# ------------------------------------------------------------
# 6. INVESTIGAÇÃO DAS DUPLICIDADES
# ------------------------------------------------------------

def investigar_duplicidades(df):

    print("\n========== REGISTROS DUPLICADOS ==========")

    # Identifica todas as linhas de grupos duplicados.
    duplicados = df.duplicated(keep=False)

    print(
        "Linhas pertencentes a grupos duplicados:",
        duplicados.sum()
    )

    # Ordena os exemplos para visualizar repetições.
    colunas = [
        "InvoiceNo", "StockCode", "Description",
        "Quantity", "UnitPrice"
    ]

    exemplos = (
        df.loc[duplicados, colunas]
        .sort_values(
            ["InvoiceNo", "StockCode"],
            kind="stable"
        )
        .head(12)
    )

    print("\nExemplos para investigação:")
    print(exemplos.to_string(index=False))


# ------------------------------------------------------------
# 7. EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - INVESTIGAÇÃO ETL")
    print("=======================================")

    df = carregar_dados()

    investigar_cancelamentos(df)
    investigar_precos(df)
    investigar_descricoes(df)
    investigar_duplicidades(df)

    print("\n=======================================")
    print(" INVESTIGAÇÃO CONCLUÍDA")
    print(" Nenhum registro foi alterado ou excluído.")
    print("=======================================")


# Permite executar o script diretamente pelo terminal.
if __name__ == "__main__":
    main()
    
