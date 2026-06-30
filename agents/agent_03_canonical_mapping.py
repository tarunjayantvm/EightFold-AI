def map_to_canonical(raw: dict) -> dict:
    """Convert any source-specific raw dict into the standard canonical field schema."""
    source = raw.get("source", "unknown")

    canonical = {
        "candidate_id":    raw.get("candidate_id") or None,
        "full_name":       raw.get("full_name") or None,
        "emails":          [],
        "phones":          [],
        "location": {
            "city":    None,
            "region":  None,
            "country": None
        },
        "links": {
            "linkedin":  raw.get("linkedin_url") or None,
            "github":    raw.get("github_url") or None,
            "portfolio": raw.get("portfolio") or None,
            "other":     []
        },
        "headline":        raw.get("title") or raw.get("headline") or None,
        "years_experience": raw.get("years_exp"),
        "skills":          [],
        "experience":      [],
        "education":       [],
        "projects":       [],
        "certifications": [],
        "source":          source
    }

    email = raw.get("email")
    if email:
        canonical["emails"] = [str(email).strip().lower()]

    phone = raw.get("phone")
    if phone:
        canonical["phones"] = [str(phone).strip()]

    skills = raw.get("skills") or []
    canonical["skills"] = [str(s) for s in skills if s]

    for edu in raw.get("education") or []:
        if isinstance(edu, dict):
            canonical["education"].append({
                "institution": edu.get("institution") or "",
                "degree": edu.get("degree") or "",
                "field": edu.get("field") or "",
                "start_year": edu.get("start_year") or edu.get("start") or "",
                "end_year": edu.get("end_year") or edu.get("end") or "",
                "cgpa": edu.get("cgpa") or "",
                "location": edu.get("location") or ""
            })

    for exp in raw.get("experience") or []:
        if isinstance(exp, dict):
            canonical["experience"].append({
                "company": exp.get("company") or raw.get("company") or None,
                "title": exp.get("title") or raw.get("title") or None,
                "location": exp.get("location") or None,
                "start": exp.get("start") or None,
                "end": exp.get("end") or None,
                "duration": exp.get("duration") or None,
                "tech_stack": exp.get("tech_stack") or [],
                "summary": exp.get("summary") or None,
                "achievements": exp.get("achievements") or []
            })

    if not canonical["experience"] and (raw.get("company") or raw.get("title")):
        canonical["experience"] = [{
            "company": raw.get("company") or None,
            "title": raw.get("title") or None,
            "location": None,
            "start": None,
            "end": None,
            "duration": None,
            "tech_stack": [],
            "summary": None,
            "achievements": []
        }]

    for project in raw.get("projects") or []:
        if isinstance(project, dict):
            canonical["projects"].append(project)

    for cert in raw.get("certifications") or []:
        if isinstance(cert, dict):
            canonical["certifications"].append(cert)

    if raw.get("location"):
        parts = [p.strip() for p in str(raw["location"]).split(",") if p.strip()]
        if len(parts) >= 2:
            canonical["location"]["city"] = parts[0]
            canonical["location"]["region"] = parts[1] if len(parts) > 1 else None
            canonical["location"]["country"] = parts[-1] if len(parts) > 2 else None
        elif len(parts) == 1:
            canonical["location"]["city"] = parts[0]

    if source == "github" and raw.get("location"):
        parts = [p.strip() for p in str(raw["location"]).split(",") if p.strip()]
        canonical["location"]["city"] = parts[0] if len(parts) > 0 else None
        canonical["location"]["country"] = parts[-1] if len(parts) > 1 else None

    return canonical