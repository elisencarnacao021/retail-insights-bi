
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 4.5 - VISUALIZAÇÃO DOS RESULTADOS
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Gerar gráficos para apoiar a interpretação das análises
# temporal, geográfica e de itens comerciais.
#
# Entradas:
# resultados/vendas_mensais.csv
# resultados/vendas_por_pais.csv
# resultados/vendas_por_produto.csv
#
# Saídas:
# resultados/graficos/01_vendas_mensais.png
# resultados/graficos/02_vendas_por_pais.png
# resultados/graficos/03_top_produtos.png
#
# IMPORTANTE:
# Não modifica as bases nem os arquivos de análise.
# ============================================================

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Permite salvar figuras sem abrir janelas.

import matplotlib.pyplot as plt
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DAS PASTAS
# ------------------------------------------------------------

# Identifica a raiz a partir da localização deste script.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

PASTA_RESULTADOS = RAIZ_PROJETO / "resultados"

PASTA_GRAFICOS = PASTA_RESULTADOS / "graficos"

# Cria a pasta de gráficos quando necessário.
PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

FONTE = "Fonte: UCI Online Retail | Elaboração própria"


# ------------------------------------------------------------
# 2. CARREGAMENTO DOS RESULTADOS DA EDA
# ------------------------------------------------------------

def carregar_resultado(nome_arquivo, colunas):

    caminho = PASTA_RESULTADOS / nome_arquivo

    # Interrompe a execução caso a análise não exista.
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    df = pd.read_csv(caminho, encoding="utf-8-sig")

    # Valida as colunas utilizadas no gráfico.
    faltantes = [
        coluna for coluna in colunas
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Colunas ausentes em {nome_arquivo}: {faltantes}"
        )

    if df.empty:
        raise ValueError(
            f"O arquivo {nome_arquivo} está vazio."
        )

    return df


# ------------------------------------------------------------
# 3. GRÁFICO 1 - EVOLUÇÃO MENSAL
# ------------------------------------------------------------

def grafico_temporal():

    mensal = carregar_resultado(
        "vendas_mensais.csv",
        ["Ano_Mes", "Valor_Vendas_GBP"]
    )

    # Mantém os períodos em ordem cronológica.
    mensal = mensal.sort_values("Ano_Mes").copy()

    # Converte GBP para milhares, facilitando a leitura.
    mensal["Valor_Mil_GBP"] = (
        mensal["Valor_Vendas_GBP"] / 1000
    )

    rotulos = mensal["Ano_Mes"].astype(str).tolist()

    # Diferencia o último mês, que é parcial.
    cores = [
        "#2478A3" if mes != "2011-12" else "#B5BDC5"
        for mes in rotulos
    ]

    fig, ax = plt.subplots(figsize=(13, 6))

    ax.bar(
        rotulos,
        mensal["Valor_Mil_GBP"],
        color=cores
    )

    ax.set_title(
        "Evolução mensal das vendas elegíveis",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xlabel("Mês da transação")
    ax.set_ylabel("Valor bruto das vendas (£ mil)")

    ax.tick_params(axis="x", rotation=45)

    ax.grid(
        axis="y",
        alpha=0.25,
        linestyle="--"
    )

    ax.set_axisbelow(True)

    fig.text(
        0.08, 0.02,
        FONTE
        + " | Dez/2011: somente até 09/12.",
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.06, 1, 1])

    destino = (
        PASTA_GRAFICOS / "01_vendas_mensais.png"
    )

    fig.savefig(destino, dpi=160)
    plt.close(fig)

    print(f"Gráfico mensal salvo: {destino}")


# ------------------------------------------------------------
# 4. GRÁFICO 2 - VENDAS POR PAÍS
# ------------------------------------------------------------

