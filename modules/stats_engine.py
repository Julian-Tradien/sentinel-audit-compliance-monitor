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