# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 3.3 - TRATAMENTO, VALIDACAO E CARREGAMENTO (ETL)
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo: reproduzir a classificacao comercial, preparar a
# base para analise de vendas e salvar arquivos auditaveis.
# A planilha original NAO sera alterada.
# ============================================================

from pathlib import Path
import numpy as np
import pandas as pd

# ------------------------------------------------------------
# 1. CAMINHOS DO PROJETO
# ------------------------------------------------------------
# O caminho solicitado identifica a planilha no computador.
CAMINHO_ARQUIVO = Path(
    r"C:\Portfolio\Retail_Insights\dados\originais\Online Retail.xlsx"
)
# Os arquivos de saida sao armazenados dentro do projeto.
PASTA_SAIDA = CAMINHO_ARQUIVO.parent.parent / "tratados"


# ------------------------------------------------------------
# 2. EXTRACAO - LEITURA DA BASE ORIGINAL
# ------------------------------------------------------------
def carregar_dados():
    if not CAMINHO_ARQUIVO.is_file():
        raise FileNotFoundError(f"Arquivo nao encontrado: {CAMINHO_ARQUIVO}")
    dados = pd.read_excel(
        CAMINHO_ARQUIVO,
        sheet_name="Online Retail",
        engine="openpyxl",
    )
    colunas_esperadas = [
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country",
    ]
    if list(dados.columns) != colunas_esperadas:
        raise ValueError("Estrutura inesperada: confira as colunas da planilha.")
    print(f"Base original: {len(dados):,} linhas | {len(dados.columns)} colunas")
    return dados


# ------------------------------------------------------------
# 3. TRANSFORMACAO - INDICADORES DE QUALIDADE
# ------------------------------------------------------------
def marcar_qualidade(df):
    dados = df.copy()
    notas = dados["InvoiceNo"].astype("string").str.strip()
    dados["Flag_Cancelamento"] = notas.str.upper().str.startswith("C", na=False)
    dados["Flag_Quantidade_Negativa"] = dados["Quantity"] < 0
    dados["Flag_Preco_Negativo"] = dados["UnitPrice"] < 0
    dados["Flag_Preco_Zero"] = dados["UnitPrice"] == 0
    dados["Flag_Descricao_Ausente"] = dados["Description"].isna()
    dados["Flag_Cliente_Ausente"] = dados["CustomerID"].isna()
    # Compara somente as oito colunas ORIGINAIS.
    dados["Flag_Duplicidade"] = df.duplicated(keep=False)
    return dados

# ------------------------------------------------------------
#  4. TRANSFORMACAO - CLASSIFICACAO DE TRANSACOES
# ------------------------------------------------------------
def classificar_transacoes(dados):
    condicoes = [
        dados["Flag_Cancelamento"],
        dados["Flag_Preco_Negativo"],
        dados["Flag_Quantidade_Negativa"],
        dados["Flag_Preco_Zero"],
        (dados["Quantity"] > 0) & (dados["UnitPrice"] > 0),
    ]
    categorias = [
        "CANCELAMENTO", "AJUSTE_PRECO_NEGATIVO",
        "QUANTIDADE_NEGATIVA_SEM_C", "PRECO_ZERO", "VENDA_VALIDA",
    ]
    dados["Status_Transacao"] = np.select(
        condicoes, categorias, default="PENDENTE_ANALISE"
    )
    return dados


