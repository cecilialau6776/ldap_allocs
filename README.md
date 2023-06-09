# ldap_allocs - LDAP Allocations

A [ColdFront](https://coldfront.readthedocs.io/en/latest/) plugin that creates and updates LDAP groups based on a projects allocations.

## Installation
If you're using a virtual environment (following ColdFront's deployment instructions should have you make and use a virtual environment), make sure you're in the virutal environment first.

`pip install git+https://github.com/cecilialau6776/ldap_allocs`

## Configuration
Add the following to ColdFront's [local settings](https://coldfront.readthedocs.io/en/latest/config/#configuration-files):

```
INSTALLED_APPS += ["coldfront_plugin_ldap_allocs"]
```

Additionally, set the following options as applicable for your LDAP server:

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

This plugin also provides a `remove_from_allocation` function that will remove users from an allocation. This can be in ColdFront's `ALLOCATION_FUNCS_ON_EXPIRE` setting.

`ALLOCATION_FUNCS_ON_EXPIRE += ['coldfront_plugin_ldap_allocs.utils.remove_from_allocation',]`

Here are a couple of example configurations:

```
ALLOCATION_FUNCS_ON_EXPIRE += ['coldfront_plugin_ldap_allocs.utils.remove_from_allocation',]
LDAP_ALLOCS_SERVER_URI=ldaps://tls.example.com
LDAP_ALLOCS_BASE="dc=tls,dc=example,dc=com"
LDAP_ALLOCS_USE_SSL=True
LDAP_ALLOCS_USE_TLS=True
LDAP_ALLOCS_CACERT_FILE=/path/to/cacert
LDAP_ALLOCS_CERT_FILE=/path/to/cert
LDAP_ALLOCS_PRIV_KEY_FILE=/path/to/key
```

```
LDAP_ALLOCS_SERVER_URI=ldap://example.com
LDAP_ALLOCS_BASE="dc=example,dc=com"
LDAP_ALLOCS_BIND_DN="cn=Manager,dc=example,dc=com"
LDAP_ALLOCS_BIND_PASSWORD="secret"
LDAP_ALLOCS_USE_SSL=True
```
