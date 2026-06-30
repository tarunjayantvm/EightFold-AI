import csv
import json
import re
import os

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _clean_text(value) -> str:
    if value is None:
        return ""
    return str(value).replace("\ufeff", "").strip()


def _clean_list(values) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    return [str(v).strip() for v in values if str(v).strip()]


def _read_resume_text(path: str) -> str:
    if not os.path.exists(path):
        return ""

    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except Exception:
            try:
                with open(path, "rb") as handle:
                    return handle.read().decode("utf-8", errors="ignore")
            except Exception:
                return ""


def _extract_contact_fields(text: str, raw: dict) -> None:
    email_match = re.search(r"[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if email_match:
        raw["email"] = email_match.group()

    phone_match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text)
    if phone_match:
        raw["phone"] = phone_match.group().strip()

    github_match = re.search(r"github\.com/[\w\-]+", text)
    if github_match:
        raw["github_url"] = "https://" + github_match.group()

    linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", text)
    if linkedin_match:
        raw["linkedin_url"] = "https://" + linkedin_match.group()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        raw["full_name"] = lines[0]

    location_candidates = [
        line.strip() for line in text.splitlines()
        if line.strip() and re.search(r"\b(coimbatore|chennai|bangalore|hyderabad|mumbai|pune|delhi|tamil nadu|india)\b", line, re.I)
    ]
    if location_candidates:
        raw["location"] = location_candidates[0]


def _parse_section(text: str, heading: str) -> str:
    pattern = rf"(?is){heading}\s*(.*?)(?=\n\n(?:Experience|Projects|Skills|Certifications|Education)\b|\Z)"
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def _parse_education_section(section_text: str) -> list[dict]:
    entries = []
    current = None
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^(education|experience|projects|skills|certifications)$", line, re.I):
            continue
        if re.search(r"\b(B\.E|B\.Tech|B\.Sc|M\.Tech|MBA|M\.Sc|HSC|SSLC|Diploma|Bachelor|Master)\b", line, re.I) and not current:
            current = {"institution": "", "degree": line, "field": "", "start_year": "", "end_year": "", "cgpa": "", "location": ""}
            continue
        if current is None:
            current = {"institution": "", "degree": "", "field": "", "start_year": "", "end_year": "", "cgpa": "", "location": ""}
        if not current.get("institution") and not re.search(r"\b(B\.E|B\.Tech|B\.Sc|M\.Tech|MBA|M\.Sc|HSC|SSLC|Diploma|Bachelor|Master)\b", line, re.I):
            if re.search(r"\b(college|school|university|institute|academy)\b", line, re.I) or re.search(r"\b(edu|engineering|science|technology)\b", line, re.I):
                current["institution"] = line
                continue
        if not current.get("field") and re.search(r"\b(computer science|information technology|electronics|mechanical|civil|electrical|artificial intelligence|data science|engineering)\b", line, re.I):
            current["field"] = line
            continue
        if not current.get("location") and re.search(r"\b(coimbatore|chennai|bangalore|hyderabad|mumbai|pune|delhi|tamil nadu|india)\b", line, re.I):
            current["location"] = line
            continue
        if not current.get("cgpa") and re.search(r"cgpa|gpa", line, re.I):
            current["cgpa"] = re.search(r"([0-9]+(?:\.[0-9]+)?)", line).group(1) if re.search(r"([0-9]+(?:\.[0-9]+)?)", line) else line
            continue
        years = re.findall(r"\b(20\d{2}|19\d{2})\b", line)
        if years:
            if not current.get("start_year") and len(years) >= 1:
                current["start_year"] = years[0]
            if not current.get("end_year") and len(years) >= 2:
                current["end_year"] = years[1]
            elif not current.get("end_year") and len(years) >= 1:
                current["end_year"] = years[-1]
            continue
        if current.get("institution") and current.get("degree") and not current.get("field") and re.search(r"\b(science|engineering|technology|arts|commerce)\b", line, re.I):
            current["field"] = line
            continue
        if current.get("institution") and current.get("degree") and not current.get("location") and len(line.split()) <= 4:
            current["location"] = line
            continue
        if not current.get("institution"):
            current["institution"] = line

        if current.get("institution") and current.get("degree") and current.get("field") and current.get("end_year"):
            entries.append(current)
            current = None

    if current and any(current.values()):
        entries.append(current)
    return entries


