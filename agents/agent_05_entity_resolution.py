import re


def _normalize_name(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _canonical_company(value: str) -> str:
    name = _normalize_name(value)
    aliases = {
        "infosys": "Infosys",
        "hcl tech": "HCL Tech",
        "hcl": "HCL Tech",
        "raarya": "Raarya"
    }
    return aliases.get(name, value.strip() if value else "")


def _canonical_institution(value: str) -> str:
    name = _normalize_name(value)
    aliases = {
        "sri ramakrishna engineering college": "Sri Ramakrishna Engineering College",
        "sri ramakrishna engineering college coimbatore": "Sri Ramakrishna Engineering College"
    }
    return aliases.get(name, value.strip() if value else "")


def resolve_entities(records: list[dict]) -> list[dict]:
    """Resolve likely duplicates across education, experience, and skill entities before merge."""
    resolved = []
    for record in records:
        resolved_record = dict(record)

        education = []
        for edu in record.get("education") or []:
            if not isinstance(edu, dict):
                continue
            normalized = dict(edu)
            normalized["institution"] = _canonical_institution(normalized.get("institution") or "") or normalized.get("institution") or ""
            education.append(normalized)
        resolved_record["education"] = education

        experience = []
        for exp in record.get("experience") or []:
            if not isinstance(exp, dict):
                continue
            normalized = dict(exp)
            normalized["company"] = _canonical_company(normalized.get("company") or "") or normalized.get("company") or ""
            experience.append(normalized)
        resolved_record["experience"] = experience

        skills = []
        seen = set()
        for skill in record.get("skills") or []:
            value = str(skill).strip()
            if not value:
                continue
            key = value.lower()
            if key not in seen:
                seen.add(key)
                skills.append(value)
        resolved_record["skills"] = skills
        resolved.append(resolved_record)
    return resolved