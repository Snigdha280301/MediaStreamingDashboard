import os
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

_RETRY_WAITS = [2, 4, 8]


class TMDBClient:
    def __init__(self):
        self.base_url = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
        self._headers = {"Authorization": f"Bearer {os.getenv('TMDB_READ_TOKEN')}"}
        self._prev_state: dict[int, int] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"
        for attempt, wait in enumerate(_RETRY_WAITS, start=1):
            response = requests.get(url, headers=self._headers)
            if response.status_code == 429:
                if attempt == len(_RETRY_WAITS):
                    response.raise_for_status()
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        return {}  # unreachable, satisfies type checkers

    def _build_record(
        self,
        item: dict,
        rank: int,
        prev_rank: int | None,
        source: str,
    ) -> dict:
        return {
            "tmdb_id": item.get("id"),
            "title": item.get("title") or item.get("name"),
            "media_type": item.get("media_type"),
            "rank": rank,
            "previous_rank": prev_rank,
            "rank_change": (rank - prev_rank) if prev_rank is not None else 0,
            "popularity": item.get("popularity"),
            "vote_average": item.get("vote_average"),
            "vote_count": item.get("vote_count"),
            "genre_ids": str(item.get("genre_ids", [])),
            "overview": item.get("overview"),
            "release_date": item.get("release_date") or item.get("first_air_date"),
            "original_language": item.get("original_language"),
            "endpoint_source": source,
            "polled_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def poll_all(self) -> list[dict]:
        endpoints = [
            ("/trending/all/day",   "trending_all",   None),
            ("/trending/movie/day", "trending_movie",  "movie"),
            ("/trending/tv/day",    "trending_tv",     "tv"),
            ("/movie/now_playing",  "now_playing",     "movie"),
            ("/tv/popular",         "popular_tv",      "tv"),
        ]

        seen: dict[int, bool] = {}
        records: list[dict] = []

        for endpoint, source, forced_media_type in endpoints:
            items = self._get(endpoint).get("results", [])
            for rank, item in enumerate(items, start=1):
                tmdb_id = item.get("id")
                if tmdb_id is None or tmdb_id in seen:
                    continue
                seen[tmdb_id] = True

                if forced_media_type:
                    item = {**item, "media_type": forced_media_type}

                prev_rank = self._prev_state.get(tmdb_id)
                records.append(self._build_record(item, rank, prev_rank, source))

        self._prev_state = {r["tmdb_id"]: r["rank"] for r in records}
        return records