def _parse_experience_section(section_text: str) -> list[dict]:
    entries = []
    current = None
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^(experience|education|projects|skills|certifications)$", line, re.I):
            continue
        if re.match(r"^[-•*]\s*", line):
            line = line[1:].strip()
        if re.search(r"\b(intern|developer|engineer|analyst|assistant|associate|manager)\b", line, re.I) and current is None:
            current = {"company": "", "title": line, "location": "", "start": "", "end": "", "duration": "", "tech_stack": [], "summary": "", "achievements": []}
            continue
        if current is None:
            current = {"company": "", "title": "", "location": "", "start": "", "end": "", "duration": "", "tech_stack": [], "summary": "", "achievements": []}
        if not current.get("company") and not re.search(r"\b(intern|developer|engineer|analyst|assistant|associate|manager)\b", line, re.I) and len(line.split()) <= 4:
            current["company"] = line
            continue
        if not current.get("title") and re.search(r"\b(intern|developer|engineer|analyst|assistant|associate|manager)\b", line, re.I):
            current["title"] = line
            continue
        if not current.get("location") and re.search(r"\b(coimbatore|chennai|bangalore|hyderabad|mumbai|pune|delhi|tamil nadu|india)\b", line, re.I):
            current["location"] = line
            continue
        if not current.get("start") and re.search(r"\b(20\d{2}|19\d{2})\b", line):
            years = re.findall(r"\b(20\d{2}|19\d{2})\b", line)
            if years:
                current["start"] = years[0]
            continue
        if not current.get("end") and re.search(r"\b(20\d{2}|19\d{2})\b", line):
            years = re.findall(r"\b(20\d{2}|19\d{2})\b", line)
            if years:
                current["end"] = years[-1]
            continue
        if not current.get("duration") and re.search(r"\b(months|years|weeks|days)\b", line, re.I):
            current["duration"] = line
            continue
        if re.search(r"\b(stack|technologies|tech|tools)\b", line, re.I):
            values = re.split(r"[:,]", line)[1:] if ":" in line else []
            if values:
                current["tech_stack"] = [item.strip() for item in values[0].split(",") if item.strip()]
            continue
        if line.lower().startswith(("designed", "built", "developed", "implemented", "created")):
            if current.get("summary"):
                current["achievements"].append(line)
            else:
                current["summary"] = line
            continue
        if current.get("summary"):
            current["achievements"].append(line)
        else:
            current["summary"] = line

        if current.get("company") and current.get("title") and current.get("summary"):
            entries.append(current)
            current = None

    if current and any(current.values()):
        entries.append(current)

    return entries


def _parse_projects_section(section_text: str) -> list[dict]:
    projects = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith(("project", "-", "•")):
            projects.append({"title": line.lstrip("-• "), "description": "", "tech_stack": [], "duration": "", "highlights": []})
    return projects


def _parse_skills_section(section_text: str) -> list[str]:
    skills = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for item in re.split(r"[,|/]+", line):
            token = item.strip()
            if token and len(token) <= 30:
                skills.append(token)
    return skills


def _parse_certifications_section(section_text: str) -> list[dict]:
    entries = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        entries.append({"name": line, "issuer": "", "date": ""})
    return entries


def _build_llm_prompt(resume_text: str) -> str:
    return """You are an expert resume parsing engine.
Your task is to extract structured candidate information from a resume.
Rules:
1. Return ONLY valid JSON.
2. Do NOT include markdown.
3. Do NOT include explanations.
4. Do NOT hallucinate.
5. If information is missing, return null or an empty array.
6. Preserve the exact wording wherever possible.
7. Do not infer missing dates or companies.
8. Extract EVERY internship, job, and work experience separately.
9. Extract EVERY education record separately.
10. Do not merge or deduplicate records.
11. Preserve the order they appear in the resume.
12. Extract skills as individual items without section titles or bullet prefixes.
13. Extract projects separately, preserving descriptions and technologies.
14. Extract certifications separately.
15. Normalize nothing (do not change casing, dates, or names).
16. Never guess or infer missing information.
17. If a value is uncertain, return null.
Extract the following schema:
{
  "full_name": "",
  "emails": [],
  "phones": [],
  "headline": "",
  "summary": "",
  "location": {
    "city": "",
    "region": "",
    "country": ""
  },
  "links": {
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "other": []
  },
  "education": [
    {
      "institution": "",
      "degree": "",
      "field": "",
      "start": "",
      "end": "",
      "cgpa": "",
      "location": ""
    }
  ],
  "experience": [
    {
      "company": "",
      "title": "",
      "location": "",
      "start": "",
      "end": "",
      "summary": "",
      "tech_stack": [],
      "achievements": []
    }
  ],
  "skills": [],
  "projects": [
    {
      "title": "",
      "description": "",
      "tech_stack": [],
      "duration": ""
    }
  ],
  "certifications": [
    {
      "name": "",
      "issuer": "",
      "date": ""
    }
  ]
}
If a field is unavailable, return null or [].
Return ONLY JSON.
Resume Text:""" + resume_text


