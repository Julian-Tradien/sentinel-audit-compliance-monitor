import io
from fpdf import FPDF

def generate_audit_pdf(incident_df, stats, steps, liq_metrics):
    # fpdf2 nutzen (Standard in modernen Umgebungen)
    pdf = FPDF()
    pdf.add_page()
    
    # --- HEADER ---
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 15, "Compliance Audit Report", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Zeitraum: Stunde(n) {steps[0]} bis {steps[1]}", ln=True, align='C')
    pdf.ln(5)

    # --- 1. STRATEGISCHES FAZIT (LIQUIDATION) ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, "1. Validierung: 100%-Liquidation-Regel", ln=True)
    pdf.set_font("Arial", size=11)
    
    pdf.multi_cell(180, 8, 
        f"- Isolierte Fraud-Faelle: {liq_metrics['tp_count']:,}\n"
        f"- Abdeckungsgrad: {liq_metrics['coverage']:.1f}% aller Betrugsfaelle im Zeitraum\n"
        f"- Basis: {liq_metrics['total_fraud']:,} Gesamtfaelle"
    )
    pdf.ln(5)

    # --- 2. PERFORMANCE BENCHMARK (SZENARIEN) ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, "2. Szenarien-Vergleich & Risiko-Abwaegung", ln=True)
    pdf.set_font("Arial", size=11)
    
    s = stats['standard']
    h = stats['high_confidence']
    
    alarms_s = s['tp'] + s['fp']
    alarms_h = h['tp'] + h['fp']
    reduction_pct = ((alarms_s - alarms_h) / alarms_s * 100) if alarms_s > 0 else 0
    
    # Gegenüberstellung der absoluten Treffer (Slippage-Analyse)
    lost_fraud = s['tp'] - h['tp']

    pdf.cell(190, 8, f"- Szenario A (Standard): {s['precision']*100:.1f}% precision | {s['tp']:,} Frauds", ln=True)
    pdf.cell(190, 8, f"- Szenario B (Optimiert): {h['precision']*100:.1f}% precision | {h['tp']:,} Frauds", ln=True)
    
    pdf.ln(2)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(200, 0, 0) # Dunkelrot für das Risiko
    pdf.cell(190, 7, f"-> Risiko-Hinweis: Szenario B uebersieht {lost_fraud:,} Faelle im Vergleich zu Szenario A.", ln=True)
    
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 128, 0) # Dunkelgrün für die Ersparnis
    pdf.cell(190, 8, f"-> Effizienz-Gewinn: {reduction_pct:.1f}% weniger Pruefaufwand (-{alarms_s - alarms_h:,} Alarme)", ln=True)
    
    # Farbe zurücksetzen
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=11)
    pdf.ln(8)

    # --- 3. INCIDENT LOG ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, "3. Detektierte Live-Incidents (Audit Log)", ln=True)
    pdf.set_font("Arial", size=8)

    if not incident_df.empty:
        header = ['Step', 'Type', 'Amount', 'Risk-Level', 'Flags']
        w = [15, 30, 30, 25, 90] # Gesamtbreite 190mm
        
        # Tabellenkopf
        pdf.set_fill_color(240, 240, 240)
        for i, col in enumerate(header):
            pdf.cell(w[i], 8, col, 1, 0, 'C', fill=True)
        pdf.ln()
        
        # Datenzeilen
        for _, row in incident_df.iterrows():
            # Daten säubern (Umlaute/Symbole entfernen für latin-1 Kompatibilität)
            clean_type = str(row['type']).encode('ascii', 'ignore').decode('ascii')
            clean_flags = str(row.get('flags', 'None')).encode('ascii', 'ignore').decode('ascii')[:60]
            
            pdf.cell(w[0], 7, str(row['step']), 1)
            pdf.cell(w[1], 7, clean_type, 1)
            pdf.cell(w[2], 7, f"{float(row['amount']):,.2f}", 1)
            pdf.cell(w[3], 7, str(row['risk_level']), 1)
            pdf.cell(w[4], 7, clean_flags, 1)
            pdf.ln()
    else:
        pdf.cell(190, 10, "Keine Live-Incidents aufgezeichnet.", ln=True)

    return bytes(pdf.output())