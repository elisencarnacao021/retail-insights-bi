
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 4.4 - ANÁLISE DOS PRODUTOS E ITENS COMERCIAIS
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Identificar os itens com maiores valores de vendas,
# unidades vendidas e participação comercial.
#
# Entrada:
# dados/tratados/vendas_elegiveis.csv
#
# Saídas:
# resultados/vendas_por_produto.csv
# resultados/top_10_produtos_valor.csv
# resultados/top_10_produtos_quantidade.csv
#
# IMPORTANTE:
# A base tratada não será alterada.
# Os valores monetários estão em GBP.
# ============================================================

from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DOS CAMINHOS
# ------------------------------------------------------------

# Identifica automaticamente a raiz do projeto.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

CAMINHO_DADOS = (
    RAIZ_PROJETO / "dados" / "tratados"
    / "vendas_elegiveis.csv"
)

PASTA_RESULTADOS = RAIZ_PROJETO / "resultados"


# ------------------------------------------------------------
# 2. CARREGAMENTO DOS DADOS
# ------------------------------------------------------------

def carregar_dados():

    # Verifica se o arquivo da ETL está disponível.
    if not CAMINHO_DADOS.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {CAMINHO_DADOS}"
        )

    # Preserva os códigos dos itens e das notas como texto.
    df = pd.read_csv(
        CAMINHO_DADOS,
        sep=",",
        encoding="utf-8-sig",
        dtype={
            "InvoiceNo": "string",
            "StockCode": "string",
            "Description": "string"
        }
    )

    print(f"\nBase carregada: {len(df):,} registros")

    return df


# ------------------------------------------------------------
# 3. VALIDAÇÃO DA BASE
# ------------------------------------------------------------

def validar_dados(df):

    print("\n========== VALIDAÇÃO DA BASE ==========")

    colunas = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "UnitPrice",
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

    # Confirma que os registros pertencem ao recorte de vendas.
    assert df["Status_Transacao"].eq(
        "VENDA_VALIDA"
    ).all(), "Existem transações não elegíveis."

    # Campos essenciais para o agrupamento.
    essenciais = [
        "InvoiceNo",
        "StockCode",
        "Quantity",
        "UnitPrice",
        "Valor_Linha_GBP"
    ]

    assert df[essenciais].notna().all().all(), (
        "Existem valores ausentes em campos essenciais."
    )

    assert df["StockCode"].str.strip().ne("").all()
    assert (df["Quantity"] > 0).all()
    assert (df["UnitPrice"] > 0).all()

    print("Integridade dos registros comerciais: OK")
    print(f"Códigos distintos: {df['StockCode'].nunique():,}")


# ------------------------------------------------------------
# 4. PADRONIZAÇÃO DAS DESCRIÇÕES
# ------------------------------------------------------------

def preparar_descricoes(df):

    # Cria uma cópia para não modificar os dados carregados.
    dados = df.copy()

    # Padroniza espaços e letras para facilitar a leitura.
    # Não modifica o código do item (StockCode).
    dados["Descricao_Padronizada"] = (
        dados["Description"]
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )

    # Sinaliza descrições ausentes ou vazias.
    dados["Descricao_Padronizada"] = (
        dados["Descricao_Padronizada"]
        .fillna("SEM DESCRICAO")
        .replace("", "SEM DESCRICAO")
    )

    return dados


# ------------------------------------------------------------
# 5. AGRUPAMENTO DOS ITENS POR CÓDIGO
# ------------------------------------------------------------

def analisar_produtos(dados):

    print("\n========== ANÁLISE DOS PRODUTOS ==========")

    # Consolida as informações pelo código do item.
    resumo = (
        dados.groupby("StockCode", as_index=False)
        .agg(
            Valor_Vendas_GBP=("Valor_Linha_GBP", "sum"),
            Unidades_Vendidas=("Quantity", "sum"),
            Pedidos_Distintos=("InvoiceNo", "nunique"),
            Descricoes_Distintas=(
                "Descricao_Padronizada", "nunique"
            )
        )
    )

    # Seleciona a descrição mais frequente de cada código.
    # Em caso de empate, utiliza ordem alfabética.
    frequencias = (
        dados.groupby(
            ["StockCode", "Descricao_Padronizada"],
            as_index=False
        )
        .size()
    )

    descricoes = (
        frequencias.sort_values(
            ["StockCode", "size", "Descricao_Padronizada"],
            ascending=[True, False, True]
        )
        .drop_duplicates(subset="StockCode")
        [["StockCode", "Descricao_Padronizada"]]
        .rename(
            columns={
                "Descricao_Padronizada": "Descricao_Referencia"
            }
        )
    )

    # Adiciona uma descrição de referência ao agrupamento.
    resumo = resumo.merge(
        descricoes,
        on="StockCode",
        how="left",
        validate="one_to_one"
    )

    # Calcula o preço médio ponderado pelas unidades.
    # É diferente da média simples dos preços das linhas.
    resumo["Preco_Medio_Ponderado_GBP"] = (
        resumo["Valor_Vendas_GBP"]
        / resumo["Unidades_Vendidas"]
    )

    # Calcula a participação de cada item nas vendas.
    valor_total = dados["Valor_Linha_GBP"].sum()

    resumo["Participacao_Percentual"] = (
        resumo["Valor_Vendas_GBP"]
        / valor_total * 100
    )

    # Ordena os itens pelo valor bruto de vendas.
    resumo = (
        resumo.sort_values(
            ["Valor_Vendas_GBP", "StockCode"],
            ascending=[False, True]
        )
        .reset_index(drop=True)
    )

    print(
        f"Códigos analisados: {len(resumo):,}"
    )

    print(
        "Códigos com mais de uma descrição padronizada:",
        (resumo["Descricoes_Distintas"] > 1).sum()
    )

    return resumo


