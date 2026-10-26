
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 3.2 - CLASSIFICAÇÃO DAS TRANSAÇÕES
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Classificar os registros conforme suas características
# comerciais e criar indicadores de qualidade dos dados.
#
# Decisões:
# 1. Preservar os registros originais.
# 2. Separar cancelamentos das vendas.
# 3. Identificar ajustes e preços zerados.
# 4. Sinalizar duplicidades e informações ausentes.
# 5. Validar se todos os registros foram classificados.
#
# IMPORTANTE:
# Nenhuma linha será excluída.
# Nenhum arquivo será gravado nesta etapa.
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DO CAMINHO DO ARQUIVO
# ------------------------------------------------------------

# Path permite trabalhar com caminhos de arquivos.
# O prefixo r preserva as barras utilizadas pelo Windows.

CAMINHO_ARQUIVO = Path(
    r"C:\Portfolio\Retail_Insights\dados\originais\Online Retail.xlsx"
)


# ------------------------------------------------------------
# 2. EXTRAÇÃO - CARREGAMENTO DOS DADOS
# ------------------------------------------------------------

def carregar_dados():

    # Verifica a existência da planilha original.
    if not CAMINHO_ARQUIVO.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {CAMINHO_ARQUIVO}"
        )

    # Lê a planilha original com Pandas.
    df = pd.read_excel(
        CAMINHO_ARQUIVO,
        sheet_name="Online Retail",
        engine="openpyxl"
    )

    print(f"\nBase carregada: {len(df):,} registros")

    return df


# ------------------------------------------------------------
# 3. TRANSFORMAÇÃO - CRIAÇÃO DOS INDICADORES DE QUALIDADE
# ------------------------------------------------------------

def criar_indicadores_qualidade(df):

    # Trabalha com uma cópia independente do DataFrame.
    # A planilha original permanece inalterada.
    dados = df.copy()

    # Converte as notas em texto para identificar a letra C.
    notas = dados["InvoiceNo"].astype("string").str.strip()

    # Marca registros associados a cancelamentos.
    dados["Flag_Cancelamento"] = (
        notas.str.upper().str.startswith("C", na=False)
    )

    # Identifica quantidades negativas.
    dados["Flag_Quantidade_Negativa"] = (
        dados["Quantity"] < 0
    )

    # Identifica preços negativos.
    dados["Flag_Preco_Negativo"] = (
        dados["UnitPrice"] < 0
    )

    # Identifica preços zerados.
    dados["Flag_Preco_Zero"] = (
        dados["UnitPrice"] == 0
    )

    # Identifica descrições não preenchidas.
    dados["Flag_Descricao_Ausente"] = (
        dados["Description"].isna()
    )

    # Identifica clientes não informados.
    dados["Flag_Cliente_Ausente"] = (
        dados["CustomerID"].isna()
    )

    # Identifica todas as linhas em grupos duplicados.
    # A comparação considera apenas as oito colunas originais,
    # antes da criação dos indicadores.
    dados["Flag_Duplicidade"] = (
        df.duplicated(keep=False)
    )

    return dados


# ------------------------------------------------------------
# 4. TRANSFORMAÇÃO - CLASSIFICAÇÃO COMERCIAL
# ------------------------------------------------------------

def classificar_transacoes(dados):

    # Define as condições de classificação.
    # A primeira condição verdadeira determina o status.

    condicoes = [
        dados["Flag_Cancelamento"],

        dados["Flag_Preco_Negativo"],

        dados["Flag_Quantidade_Negativa"],

        dados["Flag_Preco_Zero"],

        (
            (dados["Quantity"] > 0)
            & (dados["UnitPrice"] > 0)
        )
    ]

    # Define os nomes das categorias na mesma ordem.
    categorias = [
        "CANCELAMENTO",
        "AJUSTE_PRECO_NEGATIVO",
        "QUANTIDADE_NEGATIVA_SEM_C",
        "PRECO_ZERO",
        "VENDA_VALIDA"
    ]

    # Classifica cada registro de forma padronizada.
    dados["Status_Transacao"] = np.select(
        condicoes,
        categorias,
        default="PENDENTE_ANALISE"
    )

    return dados


