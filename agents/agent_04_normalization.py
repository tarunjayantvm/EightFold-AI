import re

# ── Phone normalization ──────────────────

def normalize_phone(phone: str, default_cc: str = "91") -> str | None:
    """Converts any phone to E.164 format."""
    if not phone:
        return None

    has_plus = phone.strip().startswith("+")
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return None
    if has_plus:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+{default_cc}{digits}"
    if len(digits) > 10:
        return f"+{digits}"
    return None


# ── Date normalization ───────────────────

MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    "january": "01", "february": "02", "march": "03",
    "april": "04", "june": "06", "july": "07",
    "august": "08", "september": "09", "october": "10",
    "november": "11", "december": "12"
}


def normalize_date(date_str: str) -> str | None:
    """Converts any date format to YYYY-MM."""
    if not date_str:
        return None
    s = str(date_str).strip().lower()

    m = re.match(r"(\d{4})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    m = re.match(r"([a-z]+)\s+(\d{4})", s)
    if m and m.group(1) in MONTH_MAP:
        return f"{m.group(2)}-{MONTH_MAP[m.group(1)]}"

    m = re.match(r"(\d{1,2})[/\-](\d{4})", s)
    if m:
        return f"{m.group(2)}-{m.group(1).zfill(2)}"

    m = re.match(r"^(\d{4})$", s)
    if m:
        return f"{m.group(1)}-01"

    if re.match(r"^\d{4}$", s):
        return f"{s}-01"
    return None


# ── Skill normalization ──────────────────

SKILL_MAP = {
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "natural language processing": "Natural Language Processing",
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "py": "Python",
    "python": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "react": "React",
    "reactjs": "React",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node": "Node.js",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "java": "Java",
    "c++": "C++",
    "cpp": "C++",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "sklearn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "spring boot": "Spring Boot",
    "spring": "Spring Boot",
    "git": "Git",
    "github": "GitHub",
    "linux": "Linux",
    "bash": "Bash",
    "shell": "Bash",
    "tableau": "Tableau",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "c": "C",
    "r": "R",
    "html5": "HTML5",
    "css3": "CSS3",
    "gen-ai": "GenAI",
    "genai": "GenAI",
    "generative ai": "GenAI",
    "rest api": "REST API",
    "rest apis": "REST APIs",
    "restapis": "REST APIs",
    "vs code": "VS Code",
    "vscode": "VS Code",
    "opencl": "OpenCL",
    "cuda": "CUDA",
    "jpa": "JPA/Hibernate",
    "hibernate": "JPA/Hibernate",
    "jpa/hibernate": "JPA/Hibernate",
}


def normalize_skill(skill: str) -> str:
    if skill is None:
        return ""
    text = str(skill).strip()
    if not text:
        return ""
    return SKILL_MAP.get(text.lower(), text.title())


def normalize_skills(skills: list) -> list:
    seen, result = set(), []
    for s in skills or []:
        canon = normalize_skill(s)
        if canon and canon.lower() not in seen:
            seen.add(canon.lower())
            result.append(canon)
    return result


# ── Location normalization ───────────────

COUNTRY_MAP = {
    "india": "IN", "usa": "US", "united states": "US",
    "uk": "GB", "united kingdom": "GB",
    "germany": "DE", "france": "FR",
    "canada": "CA", "australia": "AU",
    "singapore": "SG", "japan": "JP",
}


def normalize_country(country: str) -> str | None:
    if not country:
        return None
    return COUNTRY_MAP.get(country.strip().lower(), country.strip().upper()[:2])


# ── Main normalization agent ─────────────

def normalize(canonical: dict) -> dict:
    """Apply all normalizations to a canonical record."""
    phones = canonical.get("phones") or []
    if isinstance(phones, str):
        phones = [phones]
    canonical["phones"] = list(filter(None, [
        normalize_phone(p) for p in phones if p is not None
    ]))

    emails = canonical.get("emails") or []
    if isinstance(emails, str):
        emails = [emails]
    canonical["emails"] = [
        str(e).lower().strip()
        for e in emails
        if e
    ]

    canonical["skills"] = normalize_skills(canonical.get("skills") or [])

    loc = canonical.get("location") or {}
    if not isinstance(loc, dict):
        loc = {}
    canonical["location"] = {
        "city": loc.get("city"),
        "region": loc.get("region"),
        "country": normalize_country(loc.get("country")) if loc.get("country") else None
    }

    education = canonical.get("education") or []
    if not isinstance(education, list):
        education = [education] if education else []
    canonical["education"] = education
    for edu in education:
        if isinstance(edu, dict):
            if edu.get("end_year"):
                edu["end_year"] = normalize_date(str(edu["end_year"]))
            if edu.get("start_year"):
                edu["start_year"] = normalize_date(str(edu["start_year"]))

    experience = canonical.get("experience") or []
    if not isinstance(experience, list):
        experience = [experience] if experience else []
    canonical["experience"] = experience
    for exp in experience:
        if isinstance(exp, dict):
            if exp.get("start"):
                exp["start"] = normalize_date(exp["start"])
            if exp.get("end"):
                exp["end"] = normalize_date(exp["end"])
            if exp.get("tech_stack"):
                exp["tech_stack"] = normalize_skills(exp.get("tech_stack") or [])

    return canonical