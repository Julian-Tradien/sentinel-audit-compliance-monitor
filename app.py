import streamlit as st
import time
import pandas as pd
import plotly.express as px
from modules.data_handler import DataStreamer
from modules.compliance_engine import ComplianceEngine
from modules.stats_engine import calculate_benfords_law, get_performance_report, get_benford_interpretation
from modules.pdf_export import generate_audit_pdf

# Session State Initialisierung
if 'incident_log' not in st.session_state:
    st.session_state.incident_log = pd.DataFrame()

st.set_page_config(page_title="Sentinel Audit Monitor", layout="wide")


@st.cache_resource
def get_resources():
    streamer = DataStreamer("data/PS_20174392719_1491204439457_log.csv")
    streamer.load_data()
    return streamer, ComplianceEngine()

streamer, engine = get_resources()

tab_live, tab_stats = st.tabs(["📡 Live Monitoring", "📊 Statistische Revision"])
    
with tab_live:
    with st.sidebar:
        st.title(" Fraud-Audit Control")
        
        # SEKTION 1: LIVE MONITORING
        st.subheader("📡 Live-Monitoring Steuerung")
        selected_step = st.slider("Simuliere Analyse für Step:", 1, 743, 1)
        batch_speed = st.slider("Scan-Verzögerung (Sekunden):", 0.5, 10.0, 3.0)
        start_btn = st.button("Live Scan starten")
        
        st.divider() # Optische Trennung
        
        # SEKTION 2: REVISIONS-EINSTELLUNGEN
        st.subheader("📊 Revisions-Filter")
        step_range = st.slider(
            "Zeitspanne wählen (Steps):",
            min_value=int(streamer.df['step'].min()),
            max_value=int(streamer.df['step'].max()),
            value=(1, 100)
        )
        st.info("Diese Filter gelten für den Reiter 'Statistische Revision'.")

    placeholder = st.empty()

    # Styling-Funktion für die Tabelle
    def highlight_risk(val):
        if val == "HIGH": return 'background-color: rgba(255, 0, 0, 0.3)'
        if val == "MEDIUM": return 'background-color: rgba(255, 165, 0, 0.3)'
        return ''

    if start_btn:
        for batch in streamer.stream_generator(step=selected_step):
            # Analyse durchführen
            analyzed_batch = engine.process_batch(batch)
            
            # High Risk Daten extrahieren
            current_high_risk = analyzed_batch[analyzed_batch['risk_level'] == "HIGH"].copy()
            
            if not current_high_risk.empty:
                st.session_state.incident_log = pd.concat(
                    [st.session_state.incident_log, current_high_risk], 
                    ignore_index=True
                ).drop_duplicates()

            # UI Aktualisierung
            with placeholder.container():
                st.subheader(f"Echtzeit-Analyse - Step {selected_step}")
                
                # Daten filtern für die Anzeige im aktuellen Batch
                high_risk_count = len(current_high_risk)
                
                # KPIs
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Transaktionen", len(batch))
                k2.metric("Volumen", f"{batch['amount'].sum():,.2f} €")
                k3.metric("Kritische Warnungen", high_risk_count, delta_color="inverse")
                k4.metric("Integritäts-Fehler", len(analyzed_batch[analyzed_batch['flags'].str.contains("INTEGRITY")]))

                # Haupttabelle
                styled_df = analyzed_batch.style.map(
                    highlight_risk, subset=['risk_level']
                )
                st.write("Alle eingehenden Transaktionen (Aktueller Stream):")
                st.dataframe(styled_df, width="stretch", height=450)
                
                # Aktueller Status-Alert
                if high_risk_count > 0:
                    st.error(f"⚠️ {high_risk_count} High-Risk Transaktion(en) im aktuellen Batch identifiziert!")
                else:
                    st.success("✅ Aktueller Batch unauffällig.")

                st.divider()

                # DAS INCIDENT LOG (Die persistente Tabelle)
                st.subheader("Historie der identifizierten Verdachtsfälle (Incident Log)")
                
                if not st.session_state.incident_log.empty:
                    st.write("Diese Fälle müssen manuell durch einen Auditor geprüft werden:")
                    st.dataframe(
                        st.session_state.incident_log, 
                        width="stretch", 
                        height=350
                    )
                else:
                    st.info("Bisher keine kritischen Vorfälle gespeichert.")

                time.sleep(batch_speed)

