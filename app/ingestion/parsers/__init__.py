"""
Auto-import all modules in this package so their @register decorators run and
populate REGISTRY. Any ImportError is logged and ignored (plugin style).
"""

import importlib
import pkgutil
import logging
from .base import register, BaseParser, get_parse_registry

log = logging.getLogger(__name__)

# Dynamically import all submodules to trigger registration
for m in pkgutil.iter_modules(__path__):
    try:
        importlib.import_module(f"{__name__}.{m.name}")
    except Exception as e:  # pragma: no cover
        log.warning("Parser %s failed to import: %s", m.name, e)

# Import after dynamic imports to ensure all parsers are registered


__all__ = ["register", "BaseParser", "get_parse_registry"]
