# Priority order — higher index = higher trust
SOURCE_PRIORITY = {
    "csv": 1,
    "ats_json": 2,
    "resume_pdf": 3,
    "github": 4,
    "linkedin": 5
}


def resolve_conflicts(merged: dict, all_records: list[dict]) -> dict:
    """Apply priority rules when multiple sources provide different values for the same field."""
    resolution_log = []

    def best_value(field: str):
        candidates = []
        for rec in all_records:
            val = rec.get(field)
            if val in [None, "", [], {}]:
                continue
            src = rec.get("source", "unknown")
            priority = SOURCE_PRIORITY.get(src, 0)
            candidates.append((priority, src, val))

        if not candidates:
            return None, None

        candidates.sort(key=lambda x: x[0], reverse=True)
        winner_priority, winner_source, winner_val = candidates[0]

        if len(candidates) > 1:
            values = [str(c[2]) for c in candidates]
            if len(set(values)) > 1:
                resolution_log.append({
                    "field": field,
                    "winner": winner_val,
                    "source": winner_source,
                    "reason": f"Priority rule: {winner_source} (priority={winner_priority}) wins",
                    "discarded": [{"source": c[1], "value": c[2]} for c in candidates[1:]]
                })

        return winner_val, winner_source

    best_name, _ = best_value("full_name")
    if best_name and best_name != merged.get("full_name"):
        merged["full_name"] = best_name

    best_headline, _ = best_value("headline")
    if best_headline:
        merged["headline"] = best_headline

    if not merged.get("location"):
        merged["location"] = {"city": None, "region": None, "country": None}

    merged["_conflict_log"] = resolution_log
    return merged