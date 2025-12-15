from datetime import datetime


def intervals_overlap(s1: datetime, e1: datetime, s2: datetime, e2: datetime) -> bool:
    # Overlap if s1 < e2 and s2 < e1; equality means touching but not overlapping
    return s1 < e2 and s2 < e1


def clamp_interval(s1: datetime, e1: datetime, s2: datetime, e2: datetime):
    # Returns the overlapping interval, or None if no overlap
    if not intervals_overlap(s1, e1, s2, e2):
        return None
    start = max(s1, s2)
    end = min(e1, e2)
    return (start, end) if start < end else None


def hours_between(s: datetime, e: datetime) -> float:
    return (e - s).total_seconds() / 3600.0
