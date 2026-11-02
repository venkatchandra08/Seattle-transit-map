import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from routing import plan

def trip(name, stops, route=None):
    return [dict(trip_id=name,route_id=route or name,route_short_name=route or name,route_long_name='',trip_headsign='Downtown',stop_id=s,arrival=t,departure=t,stop_sequence=i) for i,(s,t) in enumerate(stops)]

class RoutingTests(unittest.TestCase):
    def test_fewer_transfers_beats_faster_arrival(self):
        rows=trip('direct',[('A',100),('C',1000)])+trip('one',[('A',100),('B',200)])+trip('two',[('B',330),('C',400)])
        r=plan(rows,'A','C',90)
        self.assertEqual((r['transfers'],r['arrival']),(0,1000))
    def test_earliest_arrival_breaks_tie(self):
        rows=trip('slow',[('A',100),('C',800)])+trip('fast',[('A',120),('C',300)])
        self.assertEqual(plan(rows,'A','C',90)['arrival'],300)
    def test_transfer_buffer_and_limit(self):
        rows=trip('one',[('A',100),('B',200)])+trip('missed',[('B',300),('C',400)])+trip('valid',[('B',320),('C',500)])
        r=plan(rows,'A','C',90)
        self.assertEqual(r['legs'][1]['trip_id'],'valid')
        self.assertEqual(r['transfers'],1)
        self.assertIsNone(plan(rows,'A','C',90,max_transfers=0))
    def test_missed_initial_departure(self):
        self.assertIsNone(plan(trip('bus',[('A',100),('B',200)]),'A','B',101))
    def test_overnight_seconds(self):
        r=plan(trip('night',[('A',86300),('B',87000)]),'A','B',86200)
        self.assertEqual(r['arrival'],87000)
    def test_same_stop(self):
        self.assertEqual(plan([],'A','A',100)['legs'],[])
    def test_no_backward_travel(self):
        self.assertIsNone(plan(trip('bus',[('A',100),('B',200)]),'B','A',90))
    def test_staying_aboard_needs_no_buffer(self):
        self.assertEqual(plan(trip('bus',[('A',100),('B',101),('C',102)]),'A','C',100)['arrival'],102)

if __name__=='__main__': unittest.main()
