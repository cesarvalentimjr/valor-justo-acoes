import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from yahooquery import search

# === CONFIGURAÇÃO DA PÁGINA ===
st.set_page_config(page_title="Calculadora de Preço Justo", layout="centered")

# === TOPO COM LOGO + TÍTULO ===
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    st.image("logopj.png", width=150)

with col_titulo:
    st.markdown("""
        <div style='display: flex; flex-direction: column; justify-content: center; height: 100%;'>
            <h1 style='margin: 0; padding-top: 5px;'>Calculadora de Preço Justo de Ações</h1>
            <p style='margin-top: 0.5em;'>Este app estima o valor justo de uma ação com base nos múltiplos médios de empresas comparáveis (P/E, P/S e P/B).</p>
        </div>
    """, unsafe_allow_html=True)

# === ESTILIZAÇÃO PERSONALIZADA ===
st.markdown("""
    <style>
        .main { background-color: #f5f7fa; }
        h1, h2, h3 { color: #003366; }
        .stButton>button {
            background-color: #004080;
            color: white;
            font-weight: 600;
            border-radius: 10px;
            padding: 0.6em 1.2em;
            margin-top: 0.5em;
        }
        .stButton>button:hover {
            background-color: #0066cc;
            transition: 0.3s ease-in-out;
        }
        .stSelectbox label, .stTextInput label {
            font-weight: 600;
            color: #003366;
        }
        .stMarkdown { font-size: 1.1rem; }
        .stSuccess { background-color: #dff0d8; }
    </style>
""", unsafe_allow_html=True)

# === FUNÇÃO DE BUSCA DE TICKERS ===
def buscar_tickers(nome_empresa):
    try:
        resultados = search(nome_empresa)
        opcoes = []
        if 'quotes' in resultados:
            for r in resultados['quotes']:
                if 'shortname' in r and 'symbol' in r:
                    nome = r['shortname']
                    ticker = r['symbol']
                    opcoes.append(f"{nome} ({ticker})")
        return opcoes
    except Exception:
        return []

# === LAYOUT COM COLUNAS ===
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏢 Empresa-Alvo")
    nome_alvo = st.text_input("🔎 Nome ou ticker:")
    tickers_alvo = buscar_tickers(nome_alvo) if nome_alvo else []
    ticker_target_full = st.selectbox("Selecione a empresa-alvo:", tickers_alvo)
    ticker_target = ticker_target_full.split("(")[-1].replace(")", "") if ticker_target_full else None

with col2:
    st.subheader("📍 Empresas Comparáveis")
    nome_comparavel = st.text_input("🔍 Nome ou ticker da comparável:")
    tickers_comparavel = buscar_tickers(nome_comparavel) if nome_comparavel else []

    if "comparaveis" not in st.session_state:
        st.session_state.comparaveis = []

    ticker_comparavel_full = st.selectbox("Selecione a comparável:", tickers_comparavel)
    ticker_comparavel = ticker_comparavel_full.split("(")[-1].replace(")", "") if ticker_comparavel_full else None

    if ticker_comparavel and ticker_comparavel not in st.session_state.comparaveis:
        if st.button("➕ Adicionar comparável"):
            st.session_state.comparaveis.append(ticker_comparavel)

    if st.session_state.comparaveis:
        remover_comparavel = st.selectbox("❌ Remover comparável:", st.session_state.comparaveis)
        if st.button("Remover selecionada"):
            st.session_state.comparaveis.remove(remover_comparavel)

# === LISTA DE COMPARÁVEIS ADICIONADOS ===
if st.session_state.comparaveis:
    st.markdown("### ✅ Comparáveis adicionadas:")
    st.markdown(", ".join(st.session_state.comparaveis))

