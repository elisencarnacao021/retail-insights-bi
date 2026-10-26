
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 3.1 - DIAGNÓSTICO DA QUALIDADE DOS DADOS
#
# Fonte: UCI Machine Learning Repository - Online Retail
#
# Objetivo:
# Identificar problemas de qualidade e características da base
# antes de aplicar regras de limpeza e transformação.
#
# IMPORTANTE:
# Este script não altera, exclui ou salva registros.
# ============================================================

from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DO CAMINHO DO ARQUIVO
# ------------------------------------------------------------

# Identifica a raiz do projeto a partir da pasta src.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# Importamos Path da biblioteca pathlib no início do script.
# Path permite trabalhar com caminhos de arquivos e pastas.
# Localiza o arquivo original.
CAMINHO_ARQUIVO = Path(
    r"C:\Portfolio\Retail_Insights\dados\originais\Online Retail.xlsx"
)


# ------------------------------------------------------------
# 2. EXTRAÇÃO - LEITURA DA BASE ORIGINAL
# ------------------------------------------------------------

def carregar_dados():

    # Verifica se o arquivo existe antes da leitura.
    if not CAMINHO_ARQUIVO.is_file():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {CAMINHO_ARQUIVO}"
        )

    # Carrega os dados sem alterar a planilha original.
    df = pd.read_excel(
        CAMINHO_ARQUIVO,
        sheet_name="Online Retail",
        engine="openpyxl"
    )

    print("\nBase original carregada com sucesso!")

    return df


# ------------------------------------------------------------
# 3. DIAGNÓSTICO - ESTRUTURA DA BASE
# ------------------------------------------------------------

def analisar_estrutura(df):

    print("\n========== ESTRUTURA DA BASE ==========")

    print(f"Total de linhas: {len(df):,}")
    print(f"Total de colunas: {len(df.columns)}")

    print("\nTipos de dados:")
    print(df.dtypes.to_string())


# ------------------------------------------------------------
# 4. DIAGNÓSTICO - VALORES AUSENTES
# ------------------------------------------------------------

def analisar_ausentes(df):

    print("\n========== VALORES AUSENTES ==========")

    # Conta valores nulos em cada coluna.
    quantidade = df.isna().sum()

    # Calcula o percentual de ausência.
    percentual = df.isna().mean() * 100

    # Organiza os resultados em uma tabela.
    resumo = pd.DataFrame({
        "Quantidade": quantidade,
        "Percentual (%)": percentual.round(2)
    })

    print(resumo.to_string())

    print(f"\nTotal de células ausentes: {quantidade.sum():,}")


# ------------------------------------------------------------
# 5. DIAGNÓSTICO - DUPLICIDADES
# ------------------------------------------------------------

def analisar_duplicidades(df):

    print("\n========== DUPLICIDADES ==========")

    # Conta registros repetidos além da primeira ocorrência.
    duplicados_excedentes = df.duplicated().sum()

    # Conta todas as linhas pertencentes a grupos duplicados.
    linhas_grupos = df.duplicated(keep=False).sum()

    percentual = duplicados_excedentes / len(df) * 100

    print(f"Registros duplicados excedentes: {duplicados_excedentes:,}")
    print(f"Linhas em grupos duplicados: {linhas_grupos:,}")
    print(f"Percentual excedente: {percentual:.2f}%")

    # Não excluímos registros nesta etapa.
    print("Decisão: duplicidades mantidas para investigação.")


# ------------------------------------------------------------
# 6. DIAGNÓSTICO - CANCELAMENTOS
# ------------------------------------------------------------

def analisar_cancelamentos(df):

    print("\n========== CANCELAMENTOS ==========")

    # Segundo a descrição da UCI, notas iniciadas com C
    # representam transações de cancelamento.
    notas = df["InvoiceNo"].astype("string").str.strip()

    cancelamentos = notas.str.upper().str.startswith(
        "C", na=False
    )

    print(f"Linhas de cancelamento: {cancelamentos.sum():,}")

    print(
        "Notas distintas de cancelamento: "
        f"{notas[cancelamentos].nunique():,}"
    )

    print(
        "Percentual de linhas de cancelamento: "
        f"{cancelamentos.mean() * 100:.2f}%"
    )

    # Ainda não descontamos cancelamentos das vendas.
    print("Decisão: cancelamentos mantidos para investigação.")


# ------------------------------------------------------------
# 7. DIAGNÓSTICO - QUANTIDADES E PREÇOS
# ------------------------------------------------------------

def analisar_valores(df):

    print("\n========== QUANTIDADES ==========")

    quantidade = df["Quantity"]

    print(f"Quantidade negativa: {(quantidade < 0).sum():,}")
    print(f"Quantidade igual a zero: {(quantidade == 0).sum():,}")
    print(f"Quantidade positiva: {(quantidade > 0).sum():,}")

    print(f"Menor quantidade: {quantidade.min()}")
    print(f"Maior quantidade: {quantidade.max()}")

    print("\n========== PREÇOS UNITÁRIOS ==========")

    preco = df["UnitPrice"]

    print(f"Preço negativo: {(preco < 0).sum():,}")
    print(f"Preço igual a zero: {(preco == 0).sum():,}")
    print(f"Preço positivo: {(preco > 0).sum():,}")

    print(f"Menor preço: {preco.min():.2f}")
    print(f"Maior preço: {preco.max():.2f}")

    # Nenhuma correção é realizada neste momento.


# ------------------------------------------------------------
# 8. DIAGNÓSTICO - DATAS E PERÍODO
# ------------------------------------------------------------

def analisar_datas(df):

    print("\n========== PERÍODO DOS DADOS ==========")

    # Converte as datas para uma série de diagnóstico.
    # O DataFrame original permanece inalterado.
    datas = pd.to_datetime(
        df["InvoiceDate"],
        errors="coerce"
    )

    print(f"Primeira transação: {datas.min()}")
    print(f"Última transação: {datas.max()}")

    print(f"Datas inválidas ou ausentes: {datas.isna().sum():,}")

    print(f"Dias distintos com transações: {datas.dt.date.nunique():,}")


# ------------------------------------------------------------
# 9. EXECUÇÃO DO DIAGNÓSTICO
# ------------------------------------------------------------

def main():

    print("\n=======================================")
    print(" RETAIL INSIGHTS - DIAGNÓSTICO INICIAL")
    print("=======================================")

    df = carregar_dados()

    analisar_estrutura(df)
    analisar_ausentes(df)
    analisar_duplicidades(df)
    analisar_cancelamentos(df)
    analisar_valores(df)
    analisar_datas(df)

    print("\n=======================================")
    print(" DIAGNÓSTICO CONCLUÍDO")
    print(" Nenhum registro foi alterado ou excluído.")
    print("=======================================")


# Executa as funções somente quando este arquivo
# é chamado diretamente pelo Python.
if __name__ == "__main__":
    main()
