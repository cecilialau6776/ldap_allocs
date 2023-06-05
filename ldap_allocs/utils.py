import json
import logging
import ssl

import ldap.filter

from django.shortcuts import get_object_or_404

from coldfront.core.user.utils import UserSearch
from coldfront.core.utils.common import import_from_settings
from coldfront.core.allocation.models import Allocation
from ldap3 import Connection, Server, Tls, LDIF, SASL, MODIFY_ADD, MODIFY_DELETE

# from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def get_group_name(allocation_obj):
    ldap_group_name = allocation_obj.resources.all()[0].get_attribute("ldap-group-name")
    if ldap_group_name is None:
        return None
    ldap_group_name += f"${allocation_obj.project.pk}"
    return ldap_group_name


def remove_from_expired_allocation(allocation_pk):
    allocation_obj = get_object_or_404(Allocation, pk=allocation_pk)
    ldap_group_name = get_group_name(allocation_obj)
    if ldap_group_name is None:
        return
    ldap_sam = LDAPModify()
    for user in allocation_obj.project.projectuser_set.all():
        ldap_sam.remove_user_from_group(ldap_group_name, user.user.username)


class LDAPUserSearch(UserSearch):
    search_source = "LDAP"

    def __init__(self, user_search_string, search_by):
        super().__init__(user_search_string, search_by)
        self.LDAP_SERVER_URI = import_from_settings("LDAP_USER_SEARCH_SERVER_URI")
        self.LDAP_BASE_DN = import_from_settings("LDAP_USER_SEARCH_BASE")
        self.LDAP_BIND_DN = import_from_settings("LDAP_USER_SEARCH_BIND_DN", None)
        self.LDAP_BIND_PASSWORD = import_from_settings(
            "LDAP_USER_SEARCH_BIND_PASSWORD", None
        )
        self.LDAP_CONNECT_TIMEOUT = import_from_settings(
            "LDAP_USER_SEARCH_CONNECT_TIMEOUT", 2.5
        )
        self.LDAP_USE_SSL = import_from_settings("LDAP_USER_SEARCH_USE_SSL", True)
        self.LDAP_USE_TLS = import_from_settings("LDAP_USER_SEARCH_USE_TLS", False)
        self.LDAP_PRIV_KEY_FILE = import_from_settings(
            "LDAP_USER_SEARCH_PRIV_KEY_FILE", ""
        )
        self.LDAP_CERT_FILE = import_from_settings("LDAP_USER_SEARCH_CERT_FILE", "")
        self.LDAP_CACERT_FILE = import_from_settings("LDAP_USER_SEARCH_CACERT_FILE", "")

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

        self.conn = Connection(
            self.server,
            self.LDAP_BIND_DN,
            self.LDAP_BIND_PASSWORD,
            auto_bind=True,
            # authentication=SASL,
            # sasl_mechanism="EXTERNAL",
            # sasl_credentials="",
        )

    def parse_ldap_entry(self, entry):
        entry_dict = json.loads(entry.entry_to_json()).get("attributes")

        user_dict = {
            "last_name": entry_dict.get("sn")[0] if entry_dict.get("sn") else "",
            "first_name": entry_dict.get("givenName")[0]
            if entry_dict.get("givenName")
            else "",
            "username": entry_dict.get("uid")[0] if entry_dict.get("uid") else "",
            "email": entry_dict.get("mail")[0] if entry_dict.get("mail") else "",
            "source": self.search_source,
        }

        return user_dict

    def search_a_user(self, user_search_string=None, search_by="all_fields"):
        size_limit = 50
        if user_search_string and search_by == "all_fields":
            filter = ldap.filter.filter_format(
                "(|(givenName=*%s*)(sn=*%s*)(uid=*%s*)(mail=*%s*))",
                [user_search_string] * 4,
            )
        elif user_search_string and search_by == "username_only":
            filter = ldap.filter.filter_format("(uid=%s)", [user_search_string])
            size_limit = 1
        else:
            filter = "(objectclass=person)"

        searchParameters = {
            "search_base": self.LDAP_BASE_DN,
            "search_filter": filter,
            "attributes": ["uid", "sn", "givenName", "mail"],
            "size_limit": size_limit,
        }
        self.conn.search(**searchParameters)
        users = []
        for idx, entry in enumerate(self.conn.entries, 1):
            user_dict = self.parse_ldap_entry(entry)
            users.append(user_dict)

        logger.info(
            "LDAP user search for %s found %s results", user_search_string, len(users)
        )
        return users


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
        # logger.info("Response to ldif: %s\n\n", self.conn.response_to_ldif())
        # logger.info("LDIF-CHANGE: %s", self.conn.response_to_ldif())
        return groups

    def add_user_to_group(self, group_name, username):
        modify_params = {
            "dn": f"cn={group_name},ou=groups,{self.LDAP_BASE_DN}",
            "changes": {"memberUid": [(MODIFY_ADD, username)]},
        }
        self.conn_ldif.modify(**modify_params)
        # logger.debug(f"Add {username} to {group_name} ldif: {self.conn_ldif.response}")
        self.conn.modify(**modify_params)
        logger.debug(f"Add {username} to {group_name} response: {self.conn.result}")

    def remove_user_from_group(self, group_name, username):
        modify_params = {
            "dn": f"cn={group_name},ou=groups,{self.LDAP_BASE_DN}",
            "changes": {"memberUid": [(MODIFY_DELETE, username)]},
        }
        self.conn_ldif.modify(**modify_params)
        # logger.debug(f"Add {username} to {group_name} ldif: {self.conn_ldif.response}")
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
        # logger.debug(f"Create group ldif: {self.conn_ldif.response}")
        self.conn.add(**add_params)
        logger.debug(f"Create group response: {self.conn.result}")
