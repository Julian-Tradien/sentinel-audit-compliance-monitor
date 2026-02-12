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

    def stream_generator(self, step):
            """
            Simuliert den Live-Stream innerhalb eines Steps mit variabler Batch-Größe.
            """
            step_data = self.get_step_data(step)
            shuffled_data = step_data.sample(frac=1).reset_index(drop=True)
            
            current_idx = 0
            total_rows = len(shuffled_data)
            
            while current_idx < total_rows:
                dynamic_batch_size = random.randint(8, 12)
                
                # Ende des Batches berechnen
                end_idx = min(current_idx + dynamic_batch_size, total_rows)
                
                yield shuffled_data.iloc[current_idx:end_idx]
                
                current_idx = end_idx