# ------------------------------------------------------------
# 5. TRANSFORMACAO - BASE PARA ANALISE COMERCIAL
# ------------------------------------------------------------
def preparar_vendas(dados):
    vendas = dados.loc[dados["Status_Transacao"] == "VENDA_VALIDA"].copy()
    # A data ja existe na planilha, mas convertemos explicitamente
    # para que o procedimento seja reproduzivel.
    vendas["InvoiceDate"] = pd.to_datetime(vendas["InvoiceDate"], errors="coerce")
    if vendas["InvoiceDate"].isna().any():
        raise ValueError("Existem datas invalidas na base de vendas.")
    vendas["Data_Venda"] = vendas["InvoiceDate"].dt.strftime("%Y-%m-%d")
    vendas["Ano"] = vendas["InvoiceDate"].dt.year
    vendas["Mes"] = vendas["InvoiceDate"].dt.month
    vendas["Ano_Mes"] = vendas["InvoiceDate"].dt.strftime("%Y-%m")
    # Moeda original: GBP. Nao representa lucro nem valores liquidos.
    vendas["Valor_Linha_GBP"] = vendas["Quantity"] * vendas["UnitPrice"]
    # CustomerID nao e necessario para as perguntas agregadas do projeto.
    # Retiramos o identificador dos arquivos tratados exportados.
    return vendas.drop(columns=["CustomerID"])


# ------------------------------------------------------------
# 6. VALIDACOES - RECONCILIACAO DE REGISTROS
# ------------------------------------------------------------
def validar(df_original, dados, vendas):
    print("\n========== VALIDACAO ==========")
    assert len(dados) == len(df_original), "A classificacao perdeu linhas."
    assert not (dados["Status_Transacao"] == "PENDENTE_ANALISE").any(), "Ha linhas pendentes."
    contagem = dados["Status_Transacao"].value_counts()
    print("Status da base:")
    print(contagem.to_string())
    print(f"Total classificado: {contagem.sum():,}")
    print(f"Linhas de vendas elegiveis: {len(vendas):,}")
    assert len(vendas) == (dados["Status_Transacao"] == "VENDA_VALIDA").sum()
    assert (vendas["Quantity"] > 0).all()
    assert (vendas["UnitPrice"] > 0).all()
    assert (vendas["Valor_Linha_GBP"] > 0).all()
    assert "CustomerID" not in vendas.columns
    # O total nao e uma conclusao final sobre faturamento, pois
    # duplicidades e outras limitacoes permanecem sinalizadas.
    print(f"Valor bruto das linhas elegiveis (GBP): {vendas['Valor_Linha_GBP'].sum():,.2f}")
    print(f"Vendas elegiveis em grupos duplicados: {vendas['Flag_Duplicidade'].sum():,}")
    print("Integridade e regras comerciais: OK")
    return contagem


# ------------------------------------------------------------
# 7. CARREGAMENTO - GERACAO DOS ARQUIVOS TRATADOS
# ------------------------------------------------------------
def salvar_resultados(dados, vendas, contagem):
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    # Somente as vendas elegiveis sao exportadas para a proxima EDA.
    # A classificacao de toda a base pode ser reproduzida pelo script.
    caminho_vendas = PASTA_SAIDA / "vendas_elegiveis.csv"
    caminho_resumo = PASTA_SAIDA / "resumo_status.csv"
    vendas.to_csv(caminho_vendas, index=False, encoding="utf-8-sig")
    (contagem.rename_axis("Status_Transacao")
     .reset_index(name="Quantidade")
     .to_csv(caminho_resumo, index=False, encoding="utf-8-sig"))
    print("\n========== ARQUIVOS GERADOS ==========")
    print(f"Vendas: {caminho_vendas}")
    print(f"Resumo dos status: {caminho_resumo}")
    assert caminho_vendas.is_file() and caminho_vendas.stat().st_size > 0
    assert caminho_resumo.is_file() and caminho_resumo.stat().st_size > 0
    print("Arquivos salvos e encontrados: OK")


# ------------------------------------------------------------
# 8. EXECUCAO PRINCIPAL
# ------------------------------------------------------------
def main():
    print("=======================================")
    print(" RETAIL INSIGHTS - ETL / ETAPA 3.3")
    print("=======================================")
    original = carregar_dados()
    dados = marcar_qualidade(original)
    dados = classificar_transacoes(dados)
    vendas = preparar_vendas(dados)
    contagem = validar(original, dados, vendas)
    salvar_resultados(dados, vendas, contagem)
    print("\nETL concluida. Planilha original preservada.")


if __name__ == "__main__":
    main()