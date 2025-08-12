import os
from pathlib import Path
import pandas as pd
import logging

log = logging.getLogger(__name__)

def save_qc(err_master: dict, out_csv: str | os.PathLike) -> pd.DataFrame:
    """
    Flatten QC results from `err_master` into a tidy DataFrame and save as CSV.

    Parameters
    ----------
    err_master : dict
        { subject: [ [file, err_dict], [file, err_dict], ... ], ... }
        where err_dict may contain keys like:
          - "missing": ["missing significant time", DataFrame(gap_start, gap_end, duration)]
          - "nan":     ["more than 30 NaNs in a row", DataFrame(start_time, end_time, length)]
    out_csv : str | PathLike
        Destination CSV path.

    Returns
    -------
    pd.DataFrame
        Columns: subject, file, error_type, message, start_time, end_time, duration_s, length
    """
    rows: list[dict] = []

    def _norm_df(err_type: str, df: pd.DataFrame | None) -> pd.DataFrame:
        """Normalize per-error detail tables to a common set of columns."""
        if df is None or df.empty:
            return pd.DataFrame(columns=["start_time", "end_time", "duration_s", "length"])

        df = df.copy()
        # Standardize time columns
        if {"gap_start", "gap_end"}.issubset(df.columns):
            df.rename(columns={"gap_start": "start_time", "gap_end": "end_time"}, inplace=True)
        # Compute duration_s if a Timedelta `duration` column exists
        if "duration" in df.columns:
            # ensure Timedelta
            df["duration"] = pd.to_timedelta(df["duration"], errors="coerce")
            df["duration_s"] = df["duration"].dt.total_seconds()
        elif "duration_s" not in df.columns:
            df["duration_s"] = pd.NA

        # Keep/rename length if present (NaN-run length in samples)
        if "length" not in df.columns:
            df["length"] = pd.NA

        # Coerce times to datetime (safe if already datetime)
        if "start_time" in df.columns:
            df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
        else:
            df["start_time"] = pd.NaT
        if "end_time" in df.columns:
            df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")
        else:
            df["end_time"] = pd.NaT

        # Return only the normalized columns (others are dropped)
        return df[["start_time", "end_time", "duration_s", "length"]]

    for subject, entries in (err_master or {}).items():
        if not entries:
            continue
        for entry in entries:
            # entry is expected as [file, err_dict]
            if not isinstance(entry, (list, tuple)) or len(entry) != 2:
                continue
            file_path, err_dict = entry
            if not err_dict or not isinstance(err_dict, dict) or len(err_dict) == 0:
                # no QC issues for this file
                continue

            for err_type, payload in err_dict.items():
                # payload is commonly [message, details_df]
                msg = None
                details_df = None
                if isinstance(payload, (list, tuple)):
                    if len(payload) >= 1 and isinstance(payload[0], str):
                        msg = payload[0]
                    if len(payload) >= 2 and isinstance(payload[1], pd.DataFrame):
                        details_df = payload[1]
                elif isinstance(payload, str):
                    msg = payload

                norm = _norm_df(err_type, details_df)
                if norm.empty:
                    rows.append({
                        "subject": subject,
                        "file": str(file_path),
                        "error_type": err_type,
                        "message": msg,
                        "start_time": pd.NaT,
                        "end_time": pd.NaT,
                        "duration_s": pd.NA,
                        "length": pd.NA,
                    })
                else:
                    for _, r in norm.iterrows():
                        rows.append({
                            "subject": subject,
                            "file": str(file_path),
                            "error_type": err_type,
                            "message": msg,
                            "start_time": r["start_time"],
                            "end_time": r["end_time"],
                            "duration_s": r["duration_s"],
                            "length": r["length"],
                        })

    df_out = pd.DataFrame(rows, columns=[
        "subject", "file", "error_type", "message",
        "start_time", "end_time", "duration_s", "length",
    ])

    # Sort for readability
    if not df_out.empty:
        df_out.sort_values(
            by=["subject", "file", "error_type", "start_time", "end_time"],
            inplace=True,
            kind="mergesort",
        )

    # Ensure directory exists and write CSV
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_csv, index=False)
    log.info("QC summary written: %s (%d rows)", out_csv, len(df_out))
    return df_out








