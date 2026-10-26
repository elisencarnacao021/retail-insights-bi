
# ============================================================
# PROJETO: RETAIL INSIGHTS
# ETAPA 2 - VERIFICAÇÃO INICIAL DA FONTE DE DADOS
#
# Objetivo:
# Confirmar a existência, a leitura e a estrutura do arquivo
# original, sem realizar exclusões ou transformações.
# ============================================================

from pathlib import Path
import pandas as pd

# 1. Identificar a pasta principal do projeto.
# O script está localizado dentro da pasta "src".
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

# 2. Definir o caminho do arquivo original.
CAMINHO_ARQUIVO = (
    Path("C:/Portfolio/Retail_Insights/dados/originais/Online Retail.xlsx")
)

# 3. Verificar se o arquivo existe.
if not CAMINHO_ARQUIVO.is_file():
    raise FileNotFoundError(
        f"Arquivo não encontrado: {CAMINHO_ARQUIVO}"
    )

print("Arquivo localizado com sucesso!")

# 4. Carregar a planilha com Pandas.
# A base original não será modificada.
df = pd.read_excel(
    CAMINHO_ARQUIVO,
    sheet_name="Online Retail",
    engine="openpyxl"
)

# 5. Verificar quantidade de linhas e colunas.
print("\nDIMENSÕES DA BASE")
print(f"Linhas: {df.shape[0]:,}")
print(f"Colunas: {df.shape[1]}")

# 6. Listar os nomes das colunas.
print("\nCOLUNAS DISPONÍVEIS")
print(df.columns.tolist())

# 7. Exibir os tipos de dados identificados.
print("\nTIPOS DE DADOS")
print(df.dtypes)

# 8. Exibir uma pequena amostra para inspeção.
print("\nPRIMEIROS CINCO REGISTROS")
print(df.head().to_string(index=False))

print("\nVerificação inicial concluída.")
