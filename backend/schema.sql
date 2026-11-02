CREATE TABLE IF NOT EXISTS stops (stop_id text PRIMARY KEY, stop_name text NOT NULL, stop_lat double precision NOT NULL, stop_lon double precision NOT NULL);
CREATE TABLE IF NOT EXISTS routes (route_id text PRIMARY KEY, route_short_name text, route_long_name text, route_color text);
CREATE TABLE IF NOT EXISTS trips (trip_id text PRIMARY KEY, route_id text REFERENCES routes, service_id text NOT NULL, trip_headsign text);
CREATE TABLE IF NOT EXISTS stop_times (trip_id text REFERENCES trips, arrival integer NOT NULL, departure integer NOT NULL, stop_id text REFERENCES stops, stop_sequence integer NOT NULL, PRIMARY KEY(trip_id,stop_sequence));
CREATE INDEX IF NOT EXISTS stop_times_stop ON stop_times(stop_id,departure);
CREATE INDEX IF NOT EXISTS trips_service ON trips(service_id);
CREATE TABLE IF NOT EXISTS calendar (service_id text PRIMARY KEY, monday integer, tuesday integer, wednesday integer, thursday integer, friday integer, saturday integer, sunday integer, start_date date, end_date date);
CREATE TABLE IF NOT EXISTS calendar_dates (service_id text, date date, exception_type integer, PRIMARY KEY(service_id,date));
CREATE TABLE IF NOT EXISTS feed_meta (imported_at timestamptz DEFAULT now(), source text);
