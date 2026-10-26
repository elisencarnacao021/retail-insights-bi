
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 4.3 - ANÁLISE GEOGRÁFICA DAS VENDAS
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Investigar a distribuição das vendas elegíveis por país
# e calcular indicadores comerciais por mercado.
#
# Entrada:
# dados/tratados/vendas_elegiveis.csv
#
# Saídas:
# resultados/vendas_por_pais.csv
# resultados/top_10_paises.csv
#
# IMPORTANTE:
# Não altera a base original nem a base tratada.
# Todos os valores monetários estão em GBP.
# ============================================================

from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DOS CAMINHOS
# ------------------------------------------------------------

# Identifica a raiz do projeto a partir da pasta src.
# Assim, evitamos caminhos absolutos dentro do código.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

CAMINHO_DADOS = (
    RAIZ_PROJETO / "dados" / "tratados"
    / "vendas_elegiveis.csv"
)

PASTA_RESULTADOS = RAIZ_PROJETO / "resultados"


# ------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS TRATADOS
# ------------------------------------------------------------

def carregar_dados():

    # Verifica se o arquivo da ETL está disponível.
    if not CAMINHO_DADOS.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {CAMINHO_DADOS}"
        )

    # Carrega apenas os dados elegíveis para vendas.
    # InvoiceNo é mantido como texto, pois identifica
    # notas fiscais e não representa uma quantidade.
    df = pd.read_csv(
        CAMINHO_DADOS,
        sep=",",
        encoding="utf-8-sig",
        dtype={
            "InvoiceNo": "string",
            "Country": "string"
        }
    )

    print(f"\nBase carregada: {len(df):,} registros")

    return df


# ------------------------------------------------------------
# 3. VALIDAÇÃO DA BASE
# ------------------------------------------------------------

def validar_dados(df):

    print("\n========== VALIDAÇÃO DA BASE ==========")

    # Campos necessários para a análise geográfica.
    colunas = [
        "InvoiceNo",
        "Country",
        "Quantity",
        "Valor_Linha_GBP",
        "Status_Transacao"
    ]

    faltantes = [c for c in colunas if c not in df.columns]

    if faltantes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {faltantes}"
        )

    if df.empty:
        raise ValueError("A base está vazia.")

    # Confirma que só há vendas elegíveis.
    assert df["Status_Transacao"].eq(
        "VENDA_VALIDA"
    ).all(), "Existem registros não elegíveis."

    # Confirma a ausência de nulos nas colunas analisadas.
    assert df[colunas].notna().all().all(), (
        "Existem dados ausentes em campos obrigatórios."
    )

    # Confere se os países estão preenchidos.
    assert df["Country"].str.strip().ne("").all(), (
        "Existem países com nome vazio."
    )

    # Garante valores positivos no recorte comercial.
    assert (df["Quantity"] > 0).all()
    assert (df["Valor_Linha_GBP"] > 0).all()

    print("Estrutura e critérios comerciais: OK")

    print(
        "Países distintos:",
        df["Country"].nunique()
    )


# ------------------------------------------------------------
# 4. AGRUPAMENTO DAS VENDAS POR PAÍS
# ------------------------------------------------------------

def analisar_paises(df):

    print("\n========== VENDAS POR PAÍS ==========")

    # Agrupa os registros pelo país informado na base.
    resumo = (
        df.groupby("Country", as_index=False)
        .agg(
            Valor_Vendas_GBP=("Valor_Linha_GBP", "sum"),
            Pedidos_Distintos=("InvoiceNo", "nunique"),
            Unidades_Vendidas=("Quantity", "sum")
        )
    )

    # Calcula o valor médio por nota dentro de cada país.
    resumo["Ticket_Medio_GBP"] = (
        resumo["Valor_Vendas_GBP"]
        / resumo["Pedidos_Distintos"]
    )

    # Calcula quanto cada país representa no total.
    valor_total = resumo["Valor_Vendas_GBP"].sum()

    resumo["Participacao_Percentual"] = (
        resumo["Valor_Vendas_GBP"] / valor_total * 100
    )

    # Ordena do maior para o menor valor vendido.
    resumo = resumo.sort_values(
        "Valor_Vendas_GBP",
        ascending=False
    ).reset_index(drop=True)

    print("\nDez principais países:")
    print(
        resumo.head(10)
        .round(2)
        .to_string(index=False)
    )

    return resumo


