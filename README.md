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
| `LDAP_ALLOCS_GID_MIN` | `65565` | Lower gid range for LDAP `posixGroup`s, inclusive |
| `LDAP_ALLOCS_GID_MAX` | `4294967295` | Upper gid range for LDAP `posixGroup`s, inclusive |
| `LDAP_ALLOCS_PREFIX` | `""` | A string added to the beginning of LDAP group names. For example, if the prefix is `"cf-"` and the resource's `ldap-group-name` is `"storage"`, the `cn` might look something like `cn=cf-storage-project_name-42` |

This plugin also provides a `remove_from_allocation` function that will remove users from an allocation. This can be in ColdFront's `ALLOCATION_FUNCS_ON_EXPIRE` setting.

`ALLOCATION_FUNCS_ON_EXPIRE += ['coldfront_plugin_ldap_allocs.utils.remove_from_allocation',]`

Here are a couple of example configurations:

```
ALLOCATION_FUNCS_ON_EXPIRE += ['coldfront_plugin_ldap_allocs.utils.remove_from_allocation',]
LDAP_ALLOCS_SERVER_URI = ldaps://tls.example.com
LDAP_ALLOCS_BASE = "dc=tls,dc=example,dc=com"
LDAP_ALLOCS_USE_SSL = True
LDAP_ALLOCS_USE_TLS = True
LDAP_ALLOCS_CACERT_FILE = /path/to/cacert
LDAP_ALLOCS_CERT_FILE = /path/to/cert
LDAP_ALLOCS_PRIV_KEY_FILE = /path/to/key
```

```
LDAP_ALLOCS_SERVER_URI = ldap://example.com
LDAP_ALLOCS_BASE = "dc=example,dc=com"
LDAP_ALLOCS_BIND_DN = "cn=Manager,dc=example,dc=com"
LDAP_ALLOCS_BIND_PASSWORD = "secret"
LDAP_ALLOCS_USE_SSL = True
```

## Details
### GID Range
The GID assigned is `LDAP_ALLOCS_GID_MIN` + the allocation's primary key in the ColdFront database. This means expected behavior with a min of `0` might be to see the first few groups have GIDs 1, 5, 7, skipping numbers as allocations for other resources aren't put in LDAP.
Once the range fills up (`LDAP_ALLOCS_GID_MIN` + `allocation_pk` > `LDAP_ALLOCS_GID_MAX`), the GIDs will start to fill the spaces, so the next GID would be 0, then 2, then 3, etc. This allows you to more easily figure out which group is associated with which allocation if anything needs to be manually looked at.

TODO: implement a notification system for when logs are GIDs are running out.

### CN/Group name
The group name or `cn` is `{LDAP_ALLOCS_PREFIX}{ldap_group_name}-{project_title}-{project_primary_key}` For example, if your configuration's `LDAP_ALLOCS_PREFIX` is `"hpc-cf-"`, the allocation's resource `ldap_group_name` is `"storage"`, project title is `"test project"`, project primary key is `42`, the `cn` will look like this: `cn=hpc-cf-storage-test_project-42`.
Project titles are "sanitized" by non alphanumeric characters with underscores.
