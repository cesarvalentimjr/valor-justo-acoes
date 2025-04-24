import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📊 Estimativa de Valor Justo da Ação com base em Múltiplos")

ticker_input = st.text_input("Digite o ticker da empresa (ex: AAPL)", value="AAPL").upper()

if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info

        pe = info.get("trailingPE")
        ps = info.get("priceToSalesTrailing12Months")
        pb = info.get("priceToBook")
        net_income = info.get("netIncomeToCommon")
        revenue = info.get("totalRevenue")
        equity = info.get("commonStockEquity")
        shares_outstanding = info.get("sharesOutstanding")

        peers_str = st.text_input("Tickers das empresas comparáveis (separados por vírgula)", value="MSFT,GOOGL,AMZN")
        peers = [ticker.strip().upper() for ticker in peers_str.split(",")]

        pe_list, ps_list, pb_list = [], [], []

        for peer in peers:
            try:
                peer_info = yf.Ticker(peer).info
                pe_list.append(peer_info.get("trailingPE"))
                ps_list.append(peer_info.get("priceToSalesTrailing12Months"))
                pb_list.append(peer_info.get("priceToBook"))
            except:
                pass

        # 🔽 AJUSTE PARA USAR MEDIANA SE A MÉDIA FOR INFLADA
        def ajustar_multiplo(multiplo_list, condicao_todos_positivos=True):
            validos = [v for v in multiplo_list if v is not None and (not condicao_todos_positivos or v > 0)]
            if not validos or (condicao_todos_positivos and len(validos) != len(multiplo_list)):
                return None, False, False
            media = np.nanmean(validos)
            mediana = np.nanmedian(validos)
            usou_mediana = media > mediana
            return (mediana if usou_mediana else media), usou_mediana, True

        pe_avg, pe_usou_mediana, pe_valido = ajustar_multiplo(pe_list, condicao_todos_positivos=True)
        ps_avg, ps_usou_mediana, _ = ajustar_multiplo(ps_list, condicao_todos_positivos=False)
        pb_avg, pb_usou_mediana, _ = ajustar_multiplo(pb_list, condicao_todos_positivos=False)

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
                st.markdown(f"**Preço Atual:** ${info.get('currentPrice', 'N/A')}")
                st.markdown("### 📉 Comparação dos Valores Estimados")
                fig = go.Figure([go.Bar(x=labels, y=fair_values, name="Valor Estimado por Múltiplo")])
                fig.add_trace(go.Scatter(x=labels, y=[info.get("currentPrice")] * len(fair_values),
                                         mode='lines+markers', name='Preço Atual', line=dict(color='red', dash='dash')))
                st.plotly_chart(fig)

                # 🔽 MENSAGENS VISUAIS SOBRE USO DA MEDIANA
                if pe_valido:
                    st.markdown(f"**📌 P/E utilizado:** `{pe_avg:.2f}`")
                    if pe_usou_mediana:
                        st.info("ℹ️ Mediana utilizada no lugar da média para o P/E, devido à possível presença de outliers.")
                else:
                    st.markdown("**📌 P/E:** Ignorado por condições não satisfeitas")

                st.markdown(f"**📌 P/S utilizado:** `{ps_avg:.2f}`")
                if ps_usou_mediana:
                    st.info("ℹ️ Mediana utilizada no lugar da média para o P/S, devido à possível presença de outliers.")

                st.markdown(f"**📌 P/B utilizado:** `{pb_avg:.2f}`")
                if pb_usou_mediana:
                    st.info("ℹ️ Mediana utilizada no lugar da média para o P/B, devido à possível presença de outliers.")
            else:
                st.warning("Não foi possível calcular o valor justo com os dados disponíveis.")
        else:
            st.warning("Número de ações em circulação não disponível.")
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")