# ------------------------------------------------------------
# 5. COMPARAÇÃO ENTRE REINO UNIDO E DEMAIS PAÍSES
# ------------------------------------------------------------

def comparar_mercados(resumo):

    print("\n========== CONCENTRAÇÃO GEOGRÁFICA ==========")

    # Localiza o Reino Unido.
    reino_unido = resumo.loc[
        resumo["Country"] == "United Kingdom"
    ]

    if reino_unido.empty:
        print("Reino Unido não encontrado na base.")
        return

    # Calcula a participação do Reino Unido.
    valor_reino_unido = (
        reino_unido["Valor_Vendas_GBP"].iloc[0]
    )

    valor_total = resumo["Valor_Vendas_GBP"].sum()

    participacao_reino_unido = (
        valor_reino_unido / valor_total * 100
    )

    # Calcula a participação conjunta dos demais países.
    valor_outros = valor_total - valor_reino_unido

    participacao_outros = (
        valor_outros / valor_total * 100
    )

    print(
        f"Reino Unido (GBP): {valor_reino_unido:,.2f}"
    )

    print(
        f"Participação Reino Unido: "
        f"{participacao_reino_unido:.2f}%"
    )

    print(
        f"Demais países (GBP): {valor_outros:,.2f}"
    )

    print(
        f"Participação demais países: "
        f"{participacao_outros:.2f}%"
    )


# ------------------------------------------------------------
# 6. VALIDAÇÃO DOS RESULTADOS
# ------------------------------------------------------------

def validar_resultados(df, resumo):

    print("\n========== RECONCILIAÇÃO ==========")

    # Compara o valor da base com os totais por país.
    valor_base = df["Valor_Linha_GBP"].sum()

    valor_paises = resumo["Valor_Vendas_GBP"].sum()

    assert abs(valor_base - valor_paises) < 0.01, (
        "Divergência na soma das vendas por país."
    )

    # Verifica a soma das quantidades.
    assert resumo["Unidades_Vendidas"].sum() == (
        df["Quantity"].sum()
    ), "Divergência na quantidade de unidades."

    # Confirma participação total de 100%.
    assert abs(
        resumo["Participacao_Percentual"].sum() - 100
    ) < 0.000001, (
        "Participações percentuais inconsistentes."
    )

    # Pedidos podem aparecer em mais de um país.
    # Portanto, não presumimos que a soma dos pedidos
    # por país seja igual ao total global distinto.
    print(
        f"Valor original (GBP): {valor_base:,.2f}"
    )

    print(
        f"Valor por países (GBP): {valor_paises:,.2f}"
    )

    print("Reconciliação dos valores e unidades: OK")


# ------------------------------------------------------------
# 7. EXPORTAÇÃO DOS RESULTADOS
# ------------------------------------------------------------

def salvar_resultados(resumo):

    # Cria a pasta de resultados, caso não exista.
    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    # Salva a análise completa por país.
    resumo.to_csv(
        PASTA_RESULTADOS / "vendas_por_pais.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.4f"
    )

    # Salva os 10 países com maior valor de vendas.
    resumo.head(10).to_csv(
        PASTA_RESULTADOS / "top_10_paises.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.4f"
    )

    print("\nArquivos gerados com sucesso:")
    print("resultados/vendas_por_pais.csv")
    print("resultados/top_10_paises.csv")


# ------------------------------------------------------------
# 8. EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - EDA / ETAPA 4.3")
    print("=======================================")

    # Carrega os registros preparados pela ETL.
    df = carregar_dados()

    # Verifica se a base está adequada para análise.
    validar_dados(df)

    # Calcula os indicadores comerciais por país.
    resumo = analisar_paises(df)

    # Avalia a concentração geográfica.
    comparar_mercados(resumo)

    # Confere a integridade dos resultados.
    validar_resultados(df, resumo)

    # Exporta as tabelas para uso posterior no BI.
    salvar_resultados(resumo)

    print("\n=======================================")
    print(" ANÁLISE GEOGRÁFICA CONCLUÍDA")
    print("=======================================")


# Executa o programa somente quando chamado diretamente.
if __name__ == "__main__":
    main()