def _get_llm_api_key(provider: str) -> str:
    if provider == "gemini":
        return (os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY") or "").strip()
    if provider == "openrouter":
        return (os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY") or "").strip()
    return (os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") or "").strip()


def _call_llm_resume_extractor(resume_text: str):
    if not resume_text or not resume_text.strip():
        print("  ⚠️  Empty resume text; skipping LLM extraction.")
        return None

    if requests is None:
        print("  ⚠️  requests is not installed; skipping LLM extraction.")
        return None

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower() or "openai"
    model = os.getenv("LLM_MODEL")
    prompt = _build_llm_prompt(resume_text[:20000])

    def _parse_payload(content: str):
        if not content:
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    for attempt in range(2):
        if provider == "gemini":
            api_key = _get_llm_api_key(provider)
            if not api_key:
                print("  ⚠️  GEMINI_API_KEY or LLM_API_KEY is not configured; skipping LLM extraction.")
                return None
            if not model:
                model = "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0}
            }
            headers = {"Content-Type": "application/json"}
            print(f"  ℹ️  Calling LLM provider: {provider} model: {model}")
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                parsed = _parse_payload(content)
                if parsed is not None:
                    return parsed
            except Exception as exc:
                print(f"  ⚠️  LLM extraction failed ({provider}): {exc}")
                return None
        elif provider == "openrouter":
            api_key = _get_llm_api_key(provider)
            if not api_key:
                print("  ⚠️  OPENROUTER_API_KEY or LLM_API_KEY is not configured; skipping LLM extraction.")
                return None
            if not model:
                model = "nvidia/nemotron-3-ultra-550b-a55b:free"
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "You are an expert resume parsing engine."},
                    {"role": "user", "content": prompt}
                ]
            }
            print(f"  ℹ️  Calling LLM provider: {provider} model: {model}")
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed = _parse_payload(content)
                if parsed is not None:
                    return parsed
            except Exception as exc:
                print(f"  ⚠️  LLM extraction failed ({provider}): {exc}")
                return None
        else:
            api_key = _get_llm_api_key(provider)
            if not api_key:
                print("  ⚠️  OPENAI_API_KEY or LLM_API_KEY is not configured; skipping LLM extraction.")
                return None
            if not model:
                model = "gpt-4o-mini"
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "You are an expert resume parsing engine."},
                    {"role": "user", "content": prompt}
                ]
            }
            print(f"  ℹ️  Calling LLM provider: {provider} model: {model}")
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                parsed = _parse_payload(content)
                if parsed is not None:
                    return parsed
            except Exception as exc:
                print(f"  ⚠️  LLM extraction failed ({provider}): {exc}")
                return None

        if attempt == 0:
            print("  ⚠️  LLM response was invalid JSON; retrying once.")

    return None