# === CÁLCULO ===
if st.button("🧮 Calcular Valor Justo"):
    comparables = st.session_state.comparaveis

    if not ticker_target or not comparables:
        st.warning("Informe a empresa-alvo e pelo menos uma comparável.")
    else:
        try:
            pe_list, ps_list, pb_list = [], [], []

            for ticker in comparables:
                info = yf.Ticker(ticker).info
                pe_list.append(info.get("trailingPE"))
                ps_list.append(info.get("priceToSalesTrailing12Months"))
                pb_list.append(info.get("priceToBook"))

            pe_avg = np.nanmean([v for v in pe_list if v and v > 0])
            ps_avg = np.nanmean([v for v in ps_list if v])
            pb_avg = np.nanmean([v for v in pb_list if v])

            st.markdown(f"**📌 P/E médio (apenas positivos):** `{pe_avg:.2f}`")
            st.markdown(f"**📌 P/S médio:** `{ps_avg:.2f}`")
            st.markdown(f"**📌 P/B médio:** `{pb_avg:.2f}`")

            ticker_obj = yf.Ticker(ticker_target)
            fin = ticker_obj.financials
            bs = ticker_obj.balance_sheet
            info_target = ticker_obj.info

            def buscar(df, nomes):
                for nome in nomes:
                    if nome in df.index:
                        return df.loc[nome].iloc[0]
                return None

            net_income = buscar(fin, ["Net Income", "Net Income Applicable To Common Shares"])
            revenue = buscar(fin, ["Total Revenue", "Revenue"])
            equity = buscar(bs, ["Common Stock Equity", "Total Stockholder Equity", "Stockholders' Equity", "Total Equity", "Ordinary Shareholders Equity"])
            shares = info_target.get("sharesOutstanding")

            st.write("### 📑 Dados encontrados:")
            st.write(f"- Net Income: `{net_income}`")
            st.write(f"- Revenue: `{revenue}`")
            st.write(f"- Equity: `{equity}`")
            st.write(f"- Shares Outstanding: `{shares}`")

            faltando = []
            if not net_income: faltando.append("Net Income")
            if not revenue: faltando.append("Revenue")
            if not equity: faltando.append("Equity")
            if not shares: faltando.append("Shares Outstanding")

            if faltando:
                st.warning("Nem todos os dados necessários foram encontrados:")
                for f in faltando:
                    st.write(f"- ❌ {f}")
            else:
                usar_pe = pe_avg > 0 and net_income and net_income > 0

                val_pe = pe_avg * net_income if usar_pe else None
                val_ps = ps_avg * revenue if ps_avg and revenue else None
                val_pb = pb_avg * equity if pb_avg and equity else None

                valores = [v for v in [val_pe, val_ps, val_pb] if v is not None]
                valor_justo_total = np.mean(valores) if valores else None
                valor_justo_por_acao = valor_justo_total / shares if shares and valor_justo_total else None

                st.subheader("📈 Resultado:")
                if valor_justo_por_acao:
                    st.success(f"Valor justo estimado por ação: **${valor_justo_por_acao:.2f}**")
                else:
                    st.error("Não foi possível calcular o valor justo por ação.")

                dados = {
                    "Empresa-Alvo": ticker_target,
                    "Valor Justo por Ação": valor_justo_por_acao,
                    "P/E Médio": pe_avg if usar_pe else "N/A",
                    "P/S Médio": ps_avg,
                    "P/B Médio": pb_avg
                }
                df_resultado = pd.DataFrame([dados])
                csv = df_resultado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Baixar relatório CSV",
                    data=csv,
                    file_name="resultado_valor_justo.csv",
                    mime="text/csv"
                )

                # Gráfico de comparação
                df_comparacao = pd.DataFrame({
                    "Comparáveis": comparables,
                    "P/E": pe_list,
                    "P/S": ps_list,
                    "P/B": pb_list
                })
                st.subheader("📊 Comparação de Múltiplos")
                st.bar_chart(df_comparacao.set_index("Comparáveis"))

        except Exception as e:
            st.error(f"Erro ao obter dados financeiros: {e}")


