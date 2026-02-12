import numpy as np
import pandas as pd

def calculate_benfords_law(series):
    """Prüft die Verteilung der ersten Ziffer gegen das Benford'sche Gesetz."""
    # Erste Ziffer extrahieren (Nullen ignorieren)
    first_digits = series[series > 0].astype(str).str[0].astype(int)
    counts = first_digits.value_counts(normalize=True).sort_index()
    
    # Theoretische Benford-Verteilung
    benford_probs = np.log10(1 + 1/np.arange(1, 10))
    
    return pd.DataFrame({
        'Ziffer': np.arange(1, 10),
        'Tatsächlich': counts.reindex(range(1, 10), fill_value=0).values,
        'Benford': benford_probs
    })

def get_benford_interpretation(benford_df):
    # Wir berechnen die Differenz zwischen Tatsächlich und Benford
    benford_df['diff'] = abs(benford_df['Tatsächlich'] - benford_df['Benford'])
    avg_diff = benford_df['diff'].mean()
    
    # Grenzwerte für die Sätze (Erfahrungswerte aus der Forensik)
    if avg_diff < 0.02:
        return "✅ **Konformität:** Die Daten folgen nahezu perfekt dem Benford'schen Gesetz. Es gibt keine statistischen Anzeichen für großflächige manuelle Manipulationen.", "success"
    elif avg_diff < 0.05:
        return "⚠️ **Geringe Abweichung:** Es zeigen sich leichte Unregelmäßigkeiten in den Betragsstrukturen. Dies könnte auf spezifische Geschäftsprozesse (z.B. Fixpreise) hindeuten.", "warning"
    else:
        return "🚨 **Hohe Anomalie:** Die Verteilung weicht massiv von der natürlichen Erwartung ab. Dies ist ein starkes Indiz für künstlich generierte Daten oder systematische Manipulation.", "error"

def get_performance_report(analyzed_df):
    """Vergleicht System-Warnungen mit der tatsächlichen Fraud-Spalte für zwei Szenarien."""
    
    actually_fraud = analyzed_df['isFraud'] == 1

    def calculate_metrics(detected_mask):
        tp = len(analyzed_df[detected_mask & actually_fraud])
        fp = len(analyzed_df[detected_mask & ~actually_fraud])
        fn = len(analyzed_df[~detected_mask & actually_fraud])
        
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        return {"tp": tp, "fp": fp, "fn": fn, "recall": recall, "precision": precision}

    # Szenario A: Standard (Medium & High)
    standard_mask = analyzed_df['risk_level'].isin(['MEDIUM', 'HIGH'])
    
    # Szenario B: High Confidence (Nur High Risk & Score >= 55)
    # Falls risk_score in analyzed_df existiert:
    high_conf_mask = (analyzed_df['risk_level'] == 'HIGH') & (analyzed_df['risk_score'] >= 55)

    return {
        "standard": calculate_metrics(standard_mask),
        "high_confidence": calculate_metrics(high_conf_mask),
        "total_count": len(analyzed_df)
    }