# ------------------------------------------------------------
# 6. IDENTIFICAÇÃO DOS DESTAQUES
# ------------------------------------------------------------

def apresentar_destaques(resumo):

    colunas = [
        "StockCode",
        "Descricao_Referencia",
        "Valor_Vendas_GBP",
        "Unidades_Vendidas",
        "Pedidos_Distintos",
        "Participacao_Percentual"
    ]

    # Ranking pelo maior valor monetário.
    top_valor = resumo.nlargest(
        10, "Valor_Vendas_GBP"
    )

    print("\n========== TOP 10 POR VALOR ==========")

    print(
        top_valor[colunas]
        .round(2)
        .to_string(index=False)
    )

    # Ranking pela quantidade total de unidades.
    top_quantidade = (
        resumo.sort_values(
            ["Unidades_Vendidas", "StockCode"],
            ascending=[False, True]
        )
        .head(10)
    )

    print("\n========== TOP 10 POR QUANTIDADE ==========")

    print(
        top_quantidade[colunas]
        .round(2)
        .to_string(index=False)
    )

    return top_valor, top_quantidade


# ------------------------------------------------------------
# 7. VALIDAÇÃO DOS AGRUPAMENTOS
# ------------------------------------------------------------

def validar_resultados(dados, resumo):

    print("\n========== RECONCILIAÇÃO ==========")

    valor_base = dados["Valor_Linha_GBP"].sum()

    valor_produtos = resumo["Valor_Vendas_GBP"].sum()

    unidades_base = dados["Quantity"].sum()

    unidades_produtos = resumo["Unidades_Vendidas"].sum()

    # A soma dos agrupamentos deve reconciliar com a base.
    assert abs(valor_base - valor_produtos) < 0.01, (
        "Divergência no valor de vendas por produto."
    )

    assert unidades_base == unidades_produtos, (
        "Divergência nas unidades por produto."
    )

    assert abs(
        resumo["Participacao_Percentual"].sum() - 100
    ) < 0.000001, (
        "Divergência nas participações percentuais."
    )

    print(f"Valor original (GBP): {valor_base:,.2f}")
    print(f"Valor agrupado (GBP): {valor_produtos:,.2f}")
    print(f"Unidades reconciliadas: {unidades_base:,}")
    print("Validação dos resultados: OK")

    # Um pedido pode conter diversos produtos.
    # Por isso, não somamos pedidos distintos por item
    # para estimar o total geral de pedidos.


# ------------------------------------------------------------
# 8. EXPORTAÇÃO DOS RESULTADOS
# ------------------------------------------------------------

def salvar_resultados(
    resumo, top_valor, top_quantidade
):

    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    # Exporta a análise completa por código.
    resumo.to_csv(
        PASTA_RESULTADOS / "vendas_por_produto.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.4f"
    )

    # Exporta os 10 principais itens por valor.
    top_valor.to_csv(
        PASTA_RESULTADOS / "top_10_produtos_valor.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.4f"
    )

    # Exporta os 10 principais itens por quantidade.
    top_quantidade.to_csv(
        PASTA_RESULTADOS / "top_10_produtos_quantidade.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.4f"
    )

    print("\nArquivos gerados:")
    print("resultados/vendas_por_produto.csv")
    print("resultados/top_10_produtos_valor.csv")
    print("resultados/top_10_produtos_quantidade.csv")


# ------------------------------------------------------------
# 9. EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - EDA / ETAPA 4.4")
    print("=======================================")

    dados = carregar_dados()

    validar_dados(dados)

    dados = preparar_descricoes(dados)

    resumo = analisar_produtos(dados)

    top_valor, top_quantidade = (
        apresentar_destaques(resumo)
    )

    validar_resultados(dados, resumo)

    salvar_resultados(
        resumo, top_valor, top_quantidade
    )

    print("\n=======================================")
    print(" ANÁLISE DOS PRODUTOS CONCLUÍDA")
    print("=======================================")


# Executa as funções somente quando este arquivo
# é chamado diretamente pelo Python.
if __name__ == "__main__":
    main()

