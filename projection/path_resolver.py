import re


def _parse_path(path: str) -> list:
    tokens = []
    pattern = re.compile(r"([^.\[\]]+)(\[(?:\*|\d+)\])?")
    for match in pattern.finditer(path):
        key = match.group(1)
        index = match.group(2)
        tokens.append((key, index))
    return tokens


def resolve(data, path: str):
    if not path:
        return None
    current = data
    for key, index in _parse_path(path):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
        if index is None:
            continue
        if not isinstance(current, list):
            return None
        if index == '[*]':
            next_path = path[path.index(key + index) + len(key + index) + 1:]
            if not next_path:
                return current
            return [resolve(item, next_path) for item in current if resolve(item, next_path) is not None]
        idx = int(index.strip('[]'))
        if idx < 0 or idx >= len(current):
            return None
        current = current[idx]
    return current
