from agents.agent_04_normalization import normalize_phone, normalize_skill


def normalize_value(value, method: str):
    if method == 'E164':
        if isinstance(value, list):
            return [normalize_phone(v) for v in value]
        return normalize_phone(value)
    if method == 'canonical':
        if isinstance(value, list):
            return [normalize_skill(v) for v in value]
        return normalize_skill(value)
    return value
