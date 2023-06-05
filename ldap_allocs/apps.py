from django.apps import AppConfig


class LdapUserSearchConfig(AppConfig):
    name = "coldfront_plugins_ldap_allocs"

    def ready(self):
        import coldfront_plugins_ldap_allocs.signals
