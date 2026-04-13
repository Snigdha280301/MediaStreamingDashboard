import pandas as pd


def validate_records(records: list[dict]) -> tuple[list[dict], list[dict], dict]:
    df = pd.DataFrame(records) if records else pd.DataFrame()

    if df.empty:
        report = {"total": 0, "valid": 0, "invalid": 0, "failures": {}}
        print("Validated: 0 valid, 0 invalid")
        return [], [], report

    # --- individual rule masks (True = passes) ---------------------------
    rules: dict[str, pd.Series] = {
        "tmdb_id_not_null":     df["tmdb_id"].notna(),
        "title_not_null":       df["title"].notna(),
        "title_not_empty":      df["title"].astype(str).str.strip() != "",
        "rank_in_range":        df["rank"].between(1, 20),
        "media_type_valid":     df["media_type"].isin(["movie", "tv"]),
        "vote_average_in_range": df["vote_average"].between(0.0, 10.0),
        "popularity_positive":  df["popularity"] > 0,
        "polled_at_not_null":   df["polled_at"].notna(),
    }

    # --- combined pass mask ----------------------------------------------
    all_pass = pd.Series(True, index=df.index)
    for mask in rules.values():
        all_pass &= mask

    valid_df   = df[all_pass]
    invalid_df = df[~all_pass]

    # --- per-rule failure counts for the report --------------------------
    failures = {
        rule: int((~mask).sum())
        for rule, mask in rules.items()
        if (~mask).any()
    }

    report = {
        "total":    len(df),
        "valid":    len(valid_df),
        "invalid":  len(invalid_df),
        "failures": failures,
    }

    print(f"Validated: {report['valid']} valid, {report['invalid']} invalid")

    return valid_df.to_dict("records"), invalid_df.to_dict("records"), report
