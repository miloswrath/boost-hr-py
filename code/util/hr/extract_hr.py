import pandas as pd

def extract_hr(file):
    if not file or not isinstance(file, list):
        raise ValueError("Files must be a non-empty list of file paths.")
    for file in file:

        if file.lower().endswith('.csv'):
            df = pd.read_csv(file, skiprows=2)
            df = df[['Time', 'HR (bpm)']].rename(columns={'Time': 'time', 'HR (bpm)': 'hr'})
            df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
            return df










