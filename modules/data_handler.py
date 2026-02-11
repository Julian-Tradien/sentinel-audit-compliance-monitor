import pandas as pd
import time
import random

class DataStreamer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.current_step = 1

    def load_data(self):
        """Lädt den Datensatz initial."""
        cols = ['step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 
                'newbalanceOrig', 'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud']
        self.df = pd.read_csv(self.file_path, usecols=cols)

    def get_step_data(self, step):
        """Filtert Daten für einen spezifischen Step."""
        return self.df[self.df['step'] == step]

    def stream_generator(self, step, batch_size=5):
        """
        Simuliert den Live-Stream innerhalb eines Steps.
        Gibt zufällige Batches aus dem Step zurück.
        """
        step_data = self.get_step_data(step)
        shuffled_data = step_data.sample(frac=1).reset_index(drop=True)
        
        for i in range(0, len(shuffled_data), batch_size):
            yield shuffled_data.iloc[i:i + batch_size]