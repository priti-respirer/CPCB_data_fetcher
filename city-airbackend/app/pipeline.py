import pandas as pd
import time
from typing import Dict, Tuple, Optional
from datetime import datetime
from .atmos_client import fetch_csv

progress_store: Dict[str, int] = {}
MAX_RETRIES = 4


def _clean_pollutant_name(p):
    return (
        p.replace("cnc", "")
         .replace("ppb", "")
         .replace("tempc", "Temp")
         .replace("rh", "RH")
         .replace("ws", "WS")
         .replace("wd", "WD")
         .upper()
    )


def _find_pollutant_col(df: pd.DataFrame, pollutant_code: str):
    target = pollutant_code.lower().replace(" ", "")
    for col in df.columns:
        col_clean = str(col).lower().replace(" ", "")
        if target in col_clean:
            return col
    return None


def _expected_total_points(start: str, end: str, aggregation: str) -> int:
    """
    Expected total buckets between start & end INCLUSIVE based on aggregation.
    Uses lowercase pandas freq aliases (h/d) to avoid "Invalid frequency: H".
    """
    start_dt = datetime.strptime(start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M")

    if start_dt > end_dt:
        return 0

    ts_start = pd.Timestamp(start_dt)
    ts_end = pd.Timestamp(end_dt)

    if aggregation == "15min":
        s = ts_start.floor("15min")
        e = ts_end.floor("15min")
        return len(pd.date_range(s, e, freq="15min"))

    if aggregation == "hourly":
        s = ts_start.floor("h")
        e = ts_end.floor("h")
        return len(pd.date_range(s, e, freq="h"))

    if aggregation == "daily":
        s = ts_start.floor("d")
        e = ts_end.floor("d")
        return len(pd.date_range(s, e, freq="d"))

    if aggregation == "monthly":
        return len(pd.period_range(ts_start.to_period("M"), ts_end.to_period("M"), freq="M"))

    if aggregation == "yearly":
        return len(pd.period_range(ts_start.to_period("Y"), ts_end.to_period("Y"), freq="Y"))

    # fallback = hourly
    s = ts_start.floor("h")
    e = ts_end.floor("h")
    return len(pd.date_range(s, e, freq="h"))


def _retry_fetch(**kwargs) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Returns (df, err). Retries on:
      - exception
      - empty df
      - dt_time missing (bad/non-csv response)
    """
    last_err = None
    for _ in range(MAX_RETRIES):
        try:
            df = fetch_csv(**kwargs)
        except Exception as e:
            last_err = f"Exception: {e}"
            time.sleep(1)
            continue

        if df is None or df.empty:
            last_err = "Empty response (timeout/rate-limit/non-CSV)"
            time.sleep(1)
            continue

        if "dt_time" not in df.columns:
            last_err = f"Bad response: dt_time missing. cols={list(df.columns)[:12]}"
            time.sleep(1)
            continue

        return df, None

    return pd.DataFrame(), last_err


def build_excel_for_request(
    catalog,
    start,
    end,
    aggregation,
    cities,
    pollutants,
    gaps,
    gap_value,
    out_path,
    job_id
):
    total_calls = sum(len(catalog.get_sites_for_city(city)) for city in cities) or 1
    completed_calls = 0

    concentration_dict = {p: {} for p in pollutants}
    uptime_dict = {p: {} for p in pollutants}
    error_rows = []

    # ✅ Expected total count from start–end (same for all stations in this export)
    expected_total = _expected_total_points(start, end, aggregation)

    # ✅ Labels requested
    uptime_label = "Uptime(%)"

    # "Valid Hours / Expected Hours" for hourly, but adapt for other aggregations too.
    unit = {
        "15min": "15-min Records",
        "hourly": "Hours",
        "daily": "Days",
        "monthly": "Months",
        "yearly": "Years"
    }.get(aggregation, "Records")

    valid_label = f"Valid {unit}"
    expected_label = f"Expected {unit}"

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:

        # INFO
        info_top = pd.DataFrame(
            [["Start Date", start], ["End Date", end], ["Aggregation", aggregation]],
            columns=["Parameter", "Value"]
        )
        info_top.to_excel(writer, sheet_name="INFO", index=False)

        current_row = len(info_top) + 2
        city_counts = []
        station_columns = {}

        for city in cities:
            clean_city = city.split("(")[0].strip()
            site_records = catalog.get_sites_for_city(city)
            stations = [r["Location"] for r in site_records]
            city_counts.append({"City": clean_city, "Station Count": len(stations)})
            station_columns[f"{clean_city} Stations"] = stations

        city_count_df = pd.DataFrame(city_counts)
        city_count_df.to_excel(writer, sheet_name="INFO", index=False, startrow=current_row)
        current_row += len(city_count_df) + 3

        if station_columns:
            max_len = max(len(v) for v in station_columns.values())
            for key in station_columns:
                station_columns[key] += [""] * (max_len - len(station_columns[key]))
            pd.DataFrame(station_columns).to_excel(writer, sheet_name="INFO", index=False, startrow=current_row)

        # =================== FETCH LOOP =====================
        for city in cities:
            clean_city = city.split("(")[0].strip()
            site_records = catalog.get_sites_for_city(city)
            if not site_records:
                continue

            city_frames = {p: [] for p in pollutants}
            city_uptime = {p: [] for p in pollutants}

            for record in site_records:
                completed_calls += 1
                progress_store[job_id] = min(99, int((completed_calls / total_calls) * 99))

                # 1) Fast call: all pollutants at once
                df_all, err_all = _retry_fetch(
                    site_ids=[record["site_id"]],
                    params=pollutants,
                    start=start,
                    end=end,
                    gaps=gaps,
                    gap_value=gap_value,
                    aggregation=aggregation,
                    data_mode="raw15" if aggregation == "15min" else "api"
                )

                # 2) If fast call failed -> fallback per pollutant
                if err_all:
                    for pollutant in pollutants:
                        df_one, err_one = _retry_fetch(
                            site_ids=[record["site_id"]],
                            params=[pollutant],
                            start=start,
                            end=end,
                            gaps=gaps,
                            gap_value=gap_value,
                            aggregation=aggregation,
                            data_mode="raw15" if aggregation == "15min" else "api"
                        )

                        if err_one:
                            msg = f"ALL-PARAM failed ({err_all}); single-param failed ({err_one})"
                            # no notes column now → only keep error in ERRORS sheet
                            error_rows.append({
                                "City": clean_city, "Station": record["Location"], "SiteID": record["site_id"],
                                "Pollutant": pollutant, "Error": msg
                            })
                            city_uptime[pollutant].append({
                                "Station": record["Location"],
                                uptime_label: "",
                                valid_label: "",
                                expected_label: expected_total
                            })
                            continue

                        df_one["dt_time"] = pd.to_datetime(df_one["dt_time"], errors="coerce")
                        pollutant_col = _find_pollutant_col(df_one, pollutant)
                        if pollutant_col is None:
                            msg = f"Column not found for '{pollutant}' (single-param). cols={list(df_one.columns)[:12]}"
                            error_rows.append({
                                "City": clean_city, "Station": record["Location"], "SiteID": record["site_id"],
                                "Pollutant": pollutant, "Error": msg
                            })
                            city_uptime[pollutant].append({
                                "Station": record["Location"],
                                uptime_label: "",
                                valid_label: "",
                                expected_label: expected_total
                            })
                            continue

                        sub = df_one[["dt_time", pollutant_col]].copy()
                        sub[pollutant_col] = pd.to_numeric(sub[pollutant_col], errors="coerce")

                        valid = sub[pollutant_col].notna().sum()
                        total = expected_total
                        uptime = round((valid / total) * 100, 2) if total else 0

                        city_uptime[pollutant].append({
                            "Station": record["Location"],
                            uptime_label: uptime,
                            valid_label: valid,
                            expected_label: total
                        })
                        city_frames[pollutant].append(sub)

                    continue

                # 3) Fast call succeeded -> process from df_all
                df_all["dt_time"] = pd.to_datetime(df_all["dt_time"], errors="coerce")

                for pollutant in pollutants:
                    pollutant_col = _find_pollutant_col(df_all, pollutant)

                    # If pollutant missing in multi-param -> fallback only for this pollutant
                    if pollutant_col is None:
                        df_one, err_one = _retry_fetch(
                            site_ids=[record["site_id"]],
                            params=[pollutant],
                            start=start,
                            end=end,
                            gaps=gaps,
                            gap_value=gap_value,
                            aggregation=aggregation,
                            data_mode="raw15" if aggregation == "15min" else "api"
                        )
                        if err_one:
                            msg = f"Missing in ALL-PARAM + single-param failed ({err_one})"
                            error_rows.append({
                                "City": clean_city, "Station": record["Location"], "SiteID": record["site_id"],
                                "Pollutant": pollutant, "Error": msg
                            })
                            city_uptime[pollutant].append({
                                "Station": record["Location"],
                                uptime_label: "",
                                valid_label: "",
                                expected_label: expected_total
                            })
                            continue

                        df_one["dt_time"] = pd.to_datetime(df_one["dt_time"], errors="coerce")
                        pollutant_col = _find_pollutant_col(df_one, pollutant)
                        if pollutant_col is None:
                            msg = f"Column not found for '{pollutant}' (single-param). cols={list(df_one.columns)[:12]}"
                            error_rows.append({
                                "City": clean_city, "Station": record["Location"], "SiteID": record["site_id"],
                                "Pollutant": pollutant, "Error": msg
                            })
                            city_uptime[pollutant].append({
                                "Station": record["Location"],
                                uptime_label: "",
                                valid_label: "",
                                expected_label: expected_total
                            })
                            continue

                        sub = df_one[["dt_time", pollutant_col]].copy()
                    else:
                        sub = df_all[["dt_time", pollutant_col]].copy()

                    sub[pollutant_col] = pd.to_numeric(sub[pollutant_col], errors="coerce")

                    valid = sub[pollutant_col].notna().sum()
                    total = expected_total
                    uptime = round((valid / total) * 100, 2) if total else 0

                    city_uptime[pollutant].append({
                        "Station": record["Location"],
                        uptime_label: uptime,
                        valid_label: valid,
                        expected_label: total
                    })
                    city_frames[pollutant].append(sub)

            # build city average per pollutant
            for pollutant in pollutants:
                if not city_frames[pollutant]:
                    uptime_dict[pollutant][clean_city] = city_uptime[pollutant]
                    continue

                combined = pd.concat(city_frames[pollutant], ignore_index=True)
                pollutant_col = _find_pollutant_col(combined, pollutant)
                if pollutant_col is None:
                    uptime_dict[pollutant][clean_city] = city_uptime[pollutant]
                    continue

                city_df = combined.groupby("dt_time", as_index=False)[pollutant_col].mean()
                city_df[pollutant_col] = city_df[pollutant_col].round(3)

                concentration_dict[pollutant][clean_city] = city_df.set_index("dt_time")
                uptime_dict[pollutant][clean_city] = city_uptime[pollutant]

        # ===================== WRITE SHEETS ======================
        for pollutant in pollutants:
            pollutant_clean = _clean_pollutant_name(pollutant)

            # pollutant data sheet
            if concentration_dict.get(pollutant):
                wide = None
                for city_name, df_city in concentration_dict[pollutant].items():
                    df_city = df_city.rename(columns={df_city.columns[0]: city_name})
                    wide = df_city if wide is None else wide.join(df_city, how="outer")

                wide = wide.sort_index().reset_index().rename(columns={"dt_time": "Timestamp"})
                wide.to_excel(writer, sheet_name=pollutant_clean[:31], index=False)

            # uptime sheet
            if uptime_dict.get(pollutant):
                max_len = max((len(v) for v in uptime_dict[pollutant].values()), default=0)
                if max_len:
                    formatted = {}
                    for city_name, rows in uptime_dict[pollutant].items():
                        stations = [r.get("Station", "") for r in rows]
                        uptimes = [r.get(uptime_label, "") for r in rows]
                        valids = [r.get(valid_label, "") for r in rows]
                        expecteds = [r.get(expected_label, "") for r in rows]

                        while len(stations) < max_len:
                            stations.append("")
                            uptimes.append("")
                            valids.append("")
                            expecteds.append("")

                        formatted[f"{city_name} Stations"] = stations
                        formatted[f"{city_name} {uptime_label}"] = uptimes
                        formatted[f"{city_name} {valid_label}"] = valids
                        formatted[f"{city_name} {expected_label}"] = expecteds

                    pd.DataFrame(formatted).to_excel(
                        writer,
                        sheet_name=f"{pollutant_clean}_UPTIME"[:31],
                        index=False
                    )

        # keep ERRORS sheet (so you still see failures)
        if error_rows:
            pd.DataFrame(error_rows).to_excel(writer, sheet_name="ERRORS", index=False)