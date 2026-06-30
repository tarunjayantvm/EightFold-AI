import sys
from types import SimpleNamespace
sys.path.append('.')

import agents.agent_02_extraction as extraction
from agents.agent_02_extraction import extract_from_resume_pdf
from agents.agent_04_normalization import normalize
from agents.agent_05_merge_dedup import merge_records
from agents.agent_07_confidence_scoring import score_confidence
from agents.agent_08_provenance import build_provenance


def test_resume_parser_extracts_structured_education_and_experience():
    raw = extract_from_resume_pdf('data/resumes/sde resume.pdf')

    assert raw['education']
    assert isinstance(raw['education'][0], dict)
    assert 'institution' in raw['education'][0]
    assert 'degree' in raw['education'][0]
    assert 'field' in raw['education'][0]

    assert raw['experience']
    assert isinstance(raw['experience'][0], dict)
    assert 'company' in raw['experience'][0]
    assert 'tech_stack' in raw['experience'][0]
    assert 'summary' in raw['experience'][0]


def test_merge_deduplicates_education_and_experience():
    rec_a = {
        'source': 'resume_pdf',
        'education': [{'institution': 'Sri Ramakrishna Engineering College', 'degree': 'B.E.', 'field': 'Computer Science', 'end_year': '2027'}],
        'experience': [{'company': 'Infosys', 'title': 'Intern', 'tech_stack': ['Python']}],
        'skills': ['Python', 'PyTorch']
    }
    rec_b = {
        'source': 'ats_json',
        'education': [{'institution': 'Sri Ramakrishna Engineering College, Coimbatore', 'degree': 'B.E.', 'field': 'Computer Science and Engineering', 'end_year': '2027'}],
        'experience': [{'company': 'Infosys', 'title': 'Intern', 'tech_stack': ['Python']}],
        'skills': ['Python', 'React']
    }

    merged = merge_records([normalize(rec_a), normalize(rec_b)])

    assert len(merged['education']) == 1
    assert len(merged['experience']) == 1
    assert len(merged['skills']) == 3


def test_experience_duration_and_years_are_derived():
    rec = {
        'source': 'resume_pdf',
        'experience': [
            {'company': 'Acme', 'title': 'Engineer', 'start': '2020-01', 'end': '2021-01'},
            {'company': 'Beta', 'title': 'Engineer', 'start': '2021-02', 'end': '2023-02'}
        ]
    }

    merged = merge_records([normalize(rec)])

    assert merged['years_experience'] == 3.0
    assert merged['experience'][0]['duration'] == '1 years'
    assert merged['experience'][1]['duration'] == '2 years'


def test_llm_extraction_retries_once_on_invalid_json(monkeypatch):
    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload
        def raise_for_status(self):
            return None
        def json(self):
            return self._payload

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(json)
        if len(calls) == 1:
            return DummyResponse({"choices": [{"message": {"content": "{not valid json"}}]})
        return DummyResponse({"choices": [{"message": {"content": '{"full_name": "Ada Lovelace", "emails": ["ada@example.com"], "phones": [], "headline": "Engineer", "summary": "", "location": {"city": "London", "region": "", "country": "UK"}, "links": {"linkedin": "", "github": "", "portfolio": "", "other": []}, "education": [], "experience": [], "skills": ["Python"], "projects": [], "certifications": []}'}}]})

    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setattr(extraction, 'requests', SimpleNamespace(post=fake_post))

    result = extraction._call_llm_resume_extractor('resume text')

    assert result['full_name'] == 'Ada Lovelace'
    assert result['skills'] == ['Python']
    assert len(calls) == 2


def test_confidence_and_provenance_are_calculated():
    merged = {
        'full_name': 'Tarun',
        'emails': ['tarun@example.com'],
        'phones': ['+919876543210'],
        'headline': 'Engineer',
        'location': {'city': 'Coimbatore', 'country': 'IN'},
        'links': {'linkedin': 'https://linkedin.com/in/test', 'github': 'https://github.com/test'},
        'skills': ['Python'],
        'experience': [{'company': 'Infosys', 'title': 'Intern'}],
        'education': [{'institution': 'SREC', 'degree': 'B.E.'}],
        '_sources': ['csv', 'resume_pdf']
    }
    records = [
        {'source': 'csv', 'full_name': 'Tarun', 'emails': ['tarun@example.com'], 'phones': ['+919876543210'], 'headline': 'Engineer', 'skills': ['Python'], 'experience': [{'company': 'Infosys', 'title': 'Intern'}], 'education': [{'institution': 'SREC', 'degree': 'B.E.'}], 'location': {'city': 'Coimbatore', 'country': 'IN'}, 'links': {'linkedin': 'https://linkedin.com/in/test'}},
        {'source': 'resume_pdf', 'full_name': 'Tarun', 'emails': ['tarun@example.com'], 'phones': ['+919876543210'], 'headline': 'Engineer', 'skills': ['Python'], 'experience': [{'company': 'Infosys', 'title': 'Intern'}], 'education': [{'institution': 'SREC', 'degree': 'B.E.'}], 'location': {'city': 'Coimbatore', 'country': 'IN'}, 'links': {'github': 'https://github.com/test'}}
    ]

    scored = score_confidence(merged, records)
    assert scored['overall_confidence'] >= 0.0
    assert scored['overall_confidence'] <= 1.0

    with_provenance = build_provenance(scored, records)
    assert with_provenance['provenance']
