import logging
from coldfront.core.allocation.signals import allocation_activate

logger = logging.get(__name__)

@receive(allocation_activate)
def allocation_activate(sender, **kwargs):
    allocation_pk = kwargs.get("allocation_pk")
    logger.warning(allocation_pk)
