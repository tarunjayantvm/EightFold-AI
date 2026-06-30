import re
from datetime import date
from agents.agent_04_normalization import normalize_skill


def _normalize_text(value: str) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _token_set(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _normalize_text(value)))


def _similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    left_tokens = _token_set(left)
    right_tokens = _token_set(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return overlap / union if union else 0.0


def _same_education(left: dict, right: dict) -> bool:
    left_inst = left.get("institution") or ""
    right_inst = right.get("institution") or ""
    left_degree = left.get("degree") or ""
    right_degree = right.get("degree") or ""
    if left_inst and right_inst:
        if _similarity(left_inst, right_inst) >= 0.7:
            return True
    if left_degree and right_degree and _similarity(left_degree, right_degree) >= 0.8:
        return True
    return False


def _merge_education(left: dict, right: dict) -> dict:
    merged = {
        "institution": left.get("institution") or right.get("institution") or "",
        "degree": left.get("degree") or right.get("degree") or "",
        "field": left.get("field") or right.get("field") or "",
        "start_year": left.get("start_year") or right.get("start_year") or "",
        "end_year": left.get("end_year") or right.get("end_year") or "",
        "cgpa": left.get("cgpa") or right.get("cgpa") or "",
        "location": left.get("location") or right.get("location") or ""
    }
    return merged


def _same_experience(left: dict, right: dict) -> bool:
    left_company = (left.get("company") or "").lower()
    right_company = (right.get("company") or "").lower()
    left_title = (left.get("title") or "").lower()
    right_title = (right.get("title") or "").lower()
    if left_company and right_company and left_company == right_company and left_title and right_title and left_title == right_title:
        return True
    return False


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    s = str(value).strip()
    m = re.match(r"^(\d{4})-(\d{2})$", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)
    m = re.match(r"^(\d{4})$", s)
    if m:
        return date(int(m.group(1)), 1, 1)
    return None


def _months_between(start_date: date, end_date: date) -> int:
    return max(0, (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month))


def _format_duration(months: int) -> str:
    if months <= 0:
        return ""
    years = months // 12
    remaining = months % 12
    if years and remaining:
        return f"{years} years {remaining} months"
    if years:
        return f"{years} years"
    return f"{months} months"


def _experience_interval(exp: dict) -> tuple[date, date] | None:
    start = _parse_date(exp.get("start") or "")
    end = _parse_date(exp.get("end") or "")
    if not start:
        return None
    if not end:
        end = date.today()
    if end < start:
        return None
    return start, end


def _merge_experience(left: dict, right: dict) -> dict:
    merged = {
        "company": left.get("company") or right.get("company") or "",
        "title": left.get("title") or right.get("title") or "",
        "location": left.get("location") or right.get("location") or "",
        "start": left.get("start") or right.get("start") or "",
        "end": left.get("end") or right.get("end") or "",
        "duration": left.get("duration") or right.get("duration") or "",
        "tech_stack": list(dict.fromkeys((left.get("tech_stack") or []) + (right.get("tech_stack") or []))),
        "summary": left.get("summary") or right.get("summary") or "",
        "achievements": list(dict.fromkeys((left.get("achievements") or []) + (right.get("achievements") or [])))
    }
    return merged


def _merge_intervals(intervals: list[tuple[date, date]]) -> int:
    if not intervals:
        return 0
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged_start, merged_end = sorted_intervals[0]
    total_months = 0
    for start, end in sorted_intervals[1:]:
        if start <= merged_end:
            if end > merged_end:
                merged_end = end
        else:
            total_months += _months_between(merged_start, merged_end)
            merged_start, merged_end = start, end
    total_months += _months_between(merged_start, merged_end)
    return total_months


def merge_records(records: list[dict]) -> dict:
    """Combine multiple normalized canonical records for the same candidate into one merged record."""
    if not records:
        return {}

    merged = {
        "candidate_id": None,
        "full_name": None,
        "emails": [],
        "phones": [],
        "location": {"city": None, "region": None, "country": None},
        "links": {"linkedin": None, "github": None, "portfolio": None, "other": []},
        "headline": None,
        "years_experience": None,
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "_sources": []
    }

    seen_emails = set()
    seen_phones = set()
    seen_skills = set()

    for rec in records:
        source = rec.get("source", "unknown")
        merged["_sources"].append(source)

        if not merged["candidate_id"] and rec.get("candidate_id"):
            merged["candidate_id"] = rec["candidate_id"]

        if not merged["full_name"] and rec.get("full_name"):
            merged["full_name"] = rec["full_name"]

        for email in rec.get("emails", []):
            normalized = str(email).lower().strip()
            if normalized and normalized not in seen_emails:
                seen_emails.add(normalized)
                merged["emails"].append(normalized)

        for phone in rec.get("phones", []):
            normalized = str(phone).strip()
            if normalized and normalized not in seen_phones:
                seen_phones.add(normalized)
                merged["phones"].append(normalized)

        for skill in rec.get("skills", []):
            normalized = normalize_skill(skill)
            if normalized and normalized.lower() not in seen_skills:
                seen_skills.add(normalized.lower())
                merged["skills"].append(normalized)

        loc = rec.get("location", {}) or {}
        for field in ["city", "region", "country"]:
            if not merged["location"][field] and loc.get(field):
                merged["location"][field] = loc[field]

        links = rec.get("links", {}) or {}
        for field in ["linkedin", "github", "portfolio"]:
            if not merged["links"][field] and links.get(field):
                merged["links"][field] = links[field]

        if not merged["headline"] and rec.get("headline"):
            merged["headline"] = rec["headline"]

        yr = rec.get("years_experience")
        if yr is not None:
            if merged["years_experience"] is None:
                merged["years_experience"] = yr
            else:
                merged["years_experience"] = max(merged["years_experience"], yr)

        for exp in rec.get("experience", []) or []:
            if not isinstance(exp, dict):
                continue
            present = False
            for existing in merged["experience"]:
                if _same_experience(existing, exp):
                    existing.update(_merge_experience(existing, exp))
                    present = True
                    break
            if not present:
                merged["experience"].append(exp)

    experience_intervals = []
    for exp in merged["experience"]:
        if exp.get("duration"):
            duration = str(exp.get("duration")).strip()
            if not duration:
                interval = _experience_interval(exp)
                if interval:
                    months = _months_between(*interval)
                    exp["duration"] = _format_duration(months)
                    experience_intervals.append(interval)
        else:
            interval = _experience_interval(exp)
            if interval:
                months = _months_between(*interval)
                exp["duration"] = _format_duration(months)
                experience_intervals.append(interval)

    total_months = _merge_intervals(experience_intervals)
    derived_years = round(total_months / 12, 1) if total_months else None
    if derived_years is not None:
        if merged["years_experience"] is None:
            merged["years_experience"] = derived_years
        else:
            try:
                existing_years = float(merged["years_experience"])
            except (TypeError, ValueError):
                existing_years = 0.0
            merged["years_experience"] = max(existing_years, derived_years)

    for rec in records:
        for edu in rec.get("education", []) or []:
            if not isinstance(edu, dict):
                continue
            present = False
            for existing in merged["education"]:
                if _same_education(existing, edu):
                    existing.update(_merge_education(existing, edu))
                    present = True
                    break
            if not present:
                merged["education"].append(edu)

        for project in rec.get("projects", []) or []:
            if project not in merged["projects"]:
                merged["projects"].append(project)

        for cert in rec.get("certifications", []) or []:
            if cert not in merged["certifications"]:
                merged["certifications"].append(cert)

    return merged