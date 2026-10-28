# ============================================================
# RETAIL INSIGHTS | ETAPA 5 - DASHBOARD STREAMLIT
# Fonte: UCI Online Retail (2010-12 a 2011-12)
# Executar na raiz: python -m streamlit run app.py
# O app le a base tratada pelo script 05, sem alterar arquivos.
# ============================================================
from pathlib import Path
import pandas as pd
import streamlit as st

# 1. Configuracao da pagina e caminhos relativos (compativeis com deploy)
st.set_page_config(page_title="Retail Insights | BI", page_icon="📊", layout="wide")
RAIZ = Path(__file__).resolve().parent
ARQUIVO = RAIZ / "dados" / "tratados" / "vendas_elegiveis.csv"
FONTE = "UCI Machine Learning Repository — Online Retail (2010–2011)"
COLUNAS = ["InvoiceNo", "StockCode", "Description", "InvoiceDate", "Country",
           "Quantity", "UnitPrice", "Valor_Linha_GBP", "Status_Transacao"]

# 2. Ler apenas o que sera usado; guardar em cache durante a sessao.
@st.cache_data(show_spinner="Carregando dados tratados...")
def carregar_vendas(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(
        caminho, encoding="utf-8-sig", usecols=COLUNAS,
        dtype={"InvoiceNo": "string", "StockCode": "string",
               "Description": "string", "Country": "string"},
        parse_dates=["InvoiceDate"]
    )
    if df.empty:
        raise ValueError("O CSV de vendas está vazio.")
    if df[COLUNAS].isna().any().any():
        # Descricao pode ser ausente sem afetar o valor agregado.
        obrigatorias = [c for c in COLUNAS if c != "Description"]
        if df[obrigatorias].isna().any().any():
            raise ValueError("Há valores ausentes em campos obrigatórios do CSV.")
    if not df["Status_Transacao"].eq("VENDA_VALIDA").all():
        raise ValueError("A base contém registros que não são vendas elegíveis.")
    if not (df["Quantity"] > 0).all() or not (df["UnitPrice"] > 0).all():
        raise ValueError("Foram encontradas quantidades ou preços não positivos.")
    diferenca = (df["Valor_Linha_GBP"] - df["Quantity"] * df["UnitPrice"]).abs()
    if not (diferenca < 0.0001).all():
        raise ValueError("Valor_Linha_GBP não corresponde a Quantity × UnitPrice.")
    return df

# 3. Funcoes analiticas: todos os indicadores recebem a base JA FILTRADA.
def indicadores(df: pd.DataFrame) -> dict:
    pedidos = df.groupby("InvoiceNo")["Valor_Linha_GBP"].sum()
    return {
        "valor": float(df["Valor_Linha_GBP"].sum()),
        "pedidos": int(pedidos.size),
        "unidades": int(df["Quantity"].sum()),
        "ticket_medio": float(pedidos.mean()),
        "mediana": float(pedidos.median()),
    }


def vendas_mensais(df: pd.DataFrame) -> pd.DataFrame:
    base = df.assign(Mes=df["InvoiceDate"].dt.to_period("M").astype(str))
    return base.groupby("Mes", as_index=False).agg(
        Valor_GBP=("Valor_Linha_GBP", "sum"),
        Pedidos=("InvoiceNo", "nunique")
    ).sort_values("Mes")


def vendas_paises(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("Country", as_index=False).agg(
        Valor_GBP=("Valor_Linha_GBP", "sum"),
        Pedidos=("InvoiceNo", "nunique"),
        Unidades=("Quantity", "sum")
    ).sort_values("Valor_GBP", ascending=False)


def vendas_produtos(df: pd.DataFrame) -> pd.DataFrame:
    # CODIGO identifica item; descricao e apenas rotulo de referencia.
    base = df.copy()
    base["Description"] = base["Description"].fillna("Sem descrição").str.strip()
    resumo = base.groupby("StockCode", as_index=False).agg(
        Valor_GBP=("Valor_Linha_GBP", "sum"),
        Unidades=("Quantity", "sum"),
        Pedidos=("InvoiceNo", "nunique")
    )
    descricoes = (base.groupby(["StockCode", "Description"]).size()
                  .reset_index(name="Frequencia")
                  .sort_values(["StockCode", "Frequencia", "Description"],
                               ascending=[True, False, True])
                  .drop_duplicates("StockCode")[["StockCode", "Description"]])
    return resumo.merge(descricoes, on="StockCode", validate="one_to_one")


# Traduções somente para apresentação; os dados e códigos originais não mudam.
PAISES_PT = {
    "United Kingdom": "Reino Unido", "Netherlands": "Países Baixos",
    "EIRE": "Irlanda", "Germany": "Alemanha", "France": "França",
    "Australia": "Austrália", "Spain": "Espanha",
    "Switzerland": "Suíça", "Belgium": "Bélgica", "Sweden": "Suécia",
    "Norway": "Noruega", "Portugal": "Portugal", "Italy": "Itália",
    "Finland": "Finlândia", "Denmark": "Dinamarca", "Austria": "Áustria",
    "Poland": "Polônia", "Japan": "Japão", "Canada": "Canadá",
    "USA": "Estados Unidos", "Brazil": "Brasil", "Greece": "Grécia",
    "Iceland": "Islândia", "Israel": "Israel", "Singapore": "Singapura"
}
PRODUTOS_PT = {
    "22423": "Suporte de bolo de 3 andares",
    "23843": "Artesanato em papel — passarinho",
    "85123A": "Porta-vela de coração branco",
    "47566": "Bandeirolas de festa",
    "85099B": "Sacola grande vermelha retrô",
    "23166": "Pote de cerâmica médio",
    "23084": "Luz noturna de coelho",
    "22086": "Kit de corrente decorativa de Natal",
    "84879": "Enfeite de pássaro colorido",
    "79321": "Luzes decorativas de pimenta",
}

def moeda(valor: float) -> str:
    # Conversão opcional apenas para apresentação; métricas-base em GBP.
    if moeda_escolhida == "BRL (simulação)":
        valor *= taxa_brl
        simbolo = "R$ "
    else:
        simbolo = "£ "
    return simbolo + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def rotulo_moeda() -> str:
    return "R$ (simulação)" if moeda_escolhida == "BRL (simulação)" else "£"


def valor_exibicao(df, coluna="Valor_GBP"):
    return df[coluna] * (taxa_brl if moeda_escolhida == "BRL (simulação)" else 1.0)


def formatar_numero_br(valor, casas=2):
    """Formata somente a APRESENTAÇÃO no padrão brasileiro."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_valor_monetario(valor, codigo):
    simbolo = "R$" if codigo == "BRL" else "£"
    return f"{simbolo} {formatar_numero_br(valor)}"


def tabela_comercial(df, nome_coluna="País"):
    """Tabela gerencial em pt-BR, preservando valores numéricos originais."""
    tabela = pd.DataFrame({
        nome_coluna: df[nome_coluna].astype(str),
        "Vendas em libras (£)": df["Valor_GBP"].apply(
            lambda x: formatar_valor_monetario(x, "GBP")
        ),
        "Pedidos distintos": df["Pedidos"].apply(
            lambda x: formatar_numero_br(x, 0)
        ),
    })
    if "Unidades" in df.columns:
        tabela["Unidades vendidas"] = df["Unidades"].apply(
            lambda x: formatar_numero_br(x, 0)
        )
    if moeda_escolhida == "BRL (simulação)":
        tabela["Vendas convertidas (R$)"] = df["Valor_Exibicao"].apply(
            lambda x: formatar_valor_monetario(x, "BRL")
        )
    return tabela


# 4. Tratamento de problemas de leitura de forma compreensivel.
st.title("📊 Retail Insights | Desempenho Comercial")
st.caption("Análise histórica de vendas elegíveis — moeda original: libra esterlina (GBP)")
if not ARQUIVO.is_file():
    st.error("Base tratada não encontrada em dados/tratados/vendas_elegiveis.csv. "
             "Execute primeiro o script 05 da ETL e mantenha o CSV no projeto.")
    st.stop()
try:
    dados = carregar_vendas(str(ARQUIVO))
except (OSError, ValueError, KeyError, pd.errors.ParserError) as erro:
    st.error(f"Não foi possível carregar a base tratada: {erro}")
    st.stop()

# 5. Filtros globais: data e pais; periodo final e inclusivo.
min_data = dados["InvoiceDate"].min().date()
max_data = dados["InvoiceDate"].max().date()
st.sidebar.header("Filtros")
moeda_escolhida = st.sidebar.radio(
    "Exibição monetária", ["GBP (original)", "BRL (simulação)"],
    help="Os cálculos originais estão em libras esterlinas (GBP)."
)
taxa_brl = 1.0
if moeda_escolhida == "BRL (simulação)":
    taxa_brl = st.sidebar.number_input(
        "Cotação informada: R$ por £1", min_value=0.01,
        value=7.1001, step=0.0001, format="%.4f",
        help="Referência: PTAX de 27/10/2026, R$ 7,1001 por GBP. Cotação manual, não ao vivo."
    )
    st.sidebar.caption("Referência: GBP/BRL, PTAX 27/10/2026 — R$ 7,1001 por £1. Taxa editável e não atualizada automaticamente.")
periodo = st.sidebar.date_input(
    "Período das transações", value=(min_data, max_data),
    min_value=min_data, max_value=max_data
)
paises_disponiveis = sorted(dados["Country"].dropna().unique().tolist())
paises = st.sidebar.multiselect(
    "Países (vazio = todos)", paises_disponiveis,
    format_func=lambda pais: PAISES_PT.get(pais, pais)
)
if not isinstance(periodo, (list, tuple)) or len(periodo) != 2:
    st.info("Selecione a data inicial e a data final para continuar.")
    st.stop()
inicio, fim = periodo
if inicio > fim:
    st.warning("A data inicial deve ser anterior à data final.")
    st.stop()
mascara = dados["InvoiceDate"].dt.date.between(inicio, fim)
if paises:
    mascara &= dados["Country"].isin(paises)
filtrados = dados.loc[mascara].copy()
st.caption(f"Recorte ativo: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y} | "
           f"Países: {', '.join(PAISES_PT.get(p, p) for p in paises) if paises else 'todos'} | "
           f"Linhas: {len(filtrados):,}".replace(",", "."))
if filtrados.empty:
    st.warning("Não há vendas elegíveis para os filtros selecionados.")
    st.stop()

# 6. Navegacao: todas as abas utilizam o mesmo filtro global.
tab_geral, tab_tempo, tab_paises, tab_produtos, tab_metodo = st.tabs([
    "Visão geral", "Evolução temporal", "Países", "Produtos", "Metodologia"
])
with tab_geral:
    st.subheader("Indicadores do período selecionado")
    k = indicadores(filtrados)
    colunas_kpi = st.columns(5)
    for coluna, titulo, valor in zip(colunas_kpi,
            ["Valor bruto elegível", "Pedidos distintos", "Unidades", "Ticket médio", "Mediana por pedido"],
            [moeda(k["valor"]), formatar_numero_br(k["pedidos"], 0),
             formatar_numero_br(k["unidades"], 0),
             moeda(k["ticket_medio"]), moeda(k["mediana"]) ]):
        coluna.metric(titulo, valor)
    st.info("O ticket médio é valor bruto elegível dividido pelo número de notas distintas. "
            "A mediana representa o valor central dos pedidos, menos influenciado por extremos.")

with tab_tempo:
    st.subheader("Evolução mensal do valor bruto elegível")
    mensal = vendas_mensais(filtrados)
    mensal["Valor_Exibicao"] = valor_exibicao(mensal)
    st.bar_chart(mensal.set_index("Mes")["Valor_Exibicao"], y_label=f"Valor bruto ({rotulo_moeda()})", x_label="Mês")
    tabela_mensal = pd.DataFrame({
        "Mês": mensal["Mes"],
        "Vendas em libras (£)": mensal["Valor_GBP"].apply(
            lambda x: formatar_valor_monetario(x, "GBP")
        ),
        "Pedidos distintos": mensal["Pedidos"].apply(
            lambda x: formatar_numero_br(x, 0)
        ),
    })
    if moeda_escolhida == "BRL (simulação)":
        tabela_mensal["Vendas convertidas (R$)"] = mensal["Valor_Exibicao"].apply(
            lambda x: formatar_valor_monetario(x, "BRL")
        )
    st.dataframe(tabela_mensal, hide_index=True, width="stretch")
    st.caption("Dezembro de 2011 possui dados somente até 09/12; "
               "o recorte mensal pode ser parcial conforme o filtro aplicado.")

with tab_paises:
    st.subheader("Concentração das vendas por país")
    pais = vendas_paises(filtrados)
    pais["País"] = pais["Country"].map(lambda p: PAISES_PT.get(p, p))
    pais["Valor_Exibicao"] = valor_exibicao(pais)
    st.bar_chart(pais.head(10).set_index("País")["Valor_Exibicao"],
                 y_label=f"Valor bruto ({rotulo_moeda()})", x_label="País")
    st.dataframe(tabela_comercial(pais, "País"), hide_index=True, width="stretch")
    st.caption("Os valores em GBP são originais. Se selecionado BRL, a coluna R$ é uma conversão simulada pela taxa informada.")
    st.caption("Países são os registrados na base original; UK representa "
               "o mercado doméstico do varejista.")

with tab_produtos:
    st.subheader("Itens por valor e quantidade")
    excluir = st.checkbox("Retirar DOT, POST e M do ranking (frete/manual)", value=True)
    produtos = vendas_produtos(filtrados)
    if excluir:
        produtos = produtos.loc[~produtos["StockCode"].str.upper().isin(["DOT", "POST", "M"])]
    criterio = st.radio("Ordenar ranking por", ["Valor_GBP", "Unidades"], horizontal=True,
                        format_func=lambda x: f"Valor ({rotulo_moeda()})" if x == "Valor_GBP" else "Unidades")
    top = produtos.sort_values(criterio, ascending=False).head(10).copy()
    top["Nome_PT"] = top.apply(
        lambda r: PRODUTOS_PT.get(str(r["StockCode"]), r["Description"]), axis=1
    )
    top["Item"] = top["StockCode"] + " — " + top["Nome_PT"].str.slice(0, 42)
    top["Valor_Exibicao"] = valor_exibicao(top)
    st.bar_chart(top.set_index("Item")["Valor_Exibicao" if criterio == "Valor_GBP" else "Unidades"],
                 y_label=f"Valor bruto ({rotulo_moeda()})" if criterio == "Valor_GBP" else "Unidades",
                 x_label="Itens")
    tabela_itens = pd.DataFrame({
        "Código": top["StockCode"].astype(str),
        "Produto / item": top["Nome_PT"].astype(str),
        "Vendas em libras (£)": top["Valor_GBP"].apply(
            lambda x: formatar_valor_monetario(x, "GBP")
        ),
        "Unidades vendidas": top["Unidades"].apply(
            lambda x: formatar_numero_br(x, 0)
        ),
        "Pedidos distintos": top["Pedidos"].apply(
            lambda x: formatar_numero_br(x, 0)
        ),
    })
    if moeda_escolhida == "BRL (simulação)":
        tabela_itens["Vendas convertidas (R$)"] = top["Valor_Exibicao"].apply(
            lambda x: formatar_valor_monetario(x, "BRL")
        )
    st.dataframe(tabela_itens, hide_index=True, width="stretch")
    st.caption("O código 23843 registra um pedido atípico de 80.995 unidades. "
               "Os demais códigos não foram auditados individualmente; alguns podem ser serviços.")

with tab_metodo:
    st.subheader("Metodologia e limitações")
    st.markdown("""
###

**Pergunta orientadora:** Como o desempenho comercial do
varejo online variou ao longo do período analisado e quais
produtos, países e padrões de transação mais contribuíram
para as vendas registradas?

**Fonte dos dados:** [Online Retail — UCI Machine Learning Repository]
(https://archive.ics.uci.edu/dataset/352/online+retail).
Dados históricos de 01/12/2010 a 09/12/2011.
Moeda original: libra esterlina (GBP).

**ETL — Extração, Transformação e Carregamento:**
A base original possui 541.909 registros. Foram investigados
dados ausentes, duplicidades, cancelamentos, quantidades
negativas, preços negativos e preços zerados.

A análise comercial utiliza 530.104 registros classificados
como `VENDA_VALIDA`, com quantidade e preço positivos
e número de nota fiscal sem indicação de cancelamento.
O campo `CustomerID` não integra a base analítica exportada.

**Limitações da análise:**
Os indicadores representam o valor bruto das vendas elegíveis,
não o lucro nem o faturamento líquido após cancelamentos.

As duplicidades foram sinalizadas e preservadas, pois não
existe identificador único para cada linha de transação.

Há códigos de postagem e serviços, descrições variáveis
e registros atípicos. Dezembro de 2011 é um mês incompleto.

Os resultados são históricos e não permitem estabelecer
causalidade nem prever vendas futuras.

**Aplicação profissional:**
O dashboard permite acompanhar indicadores comerciais,
comparar períodos, identificar mercados relevantes e
analisar a contribuição dos itens registrados.

Uma utilização corporativa exigiria rotinas adicionais
de atualização, controle de qualidade, segurança,
auditoria e governança.

**Observação monetária:**
Os dados originais estão em GBP. Os nomes traduzidos
são apenas rótulos de apresentação. A conversão para
reais é uma simulação com taxa informada manualmente,
não uma cotação oficial.
""")
    st.caption(FONTE + " | Elaboração própria")
    st.caption("Moeda original: libra esterlina (GBP). Traduções são apenas rótulos de apresentação. Conversão BRL é uma simulação pela taxa digitada, não uma cotação oficial.")
