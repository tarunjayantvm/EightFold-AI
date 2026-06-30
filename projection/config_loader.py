import json


def load_config(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as handle:
        config = json.load(handle)
    return config

def validate_config(config: dict) -> None:
    if not isinstance(config, dict):
        raise ValueError('Projection config must be a JSON object.')

    if 'fields' not in config or not isinstance(config['fields'], list):
        raise ValueError('Projection config must include a fields array.')

    for field in config['fields']:
        if not isinstance(field, dict):
            raise ValueError('Each field definition must be an object.')
        if 'path' not in field or not isinstance(field['path'], str):
            raise ValueError('Each field definition requires a string path.')
        if 'type' in field and field['type'] not in ['string', 'string[]', 'number', 'object', 'object[]']:
            raise ValueError(f"Unsupported field type: {field['type']}")

    if 'include_confidence' not in config or not isinstance(config['include_confidence'], bool):
        raise ValueError('Projection config must include include_confidence as a boolean.')

    if 'include_provenance' not in config or not isinstance(config['include_provenance'], bool):
        raise ValueError('Projection config must include include_provenance as a boolean.')

    if config.get('on_missing') not in ['null', 'omit', 'error']:
        raise ValueError('Projection config on_missing must be one of: null, omit, error.')
