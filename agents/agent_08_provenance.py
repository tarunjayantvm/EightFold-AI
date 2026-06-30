from datetime import datetime, timezone


def build_provenance(merged: dict, all_records: list[dict]) -> dict:
    """Track every field value with source, method, confidence, section, and timestamp."""
    provenance = []

    FIELD_METHOD = {
        "csv": "csv_parse",
        "ats_json": "json_parse",
        "resume_pdf": "regex + rule parser",
        "github": "api_call",
        "linkedin": "profile_enrichment"
    }

    FIELD_SECTION = {
        "full_name": "Identity",
        "emails": "Contact",
        "phones": "Contact",
        "headline": "Summary",
        "skills": "Skills",
        "experience": "Experience",
        "education": "Education",
        "location": "Location",
        "links": "Links",
        "years_experience": "Experience"
    }

    tracked_fields = [
        "full_name", "emails", "phones", "headline",
        "skills", "experience", "education",
        "location", "links", "years_experience"
    ]

    for field in tracked_fields:
        contributions = []
        for rec in all_records:
            val = rec.get(field)
            src = rec.get("source", "unknown")
            if field == "location" and isinstance(val, dict):
                val = val.get("city") or val.get("country")
            if val in [None, "", [], {}]:
                continue
            contributions.append({
                "field": field,
                "source": src,
                "method": FIELD_METHOD.get(src, "unknown"),
                "confidence": 0.9 if src == "resume_pdf" else 0.8,
                "page": 1,
                "section": FIELD_SECTION.get(field, "General"),
                "value": str(val)[:140],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        if contributions:
            winner = max(contributions, key=lambda item: (item["confidence"], item["source"] != "unknown"))
            provenance.append({
                "field": field,
                "sources": contributions,
                "final_source": winner["source"]
            })

    merged["provenance"] = provenance
    return merged