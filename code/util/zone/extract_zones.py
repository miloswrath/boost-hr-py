import pandas as pd
from util.zone.midpoint import midpoint_snap
def extract_zones(path, subject, snap_to=5):
    # 1) Read in only the 5 zones for that subject
    df = pd.read_excel(path, sheet_name='Sheet 1')
    row = df.loc[df['ID'] == subject].iloc[0, 5:15]

    # 2) Rename to short, clear names
    cols = []
    for i in range(1, 6):
        cols += [f"z{i}_start", f"z{i}_end"]
    zones = pd.DataFrame([row.values], columns=cols)

    # 3) Snap the boundaries
    return midpoint_snap(zones, snap_to=snap_to)