def _convert_llm_payload_to_raw(payload: dict) -> dict:
    raw = {
        "source": "resume_pdf",
        "candidate_id": None,
        "full_name": None,
        "email": None,
        "phone": None,
        "company": None,
        "title": None,
        "github_url": None,
        "linkedin_url": None,
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "location": None,
        "years_exp": None
    }

    if not isinstance(payload, dict):
        return raw

    full_name = payload.get("full_name")
    if full_name:
        raw["full_name"] = full_name

    emails = payload.get("emails") or []
    if isinstance(emails, list) and emails:
        raw["email"] = str(emails[0]).strip()

    phones = payload.get("phones") or []
    if isinstance(phones, list) and phones:
        raw["phone"] = str(phones[0]).strip()

    headline = payload.get("headline")
    if headline:
        raw["title"] = headline

    location = payload.get("location") or {}
    if isinstance(location, dict):
        parts = [str(location.get("city") or "").strip(), str(location.get("region") or "").strip(), str(location.get("country") or "").strip()]
        cleaned_parts = [part for part in parts if part]
        if cleaned_parts:
            raw["location"] = ", ".join(cleaned_parts)

    links = payload.get("links") or {}
    if isinstance(links, dict):
        if links.get("github"):
            raw["github_url"] = str(links.get("github")).strip()
        if links.get("linkedin"):
            raw["linkedin_url"] = str(links.get("linkedin")).strip()

    raw["skills"] = [str(skill).strip() for skill in (payload.get("skills") or []) if str(skill).strip()]

    education = payload.get("education") or []
    if isinstance(education, list):
        raw["education"] = []
        for entry in education:
            if not isinstance(entry, dict):
                continue
            raw["education"].append({
                "institution": entry.get("institution") or "",
                "degree": entry.get("degree") or "",
                "field": entry.get("field") or "",
                "start_year": entry.get("start") or "",
                "end_year": entry.get("end") or "",
                "cgpa": entry.get("cgpa") or "",
                "location": entry.get("location") or ""
            })

    experience = payload.get("experience") or []
    if isinstance(experience, list):
        raw["experience"] = []
        for entry in experience:
            if not isinstance(entry, dict):
                continue
            raw["experience"].append({
                "company": entry.get("company") or "",
                "title": entry.get("title") or "",
                "location": entry.get("location") or "",
                "start": entry.get("start") or "",
                "end": entry.get("end") or "",
                "duration": "",
                "tech_stack": [str(item).strip() for item in (entry.get("tech_stack") or []) if str(item).strip()],
                "summary": entry.get("summary") or "",
                "achievements": [str(item).strip() for item in (entry.get("achievements") or []) if str(item).strip()]
            })
        if raw["experience"]:
            first = raw["experience"][0]
            raw["company"] = first.get("company") or None
            raw["title"] = first.get("title") or None

    projects = payload.get("projects") or []
    if isinstance(projects, list):
        raw["projects"] = [project for project in projects if isinstance(project, dict)]

    certifications = payload.get("certifications") or []
    if isinstance(certifications, list):
        raw["certifications"] = [cert for cert in certifications if isinstance(cert, dict)]

    return raw


def extract_from_csv(path: str) -> list[dict]:
    """Extract raw records from recruiter CSV."""
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    "source":        "csv",
                    "candidate_id":  _clean_text(row.get("candidate_id")),
                    "full_name":     _clean_text(row.get("full_name")),
                    "email":         _clean_text(row.get("email")),
                    "phone":         _clean_text(row.get("phone")),
                    "company":       _clean_text(row.get("current_company")),
                    "title":         _clean_text(row.get("title")),
                    "github_url":    _clean_text(row.get("github_url")),
                    "linkedin_url":  _clean_text(row.get("linkedin_url")),
                    "skills":        [],
                    "education":     [],
                    "experience":    [],
                    "projects":      [],
                    "certifications": [],
                    "years_exp":     None
                })
    except Exception as e:
        print(f"  ⚠️  CSV extraction failed: {e}")
    return records


def extract_from_ats_json(path: str) -> list[dict]:
    """Extract raw records from ATS JSON blob."""
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            data = [data]

        for item in data:
            records.append({
                "source":       "ats_json",
                "candidate_id": _clean_text(item.get("candidate_id")),
                "full_name":    _clean_text(item.get("candidateName")),
                "email":        _clean_text(item.get("mail")),
                "phone":        _clean_text(item.get("mobile")),
                "company":      _clean_text(item.get("currentOrg")),
                "title":        _clean_text(item.get("designation")),
                "github_url":   "",
                "linkedin_url": "",
                "skills":       item.get("skillSet") or [],
                "education":    [
                    {
                        "institution": _clean_text(e.get("institute")) if isinstance(e, dict) else "",
                        "degree":      _clean_text(e.get("degree")) if isinstance(e, dict) else "",
                        "field":       "",
                        "end_year":    _clean_text(e.get("passYear")) if isinstance(e, dict) else ""
                    }
                    for e in (item.get("educationDetails") or [])
                ],
                "experience":   [],
                "projects":     [],
                "certifications": [],
                "years_exp": item.get("totalExp")
            })
    except Exception as e:
        print(f"  ⚠️  ATS JSON extraction failed: {e}")
    return records


