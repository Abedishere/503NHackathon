from __future__ import annotations
import pandas as pd

def daily_hours(attendance: pd.DataFrame) -> pd.DataFrame:
    """
    Input: branch, date_in_dt, work_hours, emp_name
    Output: total_hours/shifts/unique_employees per branch-day
    """
    df = attendance.dropna(subset=["branch","date_in_dt"]).copy()
    return (df.groupby(["branch","date_in_dt"], as_index=False)
              .agg(total_hours=("work_hours","sum"),
                   shifts=("work_hours","count"),
                   unique_employees=("emp_name","nunique")))