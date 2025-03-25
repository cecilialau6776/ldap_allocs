import logging

from django.core.management.base import BaseCommand
from coldfront.core.allocation.models import AttributeType, AllocationAttributeType


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Add the `ldap-group-name` attribute type choice"

    def handle(self, *args, **options):
        text_at = AttributeType.objects.get(name="Text")
        AllocationAttributeType.objects.get_or_create(
            attribute_type=at, name="ldap-group-name"
        )
