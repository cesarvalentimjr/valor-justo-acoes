import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(layout="wide")
st.title("📊 Estimativa de Valor Justo da Ação com base em Múltiplos")

# Função para buscar informações de um ticker
def buscar_dados_ticker(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception as e:
        st.warning(f"Erro ao buscar dados do ticker {ticker}: {e}")
        return None

# Função para ajustar múltiplos usando média ou mediana
def ajustar_multiplo(multiplo_list, condicao_todos_positivos=True):
    validos = [v for v in multiplo_list if v is not None and (not condicao_todos_positivos or v > 0)]
    if not validos:
        return None, False, False
    media = np.nanmean(validos)
    mediana = np.nanmedian(validos)
    usou_mediana = media > mediana
    return (mediana if usou_mediana else media), usou_mediana, True

# Entrada do ticker principal
ticker_input = st.text_input("Digite o ticker da empresa (ex: AAPL)", value="AAPL").upper()

if ticker_input:
    dados_empresa = buscar_dados_ticker(ticker_input)
    if dados_empresa:
        # Extração de dados principais
        pe = dados_empresa.get("trailingPE")
        ps = dados_empresa.get("priceToSalesTrailing12Months")
        pb = dados_empresa.get("priceToBook")
        net_income = dados_empresa.get("netIncomeToCommon")
        revenue = dados_empresa.get("totalRevenue")
        equity = dados_empresa.get("commonStockEquity")
        shares_outstanding = dados_empresa.get("sharesOutstanding")
        current_price = dados_empresa.get("currentPrice")

        # Entrada dos pares comparáveis
        peers_str = st.text_input("Tickers das empresas comparáveis (separados por vírgula)", value="MSFT,GOOGL,AMZN")
        peers = [ticker.strip().upper() for ticker in peers_str.split(",")]

        # Coleta de múltiplos dos pares
        pe_list, ps_list, pb_list = [], [], []
        for peer in peers:
            peer_dados = buscar_dados_ticker(peer)
            if peer_dados:
                pe_list.append(peer_dados.get("trailingPE"))
                ps_list.append(peer_dados.get("priceToSalesTrailing12Months"))
                pb_list.append(peer_dados.get("priceToBook"))

        # Ajuste dos múltiplos
        pe_avg, pe_usou_mediana, pe_valido = ajustar_multiplo(pe_list, condicao_todos_positivos=True)
        ps_avg, ps_usou_mediana, _ = ajustar_multiplo(ps_list, condicao_todos_positivos=False)
        pb_avg, pb_usou_mediana, _ = ajustar_multiplo(pb_list, condicao_todos_positivos=False)

        # Cálculo do valor justo
        if shares_outstanding:
            fair_values = []
            labels = []

            if pe and net_income and pe_valido:
                fair_values.append((pe_avg * net_income) / shares_outstanding)
                labels.append("P/E")

            if ps and revenue and ps_avg:
                fair_values.append((ps_avg * revenue) / shares_outstanding)
                labels.append("P/S")

            if pb and equity and pb_avg:
                fair_values.append((pb_avg * equity) / shares_outstanding)
                labels.append("P/B")

            if fair_values:
                fair_value = sum(fair_values) / len(fair_values)
                st.subheader(f"📌 Valor Justo Estimado: ${fair_value:.2f}")
                st.markdown(f"**Preço Atual:** ${current_price if current_price else 'N/A'}")
                st.markdown("### 📉 Comparação dos Valores Estimados")
                
                # Gráfico de comparação
                fig = go.Figure([go.Bar(x=labels, y=fair_values, name="Valor Estimado por Múltiplo")])
                if current_price:
                    fig.add_trace(go.Scatter(
                        x=labels, 
                        y=[current_price] * len(fair_values),
                        mode='lines+markers', 
                        name='Preço Atual', 
                        line=dict(color='red', dash='dash')
                    ))
                st.plotly_chart(fig)

                # Mensagens visuais sobre uso de mediana
                if pe_valido:
                    st.markdown(f"**📌 P/E utilizado:** `{pe_avg:.2f}`")
                    if pe_usou_mediana:
                        st.info("ℹ️ Mediana utilizada no lugar da média para o P/E, devido à possível presença de outliers.")
                else:
                    st.warning("**📌 P/E ignorado:** Condições não satisfeitas.")

                if ps_avg:
                    st.markdown(f"**📌 P/S utilizado:** `{ps_avg:.2f}`")
                    if ps_usou_mediana:
                        st.info("ℹ️ Mediana utilizada no lugar da média para o P/S, devido à possível presença de outliers.")
                else:
                    st.warning("**📌 P/S ignorado:** Dados insuficientes.")

                if pb_avg:
                    st.markdown(f"**📌 P/B utilizado:** `{pb_avg:.2f}`")
                    if pb_usou_mediana:
                        st.info("ℹ️ Mediana utilizada no lugar da média para o P/B, devido à possível presença de outliers.")
                else:
                    st.warning("**📌 P/B ignorado:** Dados insuficientes.")
            else:
                st.warning("Não foi possível calcular o valor justo com os dados disponíveis.")
        else:
            st.warning("Número de ações em circulação não disponível.")
    else:
        st.error("Erro ao buscar dados para o ticker fornecido.")





