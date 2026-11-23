"""Compatibility namespace for installations made before the FREE-HANDS rename.

New code should import :mod:`free_hands`. Keeping these aliases lets existing
local plugins and tests continue to work while users migrate.
"""

import free_hands as _free_hands

# Let Python resolve old submodule imports from the new package without
# eagerly importing optional runtime dependencies such as websocket-client.
__path__ = _free_hands.__path__
__version__ = _free_hands.__version__
