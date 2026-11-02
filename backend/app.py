from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Query
from db import connect
from routing import plan

app=FastAPI(title="Seattle Transit API")

@app.get("/api/health")
def health():
    with connect() as conn:
        exists=conn.execute("SELECT to_regclass('feed_meta') AS name").fetchone()["name"]
        return {"feed":conn.execute("SELECT * FROM feed_meta LIMIT 1").fetchone() if exists else None}

@app.get("/api/stops")
def stops(q:str=Query("",max_length=100)):
    with connect() as conn:
        if q:
            return conn.execute("SELECT * FROM stops WHERE stop_name ILIKE %s ORDER BY stop_name LIMIT 30",("%"+q+"%",)).fetchall()
        return conn.execute("SELECT * FROM stops ORDER BY stop_id").fetchall()

@app.get("/api/routes")
def routes():
    with connect() as conn:
        return conn.execute("SELECT * FROM routes ORDER BY route_short_name").fetchall()

@app.get("/api/plan")
def journey(origin:str, destination:str, at:datetime, max_transfers:int=Query(4,ge=0,le=6)):
    if at.tzinfo is None: at=at.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
    at=at.astimezone(ZoneInfo("America/Los_Angeles"))
    with connect() as conn:
        known=conn.execute("SELECT stop_id FROM stops WHERE stop_id IN (%s,%s)",(origin,destination)).fetchall()
        if len(known)!=(1 if origin==destination else 2): raise HTTPException(400,"Choose valid origin and destination stops")
        rows=[]
        # Previous service day includes GTFS times past midnight; next day permits overnight trips.
        for offset in (-1,0,1):
            service_day=at.date()+timedelta(days=offset)
            weekday=service_day.strftime("%A").lower()
            services=conn.execute(f"""SELECT service_id FROM calendar WHERE {weekday}=1 AND start_date<=%s AND end_date>=%s
                UNION SELECT service_id FROM calendar_dates WHERE date=%s AND exception_type=1
                EXCEPT SELECT service_id FROM calendar_dates WHERE date=%s AND exception_type=2""",(service_day,)*4).fetchall()
            ids=[r["service_id"] for r in services]
            data=conn.execute("""SELECT s.*,t.route_id,t.trip_headsign,r.route_short_name,r.route_long_name FROM stop_times s
                JOIN trips t USING(trip_id) JOIN routes r USING(route_id) WHERE t.service_id=ANY(%s)
                ORDER BY s.trip_id,s.stop_sequence""",(ids,)).fetchall()
            for row in data:
                row["arrival"]+=offset*86400
                row["departure"]+=offset*86400
                row["trip_id"]=str(offset)+":"+row["trip_id"]
            rows.extend(data)
        departure=at.hour*3600+at.minute*60+at.second
        # Limit the search to departures and arrivals in the next 24 hours.
        rows=[r for r in rows if departure<=r["departure"]<=departure+86400 and r["arrival"]<=departure+86400]
        result=plan(rows,origin,destination,departure,max_transfers)
        if not result: raise HTTPException(404,"No scheduled journey within 24 hours and the selected transfer limit")
        result["departure"]=departure
        result["service_date"]=at.date().isoformat()
        return result
