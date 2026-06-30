import sys
sys.path.append(".")

from agents.agent_02_extraction import extract_from_resume_pdf
from pipeline import _build_group_key, _group_records


def test_resume_parser_extracts_location_and_skills():
    raw = extract_from_resume_pdf("data/resumes/sde resume.pdf")

    assert raw["full_name"] == "Tarun Jayant V M"
    assert raw["email"].endswith("@srec.ac.in")
    assert raw["phone"] == "+91-6385582585"
    assert "Coimbatore" in raw["location"]
    assert "Java" in raw["skills"]
    assert "Python" in raw["skills"]
    assert "Spring Boot" in raw["skills"]


def test_group_key_merges_resume_with_csv_candidate():
    csv_record = {
        "candidate_id": "C001",
        "full_name": "Tarun Jayant V M",
        "email": "tarunjayant.2301250@srec.ac.in",
        "phone": "+91-6385582585"
    }
    resume_record = {
        "full_name": "Tarun Jayant V M",
        "email": "tarunjayant.2301250@srec.ac.in",
        "phone": "+91-6385582585"
    }

    assert _build_group_key(csv_record).startswith("id:")
    assert _build_group_key(resume_record).startswith("email:")


def test_linkedin_url_enriches_existing_candidate():
    existing = {
        "candidate_id": "C001",
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "linkedin_url": "https://www.linkedin.com/in/janedoe/"
    }
    linkedin_only = {
        "source": "linkedin",
        "candidate_id": None,
        "full_name": None,
        "email": None,
        "phone": None,
        "linkedin_url": "https://linkedin.com/in/janedoe"
    }

    groups = _group_records([existing, linkedin_only])

    assert len(groups) == 1
    assert groups[0][0]["candidate_id"] == "C001"
