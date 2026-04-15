from typing import Optional
from typing_extensions import TypedDict


class MediaRecord(TypedDict):
    tmdb_id: int
    title: str
    media_type: str
    rank: int
    previous_rank: Optional[int]
    rank_change: int
    popularity: float
    vote_average: Optional[float]
    vote_count: Optional[int]
    genre_ids: str
    overview: Optional[str]
    release_date: Optional[str]
    original_language: Optional[str]
    endpoint_source: str
    polled_at: str


class AgentState(TypedDict):
    rankings: list[MediaRecord]
    anomalies: list[MediaRecord]
    commentary: str
    severity: Optional[str]
    anomaly_detected: bool
    titles_mentioned: list[str]
    run_id: Optional[str]
    polled_at: Optional[str]
    error: Optional[str]


class MediaPulseState(TypedDict):
    rankings: list[dict]
    anomalies: list[dict]
    commentary: dict
    titles_mentioned: list[str]
    severity: str
    anomaly_detected: bool
    run_id: str
    polled_at: str
    error: Optional[str]