from coldfront.config.env import ENV
from coldfront.config.base import INSTALLED_APPS
from coldfront.config.core import ALLOCATION_FUNCS_ON_EXPIRE

from django.core.exceptions import ImproperlyConfigured

if "coldfront_plugin_ldap_allocs" not in INSTALLED_APPS:
    INSTALLED_APPS += ["coldfront_plugin_ldap_allocs"]

try:
    import ldap
except ImportError:
    raise ImproperlyConfigured("LDAP import failed. Please run: pip install ldap3")

# -----------------------------------------------------------------------------
#  This plugins synchronizes allocations with LDAP poxisGroups.
# -----------------------------------------------------------------------------

LDAP_ALLOCS_SERVER_URI = ENV.str("LDAP_ALLOCS_SERVER_URI")
LDAP_ALLOCS_BASE = ENV.str("LDAP_ALLOCS_BASE")
LDAP_ALLOCS_BIND_DN = ENV.str("LDAP_ALLOCS_BIND_DN", default="")
LDAP_ALLOCS_BIND_PASSWORD = ENV.str("LDAP_ALLOCS_BIND_PASSWORD", default="")
LDAP_ALLOCS_CONNECT_TIMEOUT = ENV.str("LDAP_ALLOCS_CONNECT_TIMEOUT", default=2.5)
LDAP_ALLOCS_USE_SSL = ENV.str("LDAP_ALLOCS_USE_SSL", default=True)
LDAP_ALLOCS_USE_TLS = ENV.str("LDAP_ALLOCS_USE_TLS", default=False)
LDAP_ALLOCS_PRIV_KEY_FILE = ENV.str("LDAP_ALLOCS_PRIV_KEY_FILE", default="")
LDAP_ALLOCS_CERT_FILE = ENV.str("LDAP_ALLOCS_CERT_FILE", default="")
LDAP_ALLOCS_CACERT_FILE = ENV.str("LDAP_ALLOCS_CACERT_FILE", default="")
LDAP_ALLOCS_GID_MIN = ENV.str("LDAP_ALLOCS_GID_MIN", default=65565)
LDAP_ALLOCS_GID_MIN = ENV.str("LDAP_ALLOCS_GID_MIN", default=2**32 - 1)
LDAP_ALLOCS_PREFIX = ENV.str("LDAP_ALLOCS_PREFIX", default="")
ALLOCATION_FUNCS_ON_EXPIRE += [
    "coldfront_plugin_ldap_allocs.utils.remove_from_allocation",
]