def grafico_paises():

    paises = carregar_resultado(
        "vendas_por_pais.csv",
        ["Country", "Valor_Vendas_GBP"]
    )

    # Seleciona os dez mercados com maior valor.
    top10 = (
        paises.nlargest(10, "Valor_Vendas_GBP")
        .sort_values("Valor_Vendas_GBP")
        .copy()
    )

    # Usa milhões de GBP no eixo.
    valores = top10["Valor_Vendas_GBP"] / 1_000_000

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.barh(
        top10["Country"],
        valores,
        color="#2478A3"
    )

    ax.set_title(
        "Dez principais países por valor de vendas",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xlabel("Valor bruto das vendas (£ milhões)")
    ax.set_ylabel("País")

    ax.grid(
        axis="x",
        alpha=0.25,
        linestyle="--"
    )

    ax.set_axisbelow(True)

    fig.text(
        0.08, 0.02,
        FONTE + " | Recorte: vendas elegíveis.",
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.06, 1, 1])

    destino = (
        PASTA_GRAFICOS / "02_vendas_por_pais.png"
    )

    fig.savefig(destino, dpi=160)
    plt.close(fig)

    print(f"Gráfico geográfico salvo: {destino}")


# ------------------------------------------------------------
# 5. GRÁFICO 3 - RANKING DE ITENS
# ------------------------------------------------------------

def grafico_produtos():

    produtos = carregar_resultado(
        "vendas_por_produto.csv",
        [
            "StockCode",
            "Descricao_Referencia",
            "Valor_Vendas_GBP"
        ]
    )

    # Exclui apenas lançamentos identificados
    # previamente como postagem ou registro manual.
    # Isso NÃO modifica o CSV original.
    codigos_excluidos = {"DOT", "POST", "M"}

    candidatos = produtos.loc[
        ~produtos["StockCode"].astype(str).str.upper()
        .isin(codigos_excluidos)
    ].copy()

    # Seleciona os dez itens com maior valor.
    top10 = (
        candidatos.nlargest(10, "Valor_Vendas_GBP")
        .sort_values("Valor_Vendas_GBP")
        .copy()
    )

    # Combina código e descrição para identificação.
    top10["Rotulo"] = (
        top10["StockCode"].astype(str)
        + " - "
        + top10["Descricao_Referencia"]
        .fillna("Sem descrição")
        .astype(str)
        .str.slice(0, 32)
    )

    valores = top10["Valor_Vendas_GBP"] / 1000

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.barh(
        top10["Rotulo"],
        valores,
        color="#2478A3"
    )

    ax.set_title(
        "Dez principais itens por valor de vendas",
        fontsize=15,
        fontweight="bold"
    )

    ax.set_xlabel("Valor bruto das vendas (£ mil)")
    ax.set_ylabel("Código e descrição")

    ax.grid(
        axis="x",
        alpha=0.25,
        linestyle="--"
    )

    ax.set_axisbelow(True)

    fig.text(
        0.08, 0.025,
        FONTE
        + " | Excluídos do ranking: DOT, POST e M.",
        fontsize=9
    )

    fig.text(
        0.08, 0.008,
        "Demais códigos não auditados individualmente."
        " O item 23843 contém uma venda atípica.",
        fontsize=9
    )

    fig.tight_layout(rect=[0, 0.075, 1, 1])

    destino = (
        PASTA_GRAFICOS / "03_top_produtos.png"
    )

    fig.savefig(destino, dpi=160)
    plt.close(fig)

    print(f"Gráfico de itens salvo: {destino}")


# ------------------------------------------------------------
# 6. EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - EDA / ETAPA 4.5")
    print("=======================================")

    grafico_temporal()
    grafico_paises()
    grafico_produtos()

    # Confere se todos os arquivos foram produzidos.
    arquivos = [
        "01_vendas_mensais.png",
        "02_vendas_por_pais.png",
        "03_top_produtos.png"
    ]

    for nome in arquivos:
        caminho = PASTA_GRAFICOS / nome

        assert caminho.is_file(), (
            f"Gráfico não encontrado: {nome}"
        )

        assert caminho.stat().st_size > 0, (
            f"Arquivo de gráfico vazio: {nome}"
        )

    print("\nValidação: três gráficos salvos corretamente.")
    print("Nenhuma base de dados foi modificada.")

    print("\n=======================================")
    print(" VISUALIZAÇÕES CONCLUÍDAS")
    print("=======================================")


# Executa o programa somente quando chamado diretamente.
if __name__ == "__main__":
    main()

