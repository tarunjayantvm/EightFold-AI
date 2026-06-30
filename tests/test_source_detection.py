import sys
sys.path.append(".")

from agents.agent_01_source_detection import detect_sources


def test_detects_github_and_linkedin_urls():
    detected = detect_sources([
        "https://github.com/octocat",
        "https://www.linkedin.com/in/example-user"
    ])

    assert len(detected) == 2
    assert detected[0]["valid"] is True
    assert detected[0]["source_type"] == "github"
    assert detected[1]["valid"] is True
    assert detected[1]["source_type"] == "linkedin"
