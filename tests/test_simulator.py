import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from simulator.satellite import Satellite
from simulator.telemetry_generator import SimulatorEngine
from simulator.anomaly_generator import AnomalyEngine, AnomalyType
import random


def test_satellite_tick_produces_small_deltas():
    sat = Satellite("SAT-001", seed=1)
    before = sat.state.battery_voltage
    sat.tick()
    after = sat.state.battery_voltage
    assert abs(after - before) < 1.0


def test_engine_generates_one_event_per_satellite_per_tick():
    engine = SimulatorEngine(num_satellites=5, anomaly_injection_enabled=False, seed=1)
    events = engine.tick_all()
    assert len(events) == 5
    assert {e["satellite_id"] for e in events} == {f"SAT-{i+1:03d}" for i in range(5)}


def test_engine_seed_is_reproducible():
    e1 = SimulatorEngine(num_satellites=3, anomaly_injection_enabled=False, seed=42)
    e2 = SimulatorEngine(num_satellites=3, anomaly_injection_enabled=False, seed=42)
    ev1 = e1.tick_all()
    ev2 = e2.tick_all()
    for a, b in zip(ev1, ev2):
        assert a["battery_voltage"] == b["battery_voltage"]


def test_battery_failure_anomaly_declines_over_ticks():
    sat = Satellite("SAT-001", seed=1)
    engine = AnomalyEngine(random.Random(1))
    engine.active = AnomalyType.BATTERY_FAILURE
    engine.ticks_remaining = 10

    readings = []
    for _ in range(10):
        engine.apply(sat)
        readings.append(sat.state.battery_voltage)

    assert readings[-1] < readings[0]
    assert engine.active is None


def test_sensor_corruption_produces_absurd_value():
    sat = Satellite("SAT-001", seed=1)
    engine = AnomalyEngine(random.Random(1))
    engine.active = AnomalyType.SENSOR_CORRUPTION
    engine.ticks_remaining = 1
    engine.apply(sat)
    assert sat.state.battery_temperature == 9999.0


def test_missing_field_scenario_removes_key_from_event():
    engine = SimulatorEngine(num_satellites=1, anomaly_injection_enabled=True, seed=1)
    sat_id = list(engine.satellites.keys())[0]
    engine.anomaly_engines[sat_id].active = AnomalyType.MISSING_FIELD
    engine.anomaly_engines[sat_id].ticks_remaining = 1
    events = engine.tick_all()
    assert "battery_temperature" not in events[0]