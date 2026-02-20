
import pandas as pd
import time
from typing import Dict, Optional
from .atmos_client import fetch_csv

progress_store: Dict[str, int] = {}
MAX_RETRIES = 4


# ---------------- CLEAN POLLUTANT NAME ----------------
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


# ---------------- FIND COLUMN ----------------
def _find_pollutant_col(df: pd.DataFrame, pollutant_code: str) -> Optional[str]:
    p = pollutant_code.lower().strip()
    for col in df.columns:
        if str(col).lower().startswith(p):
            return col
    return None


# ---------------- RETRY LOGIC ----------------
def _retry_fetch(**kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            df = fetch_csv(**kwargs)
            return df
        except Exception:
            time.sleep(1)
    return pd.DataFrame()


# ---------------- MAIN PIPELINE ----------------
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

    total_calls = sum(
        len(catalog.get_sites_for_city(city)) * len(pollutants)
        for city in cities
    )

    completed_calls = 0

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:

        # ===================================================
        # ================= INFO SHEET ======================
        # ===================================================
        # ===================================================
# ================= INFO SHEET ======================
# ===================================================

# ---- Top Info (Start / End / Aggregation) ----
        info_top = pd.DataFrame([
            ["Start Date", start],
            ["End Date", end],
            ["Aggregation", aggregation],
        ], columns=["Parameter", "Value"])

        info_top.to_excel(writer, sheet_name="INFO", index=False, startrow=0)

        current_row = len(info_top) + 2


        # ---- City + Station Count Table ----
        city_counts = []
        station_columns = {}

        for city in cities:

            clean_city = city.split("(")[0].strip()
            site_records = catalog.get_sites_for_city(city) or []
            stations = [r["Location"] for r in site_records]

            city_counts.append({
                "City": clean_city,
                "Station Count": len(stations)
            })

            station_columns[f"{clean_city} Stations"] = stations


        city_count_df = pd.DataFrame(city_counts)

        city_count_df.to_excel(
            writer,
            sheet_name="INFO",
            index=False,
            startrow=current_row
        )

        current_row += len(city_count_df) + 3


        # ---- Station Columns Section ----
        if station_columns:

            max_len = max(len(v) for v in station_columns.values())

            for key in station_columns:
                station_columns[key] += [""] * (max_len - len(station_columns[key]))

            station_df = pd.DataFrame(station_columns)

            station_df.to_excel(
                writer,
                sheet_name="INFO",
                index=False,
                startrow=current_row
            )

        # ===================================================
        # ================= POLLUTANT LOOP ==================
        # ===================================================

        for pollutant in pollutants:

            pollutant_clean = _clean_pollutant_name(pollutant)

            concentration_dict = {}
            uptime_dict = {}

            for city in cities:

                clean_city = city.split("(")[0].strip()
                site_records = catalog.get_sites_for_city(city)

                if not site_records:
                    continue

                all_station_frames = []
                station_uptime_rows = []

                for record in site_records:

                    df = _retry_fetch(
                        site_ids=[record["site_id"]],
                        params=[pollutant],
                        start=start,
                        end=end,
                        gaps=gaps,
                        gap_value=gap_value,
                        aggregation=aggregation,
                        data_mode="raw15" if aggregation == "15min" else "api"
                    )

                    completed_calls += 1
                    progress_store[job_id] = int((completed_calls / total_calls) * 100)

                    if df.empty:
                        continue

                    pollutant_col = _find_pollutant_col(df, pollutant)
                    if pollutant_col is None:
                        continue

                    df["dt_time"] = pd.to_datetime(df["dt_time"], errors="coerce")
                    df[pollutant_col] = pd.to_numeric(df[pollutant_col], errors="coerce")

                    valid = df[pollutant_col].notna().sum()
                    total = len(df)
                    uptime = round((valid / total) * 100, 2) if total else 0

                    station_uptime_rows.append({
                        "Station": record["Location"],
                        "Uptime (%)": uptime
                    })

                    all_station_frames.append(df)

                if not all_station_frames:
                    continue

                combined = pd.concat(all_station_frames, ignore_index=True)
                pollutant_col = _find_pollutant_col(combined, pollutant)

                city_df = (
                    combined.groupby("dt_time", as_index=False)[pollutant_col]
                    .mean()
                )

                city_df[pollutant_col] = city_df[pollutant_col].round(3)

                concentration_dict[clean_city] = city_df.set_index("dt_time")
                uptime_dict[clean_city] = station_uptime_rows


            # ---------------- CONCENTRATION SHEET ----------------

            if concentration_dict:

                wide = None

                for city_name, df_city in concentration_dict.items():
                    df_city = df_city.rename(columns={df_city.columns[0]: city_name})
                    if wide is None:
                        wide = df_city
                    else:
                        wide = wide.join(df_city, how="outer")

                wide = wide.sort_index()
                wide = wide.reset_index().rename(columns={"dt_time": "Timestamp"})

                wide.to_excel(writer, sheet_name=pollutant_clean[:31], index=False)


            # ---------------- UPTIME SHEET ----------------

            if uptime_dict:

                max_len = max(len(v) for v in uptime_dict.values())

                formatted_data = {}

                for city_name, rows in uptime_dict.items():

                    stations = [r["Station"] for r in rows]
                    uptimes = [r["Uptime (%)"] for r in rows]

                    while len(stations) < max_len:
                        stations.append("")
                        uptimes.append("")

                    formatted_data[f"{city_name} Station"] = stations
                    formatted_data[f"{city_name} Uptime (%)"] = uptimes

                uptime_df = pd.DataFrame(formatted_data)

                uptime_df.to_excel(
                    writer,
                    sheet_name=f"{pollutant_clean}_UPTIME"[:31],
                    index=False
                )