import pandas as pd
import logging
"""
This file is used to QC the heart rate data for supervised sessions
"""

logger = logging.getLogger(__name__)

class QC_Sup:

    def __init__(self, hr, zones):
        self.hr = hr
        self.zones = zones
        self.err = {}

    def main(self):
        self.qc_data()
        self.qc_zones()

        return self.err

    def qc_data(self):
        """
        QC the raw data itself
        """
        
        logger.debug("running missing check")
        missing_check, missing_periods = self._missing_periods()
        nan_runs = self._nan_check(self.hr.copy())
        if missing_check == 1:
            self.err['missing'] = ['missing significant time', missing_periods]
        elif not nan_runs.empty:
            self.err['nan'] = ['more than 30 NaNs in a row', nan_runs]
        else: 
            return None

    def qc_zones(self):
        """
        Initalize the QC zone rules and ensure they adhere to them
        """
        logger.debug("running phantom zone qc")

        return None



    def _missing_periods(self):

        df = self.hr.copy()

        # assume df has columns “time” and “hr”
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')

        # drop any NaNs so we only look at real measurements
        valid = df.dropna(subset=['hr'])

        # compute time‐diff between successive valid samples
        delta = valid['time'].diff()

        # mask where that gap exceeds 30 s
        gaps = delta > pd.Timedelta(seconds=30)

        # build a table of missing‐data intervals
        missing_periods = pd.DataFrame({
            'gap_start': valid['time'][gaps].shift(),    # end of last good sample
            'gap_end':   valid['time'][gaps]             # start of next good sample
        })
        missing_periods['duration'] = missing_periods['gap_end'] - missing_periods['gap_start']
        if missing_periods.empty:
            return 0, missing_periods
        else:
            return 1, missing_periods


    def _nan_check(self, df: pd.DataFrame, min_run: int = 30) -> pd.DataFrame:
        """
        Detect runs of > min_run consecutive NaNs in df['hr'].
        Returns a DataFrame with columns: [start_time, end_time, length].
        """
        # 1) Ensure time is datetime and sorted
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time').reset_index(drop=True)

        # 2) Boolean mask of where hr is NaN
        is_nan = df['hr'].isna()

        # 3) Build run‐IDs by marking where the mask changes
        run_id = is_nan.ne(is_nan.shift()).cumsum()

        # 4) Aggregate each run
        summary = (
            df
            .assign(is_nan=is_nan, run=run_id)
            .groupby('run')
            .agg(
                start_time=('time', 'first'),
                end_time  =('time', 'last'),
                length    =('is_nan', 'size'),
                all_nan   =('is_nan', 'all')
            )
        )

        # 5) Filter to runs that are all-NaN and longer than min_run
        long_runs = summary[(summary['all_nan']) & (summary['length'] > min_run)]

        # 6) Return just start/end/length
        return long_runs[['start_time', 'end_time', 'length']]



