import pandas as pd
from util.zone.midpoint import midpoint_snap

def extract_zones(path, subject, snap_to=5):
    # read the excel file
    df = pd.read_excel(path, sheet_name='Sheet 1')
    df = df[df['ID'] == subject]
    df = df.iloc[:, 5:15]
    df.columns = ['zone 1 start', 'zone 1 end', 'zone 2 start', 'zone 2 end', 'zone 3 start', 'zone 3 end', 'zone 4 start', 'zone 4 end', 'zone 5 start', 'zone 5 end']

