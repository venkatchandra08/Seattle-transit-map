import os
import psycopg
from psycopg.rows import dict_row

def connect():
    return psycopg.connect(os.environ.get("DATABASE_URL", "postgresql://transit:transit@localhost/transit"), row_factory=dict_row)