# ------------------------------------------------------------
# 5. VALIDAÇÃO - DISTRIBUIÇÃO DAS CLASSIFICAÇÕES
# ------------------------------------------------------------

def validar_classificacoes(dados):

    print("\n========== CLASSIFICAÇÃO COMERCIAL ==========")

    # Conta registros em cada categoria.
    resumo = (
        dados["Status_Transacao"]
        .value_counts()
        .rename_axis("Status_Transacao")
        .reset_index(name="Quantidade")
    )

    # Calcula os percentuais sobre a base original.
    resumo["Percentual (%)"] = (
        resumo["Quantidade"] / len(dados) * 100
    ).round(2)

    print(resumo.to_string(index=False))

    # Verifica se todas as linhas receberam classificação.
    total_classificado = resumo["Quantidade"].sum()

    print(f"\nTotal classificado: {total_classificado:,}")

    assert total_classificado == len(dados), (
        "Erro: a classificação não corresponde ao total!"
    )

    # Verifica se existem registros sem classificação definida.
    pendentes = (
        dados["Status_Transacao"] == "PENDENTE_ANALISE"
    ).sum()

    print(f"Registros pendentes: {pendentes:,}")

    assert pendentes == 0, (
        "Existem registros que exigem investigação adicional."
    )

    print("Validação da classificação: OK")


# ------------------------------------------------------------
# 6. VALIDAÇÃO - INDICADORES DE QUALIDADE
# ------------------------------------------------------------

def apresentar_indicadores(dados):

    print("\n========== INDICADORES DE QUALIDADE ==========")

    colunas_indicadores = [
        "Flag_Cancelamento",
        "Flag_Quantidade_Negativa",
        "Flag_Preco_Negativo",
        "Flag_Preco_Zero",
        "Flag_Descricao_Ausente",
        "Flag_Cliente_Ausente",
        "Flag_Duplicidade"
    ]

    # Soma True como 1 e False como 0.
    # Os indicadores podem se sobrepor.
    resumo = dados[colunas_indicadores].sum()

    print(resumo.to_string())

    print(
        "\nObservação: os indicadores podem se sobrepor."
    )


# ------------------------------------------------------------
# 7. VALIDAÇÃO - CONFERÊNCIA DAS VENDAS ELEGÍVEIS
# ------------------------------------------------------------

def conferir_vendas(dados):

    print("\n========== VENDAS ELEGÍVEIS ==========")

    # Seleciona apenas as transações classificadas
    # como vendas para análise posterior.
    vendas = dados.loc[
        dados["Status_Transacao"] == "VENDA_VALIDA"
    ]

    print(f"Linhas elegíveis: {len(vendas):,}")

    # Confirma que não existem cancelamentos,
    # quantidades negativas ou preços não positivos.
    assert not vendas["Flag_Cancelamento"].any()
    assert (vendas["Quantity"] > 0).all()
    assert (vendas["UnitPrice"] > 0).all()

    print("Critérios comerciais básicos: OK")

    # Não calculamos faturamento nesta etapa.
    # As métricas serão desenvolvidas posteriormente.


# ------------------------------------------------------------
# 8. EXECUÇÃO PRINCIPAL
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - CLASSIFICAÇÃO ETL")
    print("=======================================")

    # Etapa 1 - Carregar a base original.
    df = carregar_dados()

    # Etapa 2 - Criar indicadores de qualidade.
    dados = criar_indicadores_qualidade(df)

    # Etapa 3 - Classificar as transações.
    dados = classificar_transacoes(dados)

    # Etapa 4 - Validar os resultados.
    validar_classificacoes(dados)
    apresentar_indicadores(dados)
    conferir_vendas(dados)

    print("\n=======================================")
    print(" CLASSIFICAÇÃO CONCLUÍDA")
    print(" Todos os registros originais preservados.")
    print(" Nenhum arquivo foi gravado.")
    print("=======================================")


# Executa o processo somente quando o script
# é chamado diretamente pelo terminal.
if __name__ == "__main__":
    main()

