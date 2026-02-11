import streamlit as st
import time
import plotly.express as px
from modules.data_handler import DataStreamer
from modules.compliance_engine import ComplianceEngine
from modules.stats_engine import calculate_benfords_law # NEU

st.set_page_config(page_title="Sentinel Audit Monitor", layout="wide")

tab_live, tab_stats = st.tabs(["📡 Live Monitoring", "📊 Statistische Revision"])

@st.cache_resource
def get_resources():
    streamer = DataStreamer("data/PS_20174392719_1491204439457_log.csv")
    streamer.load_data()
    return streamer, ComplianceEngine()

streamer, engine = get_resources()

with tab_live:
    # Sidebar
    st.sidebar.header("Control Panel")
    selected_step = st.sidebar.slider("Simuliere Analyse für Step:", 1, 743, 1)
    batch_speed = st.sidebar.slider("Scan-Verzögerung (Sekunden):", 0.5, 3.0, 1.5)
    start_btn = st.sidebar.button("Live Scan starten")

    placeholder = st.empty()

    # Styling-Funktion für die Tabelle
    def highlight_risk(val):
        if val == "HIGH": return 'background-color: rgba(255, 0, 0, 0.3)'
        if val == "MEDIUM": return 'background-color: rgba(255, 165, 0, 0.3)'
        return ''

    if start_btn:
        for batch in streamer.stream_generator(step=selected_step):
            analyzed_batch = engine.process_batch(batch)
            
            with placeholder.container():
                st.subheader(f"Echtzeit-Analyse - Step {selected_step}")
                
                # KPIs mit Risiko-Fokus
                high_risk_count = len(analyzed_batch[analyzed_batch['risk_level'] == "HIGH"])
                
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Transaktionen", len(batch))
                k2.metric("Volumen", f"{batch['amount'].sum():,.2f} €")
                k3.metric("Kritische Warnungen", high_risk_count, delta_color="inverse")
                k4.metric("Integritäts-Fehler", len(analyzed_batch[analyzed_batch['flags'].str.contains("INTEGRITY_ERROR")]))

                # Tabelle mit Highlights anzeigen
                styled_df = analyzed_batch.style.map(
                    highlight_risk, subset=['risk_level']
                )
                
                st.dataframe(styled_df, width="stretch")
                
                # Alarm-Ticker für High Risk
                if high_risk_count > 0:
                    st.error(f"⚠️ {high_risk_count} High-Risk Transaktion(en) im aktuellen Batch identifiziert!")

                time.sleep(batch_speed)

with tab_stats:
    st.header("Forensische Datenanalyse")
    st.info("Diese Analyse betrachtet den gesamten Datensatz auf strukturelle Anomalien.")

    if st.button("Gesamtanalyse starten"):
        df = streamer.df 
        
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Benford's Law Check")
            benford_df = calculate_benfords_law(df['amount'])
            
            # Plotly Chart
            fig = px.bar(benford_df, x='Ziffer', y=['Tatsächlich', 'Benford'], 
                         barmode='group', title="Abweichung der ersten Ziffer")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Größere Abweichungen deuten auf manipulierte Beträge hin.")

        with col2:
            st.subheader("Risiko-Verteilung nach Transaktionstyp")
            type_counts = df.groupby('type')['amount'].sum().reset_index()
            fig2 = px.pie(type_counts, values='amount', names='type', hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)

        # Zusammenfassung für den Report
        st.divider()
        st.subheader("Prüfungsurteil (Draft)")
        fraud_ratio = (df['isFraud'].sum() / len(df)) * 100
        st.write(f"**Identifizierte Fraud-Quote (Historisch):** {fraud_ratio:.4f}%")
        st.write(f"**Gesamtvolumen der Prüfung:** {df['amount'].sum():,.2f} €")