def extract_from_resume_pdf(path: str) -> dict:
    """Extract structured fields from a resume PDF or text file."""
    raw = {
        "source":       "resume_pdf",
        "candidate_id": None,
        "full_name":    None,
        "email":        None,
        "phone":        None,
        "company":      None,
        "title":        None,
        "github_url":   None,
        "linkedin_url": None,
        "skills":       [],
        "education":    [],
        "experience":   [],
        "projects":     [],
        "certifications": [],
        "location":     None,
        "years_exp":    None
    }

    text = _read_resume_text(path)
    if not text:
        print(f"  ⚠️  PDF extraction failed: {path}")
        return raw

    try:
        import requests
    except ImportError:  # pragma: no cover - optional dependency
        requests = None

    if requests is not None:
        payload = _call_llm_resume_extractor(text)
        if payload is not None:
            try:
                return _convert_llm_payload_to_raw(payload)
            except Exception as exc:
                print(f"  ⚠️  LLM payload conversion failed: {exc}")

    _extract_contact_fields(text, raw)

    education_section = _parse_section(text, "Education")
    experience_section = _parse_section(text, "Experience")
    projects_section = _parse_section(text, "Projects")
    skills_section = _parse_section(text, "Skills")
    certifications_section = _parse_section(text, "Certifications")

    raw["education"] = _parse_education_section(education_section or text)
    raw["experience"] = _parse_experience_section(experience_section or text)
    raw["projects"] = _parse_projects_section(projects_section or text)
    raw["skills"] = _parse_skills_section(skills_section or text)
    raw["certifications"] = _parse_certifications_section(certifications_section or text)

    if not raw["skills"] and text:
        raw["skills"] = [token.strip() for token in re.split(r"[,|\n•·]+", text) if token.strip() and len(token.strip()) <= 30]

    if not raw["education"] and re.search(r"education", text, re.I):
        raw["education"] = [{"institution": "", "degree": "", "field": "", "start_year": "", "end_year": "", "cgpa": "", "location": ""}]

    return raw


def extract_from_linkedin(linkedin_url: str) -> dict:
    """Create a lightweight raw record from a LinkedIn URL input."""
    raw = {
        "source":       "linkedin",
        "candidate_id": None,
        "full_name":    None,
        "email":        None,
        "phone":        None,
        "company":      None,
        "title":        None,
        "github_url":   None,
        "linkedin_url": linkedin_url,
        "skills":       [],
        "education":    [],
        "experience":   [],
        "projects":     [],
        "certifications": [],
        "years_exp":    None
    }
    return raw


def extract_from_github(github_url: str) -> dict:
    """Fetch public GitHub profile via API."""
    raw = {
        "source":       "github",
        "full_name":    None,
        "email":        None,
        "headline":     None,
        "location":     None,
        "github_url":   github_url,
        "portfolio":    None,
        "skills":       [],
        "repos_count":  0
    }

    if not github_url:
        return raw

    try:
        import requests
        username = github_url.rstrip("/").split("/")[-1]
        if not username:
            return raw

        resp = requests.get(
            f"https://api.github.com/users/{username}",
            timeout=10
        )
        if resp.status_code != 200:
            print(f"  ⚠️  GitHub user '{username}' not found.")
            return raw

        data = resp.json()

        repos_resp = requests.get(
            f"https://api.github.com/users/{username}/repos?per_page=30",
            timeout=10
        )
        repos = repos_resp.json() if repos_resp.ok else []
        languages = list({
            r["language"] for r in repos
            if r.get("language")
        })

        raw.update({
            "full_name":   data.get("name", ""),
            "email":       data.get("email"),
            "headline":    data.get("bio", ""),
            "location":    data.get("location", ""),
            "portfolio":   data.get("blog", ""),
            "skills":      languages,
            "repos_count": data.get("public_repos", 0)
        })

    except Exception as e:
        print(f"  ⚠️  GitHub fetch failed: {e}")

    return raw