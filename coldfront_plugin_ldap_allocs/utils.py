import logging

import ldap.filter
from coldfront.core.allocation.models import Allocation
from coldfront.core.utils.common import import_from_settings
from django.shortcuts import get_object_or_404
from ldap3 import LDIF, MODIFY_ADD, MODIFY_DELETE, SASL, Connection, Server, Tls

logger = logging.getLogger(__name__)


def get_group_name(allocation_obj):
    ldap_group_name = allocation_obj.get_attribute("ldap-group-name")
    if ldap_group_name is None:
        logger.warn(f"No ldap-group-name attribute on allocation {allocation_obj.id}")
        return None
    ldap_group_name = f"{import_from_settings('LDAP_ALLOCS_PREFIX', '')}{ldap_group_name}-{allocation_obj.project.title}-{allocation_obj.project.pk}"
    # TODO: sanitize project title
    return ldap_group_name


def remove_from_allocation(allocation_pk):
    allocation_obj = get_object_or_404(Allocation, pk=allocation_pk)
    ldap_group_name = get_group_name(allocation_obj)
    if ldap_group_name is None:
        return
    ldap_sam = LDAPModify()
    for user in allocation_obj.project.projectuser_set.all():
        ldap_sam.remove_user_from_group(ldap_group_name, user.user.username)


class LDAPModify:
    def __init__(self):
        self.LDAP_SERVER_URI = import_from_settings("LDAP_ALLOCS_SERVER_URI")
        self.LDAP_BASE_DN = import_from_settings("LDAP_ALLOCS_BASE")
        self.LDAP_BIND_DN = import_from_settings("LDAP_ALLOCS_BIND_DN", None)
        self.LDAP_BIND_PASSWORD = import_from_settings(
            "LDAP_ALLOCS_BIND_PASSWORD", None
        )
        self.LDAP_CONNECT_TIMEOUT = import_from_settings(
            "LDAP_ALLOCS_CONNECT_TIMEOUT", 2.5
        )
        self.LDAP_USE_SSL = import_from_settings("LDAP_ALLOCS_USE_SSL", True)
        self.LDAP_USE_TLS = import_from_settings("LDAP_ALLOCS_USE_TLS", False)
        self.LDAP_PRIV_KEY_FILE = import_from_settings("LDAP_ALLOCS_PRIV_KEY_FILE", "")
        self.LDAP_CERT_FILE = import_from_settings("LDAP_ALLOCS_CERT_FILE", "")
        self.LDAP_CACERT_FILE = import_from_settings("LDAP_ALLOCS_CACERT_FILE", "")

        tls = None
        if self.LDAP_USE_TLS:
            tls = Tls(
                local_private_key_file=self.LDAP_PRIV_KEY_FILE,
                local_certificate_file=self.LDAP_CERT_FILE,
                ca_certs_file=self.LDAP_CACERT_FILE,
            )

        self.server = Server(
            self.LDAP_SERVER_URI,
            use_ssl=self.LDAP_USE_SSL,
            connect_timeout=self.LDAP_CONNECT_TIMEOUT,
            tls=tls,
        )

        self.conn_ldif = Connection(server=None, client_strategy=LDIF)
        self.conn_ldif.open()
        self.conn = Connection(
            self.server,
            self.LDAP_BIND_DN,
            self.LDAP_BIND_PASSWORD,
            auto_bind=True,
            authentication=SASL,
            sasl_mechanism="EXTERNAL",
            sasl_credentials="",
        )

    def search_a_group(self, group_name, objectClass=None):
        size_limit = 50
        filter = ldap.filter.filter_format("(cn=%s)", [group_name])
        search_base = self.LDAP_BASE_DN
        if objectClass is not None:
            search_base = f"ou={objectClass},{search_base}"
        searchParameters = {
            "search_base": search_base,
            "search_filter": filter,
            "size_limit": size_limit,
        }
        logger.debug(f"Group search params: {searchParameters}")

        self.conn.search(**searchParameters)

        groups = []
        for entry in self.conn.entries:
            groups.append(entry)

        logger.info("LDAP group search for %s found %s results", group_name, (groups))
        return groups

    def add_user_to_group(self, group_name, username):
        modify_params = {
            "dn": f"cn={group_name},ou=groups,{self.LDAP_BASE_DN}",
            "changes": {"memberUid": [(MODIFY_ADD, username)]},
        }
        self.conn_ldif.modify(**modify_params)
        self.conn.modify(**modify_params)
        logger.debug(f"Add {username} to {group_name} response: {self.conn.result}")

    def remove_user_from_group(self, group_name, username):
        modify_params = {
            "dn": f"cn={group_name},ou=groups,{self.LDAP_BASE_DN}",
            "changes": {"memberUid": [(MODIFY_DELETE, username)]},
        }
        self.conn_ldif.modify(**modify_params)
        self.conn.modify(**modify_params)
        logger.debug(
            f"Remove {username} from {group_name} response: {self.conn.result}"
        )

    def create_group(self, group_name, objectClass, attrs: dict):
        # self.conn_ldif.add(
        add_params = {
            "dn": f"cn={group_name},ou=groups,{self.LDAP_BASE_DN}",
            "attributes": {
                "objectClass": [],
                # "ou": "groups",
            },
        }
        add_params["attributes"]["objectClass"].append(objectClass)
        add_params["attributes"].update(attrs)
        self.conn_ldif.add(**add_params)
        self.conn.add(**add_params)
        logger.debug(f"Create group response: {self.conn.result}")

    def get_group_gid(self, group_cn) -> int:
        filter = ldap.filter.filter_format("(cn=%s)", [group_name])
        size_limit = 1
        search_base = self.LDAP_BASE_DN
        searchParameters = {
            "search_base": search_base,
            "search_filter": filter,
            "size_limit": size_limit,
            "attributes": "gidNumber",
        }
        self.conn.search(**searchParameters)
        return self.conn.entries[0]["gidNumber"]

    def get_next_gid(self):
        gid_min = import_from_settings("LDAP_ALLOCS_GID_MIN", 65565)
        gid_max = import_from_settings("LDAP_ALLOCS_GID_MAX", 2**32 - 1)
        filter = ldap.filter.filter_format(
            "(cn=%s*)",
            [import_from_settings("LDAP_ALLOCS_PREFIX", "")],
        )
        search_base = f"ou=groups,{self.LDAP_BASE_DN}"
        searchParameters = {
            "search_base": search_base,
            "search_filter": filter,
            "attributes": "gidNumber",
        }
        self.conn.search(**searchParameters)
        gid_list = [entry["gidNumber"] for entry in self.conn.entries]
        try:
            return next(
                (gid for gid in range(gid_min, gid_max + 1) if gid not in gid_list)
            )
        except StopIteration:
            return None
