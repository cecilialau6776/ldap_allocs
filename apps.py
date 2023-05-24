from django.apps import AppConfig


class LdapUserSearchConfig(AppConfig):
    name = "coldfront.plugins.ldap_allocs"

    def ready(self):
        import coldfront.plugins.ldap_allocs.signals
