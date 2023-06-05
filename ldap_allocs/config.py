from coldfront.config.base import INSTALLED_APPS
from coldfront.config.env import ENV
from django.core.exceptions import ImproperlyConfigured

if "coldfront_plugins_ldap_allocs" not in INSTALLED_APPS:
    INSTALLED_APPS += ["coldfront_plugins_ldap_allocs"]

try:
    import ldap
except ImportError:
    raise ImproperlyConfigured("Please run: pip install ldap3")

# -----------------------------------------------------------------------------
#  This modifies LDAP groups based on allocations.
# -----------------------------------------------------------------------------

LDAP_ALLOCS_SERVER_URI = ENV.str("LDAP_ALLOCS_SERVER_URI")
LDAP_ALLOCS_BASE = ENV.str("LDAP_ALLOCS_BASE")
LDAP_ALLOCS_BIND_DN = ENV.str("LDAP_ALLOCS_BIND_DN", default="")
LDAP_ALLOCS_BIND_PASSWORD = ENV.str("LDAP_ALLOCS_BIND_PASSWORD", default="")
LDAP_ALLOCS_CONNECT_TIMEOUT = ENV.float("LDAP_ALLOCS_CONNECT_TIMEOUT",
                                        default=2.5)
LDAP_ALLOCS_USE_SSL = ENV.bool("LDAP_ALLOCS_USE_SSL", default=True)
LDAP_ALLOCS_USE_TLS = ENV.bool("LDAP_ALLOCS_USE_TLS", default=False)
LDAP_ALLOCS_PRIV_KEY_FILE = ENV.str("LDAP_ALLOCS_PRIV_KEY_FILE", default="")
LDAP_ALLOCS_CERT_FILE = ENV.str("LDAP_ALLOCS_CERT_FILE", default="")
LDAP_ALLOCS_CACERT_FILE = ENV.str("LDAP_ALLOCS_CACERT_FILE", default="")
