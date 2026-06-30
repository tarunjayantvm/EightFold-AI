from .path_resolver import resolve
from .normalizer import normalize_value


def _set_nested_value(output: dict, path: str, value):
    keys = path.split('.') if isinstance(path, str) else [path]
    current = output
    for key in keys[:-1]:
        if not isinstance(current.get(key), dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def project_candidate(canonical: dict, config: dict) -> dict:
    output = {}
    on_missing = config.get('on_missing', 'null')

    for field in config.get('fields', []):
        dest = field['path']
        source_path = field.get('from', field['path'])
        required = field.get('required', False)
        normalize = field.get('normalize')

        value = resolve(canonical, source_path)
        if normalize and value is not None:
            value = normalize_value(value, normalize)

        if value is None or value == [] or value == '':
            if required and on_missing == 'error':
                raise ValueError(f"Missing required field {dest}")
            if on_missing == 'omit':
                continue
            value = None

        _set_nested_value(output, dest, value)

    if config.get('include_confidence', False):
        output['overall_confidence'] = canonical.get('overall_confidence')
    if config.get('include_provenance', False):
        output['provenance'] = canonical.get('provenance')

    return output
