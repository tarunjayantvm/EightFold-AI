import os
import json

SUPPORTED_TYPES = {
    ".csv":  "csv",
    ".json": "ats_json",
    ".pdf":  "resume_pdf",
    ".txt":  "recruiter_notes"
}


def _is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

def detect_sources(input_paths: list[str]) -> list[dict]:
    """
    Agent 1 — Source Detection Agent
    Identifies the type of every input source.
    Returns list of {path, source_type, valid} dicts.
    """
    detected = []

    for path in input_paths:
        if not path:
            continue

        result = {
            "path":        path,
            "source_type": None,
            "valid":       False,
            "error":       None
        }

        if _is_url(path):
            if "github.com" in path:
                result["source_type"] = "github"
            elif "linkedin.com" in path:
                result["source_type"] = "linkedin"
            else:
                result["error"] = f"Unsupported URL: {path}"
                detected.append(result)
                continue

            result["valid"] = True
            detected.append(result)
            continue

        # Check file exists
        if not os.path.exists(path):
            result["error"] = f"File not found: {path}"
            detected.append(result)
            continue

        # Detect by extension
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_TYPES:
            result["error"] = f"Unsupported format: {ext}"
            detected.append(result)
            continue

        # Validate JSON is actually valid JSON
        if ext == ".json":
            try:
                with open(path, "r") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                result["error"] = f"Invalid JSON: {e}"
                detected.append(result)
                continue

        result["source_type"] = SUPPORTED_TYPES[ext]
        result["valid"]       = True
        detected.append(result)

    return detected