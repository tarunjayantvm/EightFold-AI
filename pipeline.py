import json
import os

from agents.agent_01_source_detection  import detect_sources
from agents.agent_02_extraction        import (
    extract_from_csv, extract_from_ats_json,
    extract_from_resume_pdf, extract_from_github,
    extract_from_linkedin
)
from agents.agent_03_canonical_mapping import map_to_canonical
from agents.agent_04_normalization     import normalize
from agents.agent_05_entity_resolution import resolve_entities
from agents.agent_05_merge_dedup       import merge_records
from agents.agent_06_conflict_resolution import resolve_conflicts
from agents.agent_07_confidence_scoring  import score_confidence
from agents.agent_08_provenance          import build_provenance
from agents.agent_09_config_projection   import project
from agents.agent_10_validation          import validate


def _normalize_identity(value) -> str:
    return str(value or "").strip().lower()


def _normalize_linkedin_url(value) -> str:
    url = _normalize_identity(value)
    if not url:
        return ""
    if url.startswith("https://"):
        url = url[len("https://"):]
    elif url.startswith("http://"):
        url = url[len("http://"):]
    if url.startswith("www."):
        url = url[len("www."):]
    if url.endswith("/"):
        url = url[:-1]
    return url


def _build_group_key(record: dict) -> str:
    candidate_id = _normalize_identity(record.get("candidate_id"))
    if candidate_id:
        return f"id:{candidate_id}"

    email = _normalize_identity(record.get("email"))
    phone = _normalize_identity(record.get("phone"))
    name = _normalize_identity(record.get("full_name"))
    linkedin = _normalize_linkedin_url(record.get("linkedin_url"))

    if email:
        return f"email:{email}"
    if phone:
        return f"phone:{phone}"
    if name:
        return f"name:{name}"
    if linkedin:
        return f"linkedin:{linkedin}"
    return "unknown"


def _same_candidate(left: dict, right: dict) -> bool:
    left_id = _normalize_identity(left.get("candidate_id"))
    right_id = _normalize_identity(right.get("candidate_id"))
    if left_id and right_id and left_id == right_id:
        return True

    for field in ["email", "phone", "full_name"]:
        left_value = _normalize_identity(left.get(field))
        right_value = _normalize_identity(right.get(field))
        if left_value and right_value and left_value == right_value:
            return True

    left_linkedin = _normalize_linkedin_url(left.get("linkedin_url"))
    right_linkedin = _normalize_linkedin_url(right.get("linkedin_url"))
    if left_linkedin and right_linkedin and left_linkedin == right_linkedin:
        return True

    return False


def _group_records(records: list[dict]) -> list[list[dict]]:
    grouped = []
    for record in records:
        matched_idx = None
        for idx, group in enumerate(grouped):
            if _same_candidate(record, group[0]):
                matched_idx = idx
                break
        if matched_idx is None:
            grouped.append([record])
        else:
            grouped[matched_idx].append(record)
    return grouped


def run_pipeline(
    input_paths: list[str],
    config_path: str | None = None,
    output_path: str  = "output/output.json"
):
    print("\n" + "="*55)
    print("  Multi-Source Candidate Data Transformer")
    print("  Eightfold AI Assignment")
    print("="*55 + "\n")

    config = None
    if config_path:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"✅ Config loaded       : {config_path}")
    else:
        print("ℹ️  No projection config provided; running canonical output only.")

    # ── Agent 1: Detect sources ───────────
    detected = detect_sources(input_paths)
    valid    = [d for d in detected if d["valid"]]
    invalid  = [d for d in detected if not d["valid"]]

    print(f"✅ Sources detected    : {len(valid)} valid, {len(invalid)} invalid")
    for inv in invalid:
        print(f"   ⚠️  {inv['path']}: {inv['error']}")

    # ── Agent 2: Extract all records ──────
    all_raw = []
    for source in valid:
        stype = source["source_type"]
        path  = source["path"]
        print(f"   📂 Extracting [{stype}]: {path}")

        if stype == "csv":
            all_raw.extend(extract_from_csv(path))
        elif stype == "ats_json":
            all_raw.extend(extract_from_ats_json(path))
        elif stype == "resume_pdf":
            all_raw.append(extract_from_resume_pdf(path))
        elif stype == "github":
            all_raw.append(extract_from_github(path))
        elif stype == "linkedin":
            all_raw.append(extract_from_linkedin(path))

    print(f"✅ Records extracted   : {len(all_raw)}")

    # ── Group records that refer to the same candidate ─────────────
    groups = _group_records(all_raw)

    print(f"✅ Candidates found    : {len(groups)}")
    print()

    output_profiles = []

    for group in groups:
        recs = group
        cid = recs[0].get("candidate_id") or _build_group_key(recs[0])
        name = recs[0].get("full_name", "Unknown")
        print(f"─── Processing: {name} ({cid}) ───")

        # Fetch GitHub if available
        github_url = next(
            (r.get("github_url") for r in recs if r.get("github_url")), None
        )
        if github_url:
            print(f"   🌐 Fetching GitHub : {github_url}")
            github_raw = extract_from_github(github_url)
            if github_raw.get("full_name"):
                recs.append(github_raw)

        # ── Agent 3: Canonical mapping ────
        canonical_recs = [map_to_canonical(r) for r in recs]

        # ── Agent 4: Normalize ────────────
        canonical_recs = [normalize(c) for c in canonical_recs]

        # ── Agent 5a: Entity resolution ───
        canonical_recs = resolve_entities(canonical_recs)

        # ── Agent 5b: Merge & dedup ────────
        merged = merge_records(canonical_recs)
        merged["candidate_id"] = cid

        # ── Agent 6: Conflict resolution ──
        merged = resolve_conflicts(merged, canonical_recs)

        # ── Agent 7: Confidence scoring ───
        merged = score_confidence(merged, canonical_recs)

        # ── Agent 8: Provenance ───────────
        merged = build_provenance(merged, canonical_recs)

        # ── Agent 9: Config projection ────
        if config is not None:
            projected = project(merged, config)
        else:
            projected = merged

        # ── Agent 10: Validation ──────────
        projected = validate(projected)

        val = projected["_validation"]
        status = "✅" if val["passed"] else "❌"
        print(f"   {status} Confidence: {merged['overall_confidence']} | "
              f"Errors: {len(val['errors'])} | "
              f"Warnings: {len(val['warnings'])}")

        output_profiles.append(projected)

    # Save output
    os.makedirs("output", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_profiles, f, indent=2)

    print(f"\n✅ Output saved        : {output_path}")
    print(f"✅ Total profiles      : {len(output_profiles)}")
    print("="*55 + "\n")
    return output_profiles


if __name__ == "__main__":
    run_pipeline(
        input_paths = [
            "data/candidates.csv",
            "data/ats_export.json"
        ],
        config_path = "config/default_config.json",
        output_path = "output/output.json"
    )