def _validate_type(value, expected: str) -> bool:
    if expected == 'string':
        return isinstance(value, str)
    if expected == 'string[]':
        return isinstance(value, list) and all(isinstance(item, str) for item in value)
    if expected == 'number':
        return isinstance(value, (int, float))
    if expected == 'object':
        return isinstance(value, dict)
    if expected == 'object[]':
        return isinstance(value, list) and all(isinstance(item, dict) for item in value)
    return False


def _get_nested_value(output: dict, path: str):
    if not path:
        return None
    current = output
    for part in path.split('.'):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate_output(output: dict, config: dict) -> list[str]:
    errors = []
    fields = config.get('fields', [])
    on_missing = config.get('on_missing', 'null')

    for field in fields:
        path = field['path']
        expected_type = field.get('type')
        required = field.get('required', False)

        value = _get_nested_value(output, path)
        if value is None:
            if required and on_missing == 'error':
                errors.append(f"Missing required field {path}")
            continue

        if expected_type and not _validate_type(value, expected_type):
            errors.append(f"Field {path} expected {expected_type}, got {type(value).__name__}")

    return errors
