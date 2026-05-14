import numpy as np
import pandas as pd

def clean_response(data):
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items()}

    if isinstance(data, list):
        return [clean_response(i) for i in data]

    if isinstance(data, np.integer):
        return int(data)

    if isinstance(data, np.floating):
        return float(data)

    if isinstance(data, pd.Timestamp):
        return str(data.date())

    return data