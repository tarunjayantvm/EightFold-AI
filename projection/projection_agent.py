import logging

from .config_loader import load_config, validate_config
from .projection_engine import project_candidate
from .validator import validate_output

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def project(canonical: dict, config: dict = None, config_path: str | None = None) -> dict:
    if config is None:
        if not config_path:
            raise ValueError('Projection requires either config or config_path.')
        logger.info('Loading projection config from %s', config_path)
        config = load_config(config_path)
    else:
        logger.info('Using in-memory projection config')

    validate_config(config)
    projected = project_candidate(canonical, config)
    errors = validate_output(projected, config)
    if errors:
        logger.error('Projection validation errors: %s', errors)
        raise ValueError('Projection validation failed: ' + '; '.join(errors))
    return projected
