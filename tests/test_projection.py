from agents.agent_09_config_projection import project


def test_projection_with_default_config():
    canonical = {
        'candidate_id': '123',
        'full_name': 'Test Candidate',
        'emails': ['test@example.com'],
        'phones': ['9876543210'],
        'headline': 'Engineer',
        'location': {'city': 'Test City', 'country': 'US'},
        'links': {'linkedin': 'https://linkedin.com/in/test'},
        'skills': ['Python', 'react'],
        'experience': [{'company': 'Acme', 'title': 'Engineer', 'start': '2020-01', 'end': '2021-01'}],
        'education': [{'institution': 'Test University', 'degree': 'B.S.'}],
        'overall_confidence': 0.85,
        'provenance': ['csv']
    }

    config = {
        'fields': [
            {'path': 'candidate_id', 'type': 'string'},
            {'path': 'full_name', 'type': 'string', 'required': True},
            {'path': 'primary_email', 'from': 'emails[0]', 'type': 'string'},
            {'path': 'phone', 'from': 'phones[0]', 'type': 'string', 'normalize': 'E164'},
            {'path': 'profile.linkedin', 'from': 'links.linkedin', 'type': 'string'},
        ],
        'include_confidence': True,
        'include_provenance': True,
        'on_missing': 'null'
    }

    projected = project(canonical, config)

    assert projected['candidate_id'] == '123'
    assert projected['full_name'] == 'Test Candidate'
    assert projected['primary_email'] == 'test@example.com'
    assert projected['phone'] == '+919876543210'
    assert projected['profile']['linkedin'] == 'https://linkedin.com/in/test'
    assert projected['overall_confidence'] == 0.85
    assert projected['provenance'] == ['csv']


def test_projection_omits_missing_optional_fields_by_default():
    canonical = {
        'full_name': 'Test Candidate',
        'emails': ['test@example.com'],
        'overall_confidence': 0.9,
        'provenance': ['csv']
    }
    config = {
        'fields': [
            {'path': 'full_name', 'type': 'string', 'required': True},
            {'path': 'primary_email', 'from': 'emails[0]', 'type': 'string'},
            {'path': 'phone', 'from': 'phones[0]', 'type': 'string'}
        ],
        'include_confidence': True,
        'include_provenance': True,
        'on_missing': 'omit'
    }

    projected = project(canonical, config)
    assert projected['full_name'] == 'Test Candidate'
    assert projected['primary_email'] == 'test@example.com'
    assert 'phone' not in projected
    assert projected['overall_confidence'] == 0.9


def test_projection_config_validation_error():
    canonical = {'full_name': 'Test Candidate'}
    config = {
        'fields': [
            {'path': 'full_name', 'type': 'string', 'required': True},
            {'path': 'missing_field', 'type': 'string', 'required': True}
        ],
        'include_confidence': False,
        'include_provenance': False,
        'on_missing': 'error'
    }

    try:
        project(canonical, config)
        assert False, 'Expected ValueError for missing required field'
    except ValueError as exc:
        assert 'Missing required field missing_field' in str(exc)
