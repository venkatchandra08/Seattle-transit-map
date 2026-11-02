"""Atomic, streaming GTFS ZIP importer. Never extracts archive paths."""
import csv
import io
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from db import connect

FEED = "https://metro.kingcounty.gov/gtfs/google_transit.zip"
def seconds(value):
    h,m,s = map(int,value.split(":"))
    if h < 0 or not 0 <= m < 60 or not 0 <= s < 60:
        raise ValueError("Invalid GTFS time")
    return h*3600+m*60+s

def day(value):
    return datetime.strptime(value,"%Y%m%d").date()

def run(source):
    with tempfile.TemporaryFile() as stream:
        if source.startswith(("https://", "http://")):
            with urllib.request.urlopen(source, timeout=120) as response:
                while block := response.read(1024*1024):
                    stream.write(block)
        else:
            with open(source,"rb") as f:
                while block := f.read(1024*1024): stream.write(block)
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive, connect() as conn:
            conn.execute(Path(__file__).with_name("schema.sql").read_text())
            conn.execute("TRUNCATE stop_times,trips,routes,stops,calendar,calendar_dates,feed_meta")
            specs = [
                ("stops",["stop_id","stop_name","stop_lat","stop_lon"],None),
                ("routes",["route_id","route_short_name","route_long_name","route_color"],None),
                ("trips",["trip_id","route_id","service_id","trip_headsign"],None),
                ("stop_times",["trip_id","arrival_time","departure_time","stop_id","stop_sequence"],["trip_id","arrival","departure","stop_id","stop_sequence"]),
                ("calendar",["service_id","monday","tuesday","wednesday","thursday","friday","saturday","sunday","start_date","end_date"],None),
                ("calendar_dates",["service_id","date","exception_type"],None)]
            for table, fields, columns in specs:
                filename=table+".txt"
                if filename not in archive.namelist() and table in ("calendar","calendar_dates"): continue
                count=0
                with archive.open(filename) as file, conn.cursor().copy(f"COPY {table} ({','.join(columns or fields)}) FROM STDIN") as copy:
                    for row in csv.DictReader(io.TextIOWrapper(file,encoding="utf-8-sig")):
                        # Unscheduled intermediate times cannot be used by this router.
                        if table=="stop_times" and (not row["arrival_time"] or not row["departure_time"]): continue
                        values=[]
                        for field in fields:
                            value=row.get(field,"")
                            if field in ("arrival_time","departure_time"): value=seconds(value)
                            elif field in ("start_date","end_date","date"): value=day(value)
                            values.append(value)
                        copy.write_row(values)
                        count+=1
                print(table,count,flush=True)
            conn.execute("INSERT INTO feed_meta(source) VALUES (%s)",(source,))
    print("Import committed successfully.")

if __name__=="__main__": run(sys.argv[1] if len(sys.argv)>1 else FEED)