with tab_stats:
    st.header("📊 Forensische Gesamtrevision")
    
    # --- FIX: FILTERLOGIK ANWENDEN ---
    # Wir nehmen den Original-DF und filtern ihn sofort basierend auf der Sidebar
    # step_range kommt aus deiner Sidebar: st.sidebar.slider(..., value=(1, 100))
    audit_df = streamer.df[
        (streamer.df['step'] >= step_range[0]) & 
        (streamer.df['step'] <= step_range[1])
    ]
    
    st.info(f"Analysierter Zeitraum: Step **{step_range[0]}** bis **{step_range[1]}** "
            f"({len(audit_df):,} Transaktionen)")

    # --- SEKTION 1: Mathematische Forensik ---
    st.subheader("1. Benford's Law Analyse")
    # WICHTIG: Nutze audit_df statt full_df
    benford_df = calculate_benfords_law(audit_df['amount'])
    fig_benford = px.bar(benford_df, x='Ziffer', y=['Tatsächlich', 'Benford'], barmode='group')
    st.plotly_chart(fig_benford, use_container_width=True)

    message, level = get_benford_interpretation(benford_df)
    if level == "success": st.success(message)
    elif level == "warning": st.warning(message)
    else: st.error(message)

    st.divider()

    # --- SEKTION 2: Forensische Prüfung der Konten-Leerung ---
    st.subheader("2. Audit-Check: Effizienz der 100%-Liquidation")
    # WICHTIG: Nutze audit_df statt full_df
    mask_100_percent = (audit_df['amount'] == audit_df['oldbalanceOrg']) & (audit_df['oldbalanceOrg'] > 0)
    liquidation_df = audit_df[mask_100_percent].copy()
    
    tp_count = len(liquidation_df[liquidation_df['isFraud'] == 1])
    fp_count = len(liquidation_df[liquidation_df['isFraud'] == 0])

    plot_data = pd.DataFrame({
        'Kategorie': ['Betrug (Volltreffer)', 'Legal (Fehlalarm)'],
        'Anzahl': [tp_count, fp_count],
        'Status': ['Fraud', 'Clean']
    })

    fig_liq_bar = px.bar(
        plot_data, x='Anzahl', y='Kategorie', color='Status',
        orientation='h', text='Anzahl',
        title="Validierung der 100%-Liquidation-Regel (Zeitraum-spezifisch)",
        color_discrete_map={'Fraud': '#ef553b', 'Clean': '#636efa'}
    )
    fig_liq_bar.update_traces(textposition='outside')
    st.plotly_chart(fig_liq_bar, use_container_width=True)

    # Abdeckung berechnen bezogen auf den Zeitraum
    total_fraud_in_period = audit_df['isFraud'].sum()
    fraud_coverage_pct = (tp_count / total_fraud_in_period) * 100 if total_fraud_in_period > 0 else 0

    st.success(f"""
    **Strategisches Audit-Fazit (Zeitraum):**
    * **Präzision:** Die Regel isoliert **{tp_count:,}** Fraud-Fälle. 
    * **Abdeckungsgrad:** Das sind **{fraud_coverage_pct:.1f}%** des Betrugs in diesem Zeitraum (**{total_fraud_in_period:,}** Fälle).
    """)

    # --- SEKTION 3: DIE GÜTEPRÜFUNG ---
    st.divider()
    st.subheader("3. Validierung der Kontroll-Güte")
    
    if st.button("Detaillierte Audit-Validierung"):
        with st.spinner("Berechne Risiko-Szenarien..."):
            analyzed_audit = engine.process_batch(audit_df)
            reports = get_performance_report(analyzed_audit)
            total_tx = reports['total_count']

            # --- REIHE 1: STANDARD ---
            st.subheader("Szenario A: Standard Compliance (Medium + High)")
            s = reports['standard']
            col1, col2 = st.columns(2)
            with col1:
                # FIX: 'color' Parameter hinzugefügt, damit die Map greift
                fig1 = px.pie(names=['Betrug (TP)', 'Fehlalarm (FP)'], 
                            values=[s['tp'], s['fp']], 
                            color=['Betrug (TP)', 'Fehlalarm (FP)'],
                            title="Präzision (Standard)", hole=0.4, 
                            color_discrete_map={'Betrug (TP)':'#ef553b', 'Fehlalarm (FP)':'#636efa'})
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                # FIX: 'color' Parameter hinzugefügt
                fig2 = px.pie(names=['Alarme', 'OK'], 
                            values=[s['tp']+s['fp'], total_tx-(s['tp']+s['fp'])], 
                            color=['Alarme', 'OK'],
                            title="System-Last (Standard)", hole=0.4, 
                            color_discrete_map={'Alarme':'#ffa15a', 'OK':'#00cc96'})
                st.plotly_chart(fig2, use_container_width=True)

            # --- REIHE 2: HIGH CONFIDENCE ---
            st.subheader("Szenario B: High-Confidence Audit (Score >= 55)")
            h = reports['high_confidence']
            col3, col4 = st.columns(2)
            with col3:
                # FIX: 'color' Parameter hinzugefügt
                fig3 = px.pie(names=['Betrug (TP)', 'Fehlalarm (FP)'], 
                            values=[h['tp'], h['fp']], 
                            color=['Betrug (TP)', 'Fehlalarm (FP)'],
                            title="Präzision (Optimiert)", hole=0.4, 
                            color_discrete_map={'Betrug (TP)':'#ef553b', 'Fehlalarm (FP)':'#636efa'})
                st.plotly_chart(fig3, use_container_width=True)
            with col4:
                # FIX: 'color' Parameter hinzugefügt
                fig4 = px.pie(names=['Alarme', 'OK'], 
                            values=[h['tp']+h['fp'], total_tx-(h['tp']+h['fp'])], 
                            color=['Alarme', 'OK'],
                            title="System-Last (Optimiert)", hole=0.4, 
                            color_discrete_map={'Alarme':'#ffa15a', 'OK':'#00cc96'})
                st.plotly_chart(fig4, use_container_width=True)

            # --- VERGLEICHS-METRIKEN ---
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Recall-Verlust", f"{(s['recall'] - h['recall'])*100:.1f}% weniger Treffer", delta_color="inverse")
            
            total_saved = (s['tp']+s['fp']) - (h['tp']+h['fp'])
            m2.metric("Eingesparte Alarme", f"{total_saved:,}")
            
            reduction_pct = (total_saved / (s['tp']+s['fp']) * 100) if (s['tp']+s['fp']) > 0 else 0
            m3.metric("Effizienz-Steigerung", f"-{reduction_pct:.1f}% Aufwand")

            st.success(f"Strategie-Check: Durch den Fokus auf High-Confidence Fälle reduzieren wir die Prüflast um **{reduction_pct:.1f}%**.")
    
    # --- PDF EXPORT BUTTON ---
    st.divider()
    st.subheader("📑 Finaler Audit-Export")

    if 'reports' in locals() and 'tp_count' in locals():
        # Alle notwendigen Daten für die Funktion bündeln
        liq_data = {
            "tp_count": tp_count,
            "coverage": fraud_coverage_pct,
            "total_fraud": total_fraud_in_period
        }
        
        try:
            # PDF generieren
            pdf_bytes = generate_audit_pdf(
                st.session_state.incident_log, 
                reports, 
                step_range, 
                liq_data
            )
            
            # Download Button anzeigen
            st.download_button(
                label="📥 Vollständigen Audit-Bericht (PDF) exportieren",
                data=pdf_bytes,
                file_name=f"Audit_Report_Steps_{step_range[0]}_{step_range[1]}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Fehler im Export-Modul: {e}")
            # Debugging Hilfe: st.write(e) 
    else:
        st.info("💡 Führe erst die 'Detaillierte Audit-Validierung' durch, um den Bericht zu generieren.")