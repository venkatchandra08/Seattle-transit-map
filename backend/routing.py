"""Time-dependent round routing: first reachable boarding round wins.
Each round scans every usable trip and keeps earliest arrival per stop.
This minimizes boardings first, arrival time second. Transfers occur at the
same GTFS stop only. Staying on a trip never incurs a transfer buffer.
"""
from collections import defaultdict

def plan(rows, origin, destination, departure, max_transfers=4, transfer_buffer=120):
    if origin == destination:
        return {"transfers":0,"arrival":departure,"legs":[]}
    trips=defaultdict(list)
    for row in rows: trips[row["trip_id"]].append(row)
    previous={origin:(departure,[])}
    for boarding in range(1,max_transfers+2):
        current={}
        for trip in trips.values():
            trip.sort(key=lambda x:x["stop_sequence"])
            boarded=None
            for stop in trip:
                sid=stop["stop_id"]
                if boarded:
                    start,path=boarded
                    arrival=stop["arrival"]
                    if sid not in current or arrival < current[sid][0]:
                        leg={"trip_id":stop["trip_id"],"route_id":stop["route_id"],"route":stop["route_short_name"] or stop["route_long_name"],"headsign":stop["trip_headsign"],"from":start["stop_id"],"to":sid,"departure":start["departure"],"arrival":arrival}
                        current[sid]=(arrival,path+[leg])
                ready=previous.get(sid)
                if boarded is None and ready and ready[0]+(transfer_buffer if boarding>1 else 0)<=stop["departure"]:
                    boarded=(stop,ready[1])
        if destination in current:
            arrival,legs=current[destination]
            return {"transfers":len(legs)-1,"arrival":arrival,"legs":legs}
        previous=current
        if not previous: break
    return None
