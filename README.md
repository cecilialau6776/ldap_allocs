# ldap_allocs - LDAP Allocations

A [ColdFront](https://coldfront.readthedocs.io/en/latest/) plugin that creates and updates LDAP `posixGroup`s based on a project's allocations.

## Installation
If you're using a virtual environment (following ColdFront's deployment instructions should have you make and use a virtual environment), make sure you're in the virutal environment first.

`pip install git+https://github.com/cecilialau6776/ldap_allocs`

## Configuration
To enable this plugin, set the following environment variables:
```env
PLUGIN_LDAP_ALLOCS=True
LDAP_ALLOCS_SERVER_URI=ldap://example.com
LDAP_ALLOCS_BASE="ou=Groups,dc=example,dc=com"
```

Also, set following environment variables as applicable for your LDAP server:

| Option | Default | Description |
| --- | --- | --- |
| `LDAP_ALLOCS_SERVER_URI` | N/A | URI for the LDAP server, required |
| `LDAP_ALLOCS_BASE` | N/A | Search base, required |
| `LDAP_ALLOCS_BIND_DN` | `""` | Bind DN |
| `LDAP_ALLOCS_BIND_PASSWORD` | `""` | Bind Password |
| `LDAP_ALLOCS_CONNECT_TIMEOUT` | `2.5` | Time in seconds before the connection times out |
| `LDAP_ALLOCS_USE_SSL` | `True` | Whether or not to use SSL |
| `LDAP_ALLOCS_USE_TLS` | `False` | Whether or not to use TLS |
| `LDAP_ALLOCS_PRIV_KEY_FILE` | `""` | Path to the private key file |
| `LDAP_ALLOCS_CERT_FILE` | `""` | Path to the certificate file |
| `LDAP_ALLOCS_CACERT_FILE` | `""` | Path to the CA certificate file |
| `LDAP_ALLOCS_GID_MIN` | `65565` | Lower gid range for LDAP `posixGroup`s, inclusive |
| `LDAP_ALLOCS_GID_MIN` | `4294967295` | Upper gid range for LDAP `posixGroup`s, inclusive |
| `LDAP_ALLOCS_PREFIX` | `""` | A string added to the beginning of LDAP group names. For example, if the prefix is `"cf-"` and the resource's `ldap-group-name` is `"storage"`, the `cn` might look something like `cn=cf-storage-project_name-42` |

This plugin also provides a `remove_from_allocation()` function that will remove users from an allocation. By default, this is put in ColdFront's `ALLOCATION_FUNCS_ON_EXPIRE` to remove users from the LDAP group when it expires, but you can disable this by putting the following in ColdFront's [local settings](https://coldfront.readthedocs.io/en/latest/config/#configuration-files):

```py
ALLOCATION_FUNCS_ON_EXPIRE.remove("coldfront_plugin_ldap_allocs.utils.remove_from_allocation")
```

All of the above options can also be set in ColdFront's local settings with the same name.

### Examples

Here are a couple of example configurations:

```env
# /etc/coldfront/coldfront.env
LDAP_ALLOCS_SERVER_URI=ldaps://tls.example.com
LDAP_ALLOCS_BASE="dc=tls,dc=example,dc=com"
LDAP_ALLOCS_USE_SSL=True
LDAP_ALLOCS_USE_TLS=True
LDAP_ALLOCS_CACERT_FILE=/path/to/cacert
LDAP_ALLOCS_CERT_FILE=/path/to/cert
LDAP_ALLOCS_PRIV_KEY_FILE=/path/to/key
```

```py
# /etc/coldfront/local_settings.py
INSTALLED_APPS += ["coldfront_plugin_ldap_allocs"]
LDAP_ALLOCS_SERVER_URI = "ldap://example.com"
LDAP_ALLOCS_BASE = "dc=example,dc=com"
LDAP_ALLOCS_BIND_DN = "cn=Manager,dc=example,dc=com"
LDAP_ALLOCS_BIND_PASSWORD = "secret"
LDAP_ALLOCS_USE_SSL = True
```
