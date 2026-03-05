from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Dict, Optional
from datetime import datetime
import os
import tempfile
import uuid
from threading import Thread

from .site_catalog import SiteCatalog
from .pipeline import build_excel_for_request, progress_store

app = FastAPI(title="City Air Quality Export API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

SITE_XLSX_PATH = os.getenv("SITE_XLSX_PATH", "site_ids_to_fetch_daily_data.xlsx")
catalog = SiteCatalog(SITE_XLSX_PATH)

POLLUTANT_MAP = {
    "PM10": "pm10cnc",
    "PM2.5": "pm2.5cnc",
    "NO2": "no2ppb",
    "CO": "co",
    "Ozone": "o3ppb",
    "SO2": "so2",
    "NH3": "nh3",
    "Benzene": "benzene",
    "Eth-Benzene": "ethbenzene",
    "Toluene": "toluene",
    "Xylene": "xylene",
    "RH": "rh",
    "Temp": "tempc",
    "WS": "ws",
    "WD": "wd",
    "CH4": "ch4",
    "CO2": "co2",
    "AT": "at"
}

SUPPORTED_POLLUTANTS = list(POLLUTANT_MAP.values())
Aggregation = Literal["15min", "hourly", "daily", "monthly", "yearly"]

class ExportRequest(BaseModel):
    start: str
    end: str
    aggregation: Aggregation
    cities: List[str]
    pollutants: List[str]
    gaps: int = 1
    gap_value: str = "NULL"

error_store: Dict[str, Optional[str]] = {}

@app.get("/meta/cities")
def get_cities():
    return {"cities": catalog.list_cities()}

@app.get("/meta/pollutants")
def get_pollutants():
    return {"pollutants": POLLUTANT_MAP}

@app.post("/export")
def export(req: ExportRequest):
    start_dt = datetime.strptime(req.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.strptime(req.end, "%Y-%m-%dT%H:%M")

    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start datetime must be before End datetime")
    bad = [p for p in req.pollutants if p not in SUPPORTED_POLLUTANTS]
    if bad:
        raise HTTPException(status_code=400, detail=f"Unsupported pollutants: {bad}")

    try:
        datetime.strptime(req.start, "%Y-%m-%dT%H:%M")
        datetime.strptime(req.end, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="start/end must be YYYY-MM-DDTHH:mm")

    job_id = str(uuid.uuid4())
    progress_store[job_id] = 0
    error_store[job_id] = None

    tmpdir = tempfile.mkdtemp(prefix="airq_export_")
    out_path = os.path.join(tmpdir, f"city_air_quality_{req.aggregation}_{uuid.uuid4().hex[:8]}.xlsx")

    def run_export():
        try:
            build_excel_for_request(
                catalog=catalog,
                start=req.start,
                end=req.end,
                aggregation=req.aggregation,
                cities=req.cities,
                pollutants=req.pollutants,
                gaps=req.gaps,
                gap_value=req.gap_value,
                out_path=out_path,
                job_id=job_id
            )
            progress_store[job_id] = 100
        except Exception as e:
            progress_store[job_id] = -1
            error_store[job_id] = str(e)

    Thread(target=run_export).start()
    return {"job_id": job_id, "file_path": out_path}

@app.get("/progress/{job_id}")
def get_progress(job_id: str):
    return {"progress": progress_store.get(job_id, 0), "error": error_store.get(job_id)}

@app.get("/download")
def download(file_path: str):
    return FileResponse(
        file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )