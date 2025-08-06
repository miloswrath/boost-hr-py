import pandas as pd

class ExtractHR:
    def __init__(self, file):
        self.file = file

    def extract_hr(self):
        if not self.file or not isinstance(self.file, list):
            raise ValueError("Files must be a non-empty list of file paths.")
        for file in self.file:

            if file.endswith('.csv'):
                df = pd.read_csv(file, skiprows=2)
                df = df[['Time', 'Heart Rate (bpm)']].rename(columns={'Time': 'time', 'Heart Rate (bpm)': 'hr'})
                df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')









