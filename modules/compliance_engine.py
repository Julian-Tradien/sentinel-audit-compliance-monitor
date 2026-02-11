import pandas as pd
import numpy as np

class ComplianceEngine:
    def __init__(self, threshold_high_amount=500000):
        self.threshold_high_amount = threshold_high_amount

    def check_transaction(self, row):
        """
        Prüft eine einzelne Transaktion auf Compliance-Verstöße.
        Gibt ein Dictionary mit Score und Flags zurück.
        """
        score = 0
        flags = []

        # Regel 1: Schwellenwert-Prüfung (Threshold)
        if row['amount'] > self.threshold_high_amount:
            score += 40
            flags.append("HIGH_AMOUNT")

        # Regel 2: Vollständige Konto-Leerung (Indiz für Fraud/Kontoübernahme)
        if row['amount'] == row['oldbalanceOrg'] and row['amount'] > 0:
            score += 30
            flags.append("FULL_BALANCE_TRANSFER")

        # Regel 3: Mathematische Inkonsistenz (Datenintegrität)
        # Prüfung: Ist der neue Kontostand logisch korrekt? 
        # (Wir erlauben eine kleine Toleranz von 0.01 wegen Rundungsfehlern)
        expected_balance = row['oldbalanceOrg'] - row['amount']
        if abs(expected_balance - row['newbalanceOrig']) > 0.01:
            if row['type'] in ['TRANSFER', 'CASH_OUT']: # Nur bei Abgängen relevant
                score += 20
                flags.append("INTEGRITY_ERROR")

        # Regel 4: Zielkonto-Check (Nur für Demo-Zwecke: Transfer auf Konten ohne Historie)
        if row['oldbalanceDest'] == 0 and row['newbalanceDest'] == 0 and row['amount'] > 0:
            score += 25
            flags.append("ZERO_BALANCE_DESTINATION")

        return {
            "risk_score": score,
            "risk_level": "HIGH" if score >= 50 else "MEDIUM" if score >= 20 else "LOW",
            "flags": ", ".join(flags) if flags else "CLEAN"
        }

    def process_batch(self, batch_df):
        """Verarbeitet einen ganzen Batch und fügt Risiko-Spalten hinzu."""
        results = batch_df.apply(self.check_transaction, axis=1, result_type='expand')
        return pd.concat([batch_df, results], axis=1)