from django.apps import AppConfig


class LdapUserSearchConfig(AppConfig):
    name = "coldfront_plugin_ldap_allocs"

    def ready(self):
        import coldfront_plugin_ldap_allocs.signals
