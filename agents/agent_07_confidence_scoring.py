SOURCE_BASE_CONFIDENCE = {
    "csv": 0.80,
    "ats_json": 0.85,
    "resume_pdf": 0.90,
    "github": 0.95,
    "linkedin": 0.90
}


def score_confidence(merged: dict, all_records: list[dict]) -> dict:
    """Assign field-level and overall confidence scores using source trust and agreement."""
    scores = {}
    weights = {
        "full_name": 0.15,
        "emails": 0.10,
        "phones": 0.08,
        "headline": 0.08,
        "skills": 0.12,
        "experience": 0.16,
        "education": 0.14,
        "location": 0.08,
        "links": 0.09
    }

    def field_confidence(field: str) -> float:
        values_per_source = []
        for rec in all_records:
            val = rec.get(field)
            if field == "location" and isinstance(val, dict):
                val = val.get("city") or val.get("country")
            if val in [None, "", [], {}]:
                continue
            src = rec.get("source", "unknown")
            values_per_source.append((src, str(val).lower().strip()))

        if not values_per_source:
            return 0.0

        best_src = max(values_per_source, key=lambda x: SOURCE_BASE_CONFIDENCE.get(x[0], 0.5))
        base = SOURCE_BASE_CONFIDENCE.get(best_src[0], 0.5)
        unique_vals = {v for _, v in values_per_source}
        if len(unique_vals) == 1 and len(values_per_source) > 1:
            base = min(1.0, base + 0.05 * (len(values_per_source) - 1))
        return round(base, 2)

    for field in weights:
        scores[field] = field_confidence(field)

    total_weight = 0.0
    weighted_score = 0.0
    for field, weight in weights.items():
        value = scores[field]
        if value > 0:
            weighted_score += value * weight
            total_weight += weight

    overall = round(weighted_score / total_weight, 2) if total_weight else 0.0

    merged["field_confidence"] = scores
    merged["overall_confidence"] = overall
    return merged