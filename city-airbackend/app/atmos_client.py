import pandas as pd
from typing import List, Literal
from urllib.parse import quote

BASE_URL = "https://atmos.urbansciences.in/adp/v4/getDeviceDataParamClone"
API_KEY = "ncapAPIKey"

Aggregation = Literal["15min", "hourly", "daily", "monthly", "yearly"]
DataMode = Literal["api", "raw15"]

TS_MAP = {
    "hourly": "hh",
    "daily": "dd",
    "monthly": "MM",  # capital MM = month
    "yearly": "YY",
}

def fetch_csv(
    site_ids: List[str],
    params: List[str],
    start: str,
    end: str,
    gaps: int,
    gap_value: str,
    aggregation: Aggregation,
    data_mode: DataMode = "api",
) -> pd.DataFrame:
    """
    data_mode:
      - "api"   : use API aggregated values (hh/dd/MM/YY)
      - "raw15" : fetch 15-min values (ts=mm, avg=15)

    aggregation:
      - "15min" is only meaningful with data_mode="raw15"
      - hourly/daily/monthly/yearly use API if data_mode="api"
    """

    if data_mode == "raw15" or aggregation == "15min":
        ts_ref = "mm"     # minute resolution
        avg_window = 15   # 15-min average
    else:
        ts_ref = TS_MAP.get(aggregation, "hh")
        avg_window = 1    # API already gives aggregated points

    site_str = ",".join(site_ids)
    param_str = ",".join(params)

    url = (
        f"{BASE_URL}/imei/{site_str}"
        f"/params/{param_str}"
        f"/startdate/{start}"
        f"/enddate/{end}"
        f"/ts/{ts_ref}"
        f"/avg/{avg_window}"
        f"/api/{API_KEY}"
        f"?gaps={gaps}&gap_value={quote(gap_value)}"
    )

    try:
        return pd.read_csv(url)
    except Exception:
        return pd.DataFrame()

