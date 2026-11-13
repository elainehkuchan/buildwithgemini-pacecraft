"""Training pace calculation tool for runners."""

import re
from typing import Any, Dict


def _parse_time_to_seconds(time_str: str) -> float:
    """Parse time formats like '22:30', '1:45:00', or '25m' into total seconds."""
    clean = str(time_str).strip().lower()
    
    # Format: HH:MM:SS or MM:SS
    if ":" in clean:
        parts = [float(p) for p in clean.split(":")]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
    
    # Single number assuming minutes
    match = re.search(r"(\d+(\.\d+)?)", clean)
    if match:
        return float(match.group(1)) * 60
    return 1200.0  # default fallback to 20 mins


def _format_pace(seconds_per_unit: float) -> str:
    """Format seconds into M:SS min/unit string."""
    mins = int(seconds_per_unit // 60)
    secs = int(round(seconds_per_unit % 60))
    if secs == 60:
        mins += 1
        secs = 0
    return f"{mins}:{secs:02d}"


def calculate_training_paces(race_distance: str, race_time: str) -> Dict[str, Any]:
    """Calculate recommended training pace zones (Easy, Marathon, Threshold, Interval, Repetition)
    based on a recent race or time-trial performance (e.g. 5k, 10k, half marathon, marathon).

    Args:
        race_distance: The distance of the baseline race (e.g. '5k', '10k', 'half_marathon', 'marathon', '1_mile').
        race_time: The finish time (e.g. '22:30', '48:00', '1:45:00').

    Returns:
        A dictionary with calculated paces per mile and per kilometer across all training zones.
    """
    distance_clean = str(race_distance).lower().replace(" ", "").replace("-", "_")
    
    # Distance in miles
    distances_in_miles = {
        "1_mile": 1.0,
        "1mile": 1.0,
        "mile": 1.0,
        "5k": 3.10686,
        "10k": 6.21371,
        "half_marathon": 13.1094,
        "halfmarathon": 13.1094,
        "half": 13.1094,
        "13.1": 13.1094,
        "marathon": 26.2188,
        "full_marathon": 26.2188,
        "26.2": 26.2188,
    }
    
    base_dist = distances_in_miles.get(distance_clean, 3.10686)
    total_sec = _parse_time_to_seconds(race_time)
    baseline_pace_per_mile = total_sec / base_dist

    # Normalize to 5K pace as reference using Riegel formula: T2 = T1 * (D2/D1)^1.06
    five_k_pace_sec = baseline_pace_per_mile * ((3.10686 / base_dist) ** 0.06)

    # Standard training pace multipliers relative to 5K pace
    zones = {
        "easy_recovery": {"name": "Easy / Recovery Run", "multiplier": 1.35, "desc": "Aerobic base building and recovery between hard sessions."},
        "marathon_pace": {"name": "Marathon Pace (Steady)", "multiplier": 1.20, "desc": "Aerobic stamina and race-specific endurance."},
        "threshold_tempo": {"name": "Threshold / Tempo", "multiplier": 1.08, "desc": "Lactate threshold runs (comfortably hard, 20-40 min efforts)."},
        "interval_vo2max": {"name": "Interval (VO2 Max)", "multiplier": 0.98, "desc": "Hard 3-5 minute intervals to raise aerobic capacity."},
        "repetition_speed": {"name": "Repetition / Speed", "multiplier": 0.92, "desc": "Short, fast 200m-400m repeats for neuromuscular efficiency."},
    }

    result_zones = {}
    for key, info in zones.items():
        mile_sec = five_k_pace_sec * info["multiplier"]
        km_sec = mile_sec / 1.60934
        result_zones[key] = {
            "zone_name": info["name"],
            "pace_per_mile": f"{_format_pace(mile_sec)} /mi",
            "pace_per_km": f"{_format_pace(km_sec)} /km",
            "purpose": info["desc"],
        }

    return {
        "baseline_input": {"race_distance": race_distance, "race_time": race_time},
        "training_paces": result_zones,
    }
