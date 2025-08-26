import logging

from coldfront.core.allocation.models import (
    Allocation,
    AllocationAttribute,
    AllocationAttributeType,
    AllocationUser,
)
from coldfront.core.allocation.signals import (
    allocation_activate,
    allocation_activate_user,
    allocation_remove_user,
)
from coldfront.core.utils.common import import_from_settings
from django.dispatch import receiver
from django.shortcuts import get_object_or_404

from coldfront_plugin_ldap_allocs.utils import LDAPModify, get_group_name
import ldap3.core.results as LDAP

logger = logging.getLogger(__name__)


@receiver(allocation_remove_user)
def alloc_remove_user(sender, **kwargs):
    allocation_user_id = kwargs.get("allocation_user_pk")
    allocation_user = get_object_or_404(AllocationUser, pk=allocation_user_id)
    allocation_obj = allocation_user.allocation
    if allocation_obj.status.name != "Active":
        return
    ldap_group_name = get_group_name(allocation_obj)
    if ldap_group_name is None:
        return
    ldap_sam = LDAPModify()
    ldap_sam.remove_user_from_group(ldap_group_name, allocation_user.user.username)


@receiver(allocation_activate_user)
def alloc_activate_user(sender, **kwargs):
    allocation_user_id = kwargs.get("allocation_user_pk")
    allocation_user = get_object_or_404(AllocationUser, pk=allocation_user_id)
    allocation_obj = allocation_user.allocation
    if allocation_obj.status.name != "Active":
        return

    ldap_group_name = get_group_name(allocation_obj)
    if ldap_group_name is None:
        return
    ldap_sam = LDAPModify()
    ldap_sam.add_user_to_group(ldap_group_name, allocation_user.user.username)


# @receiver(allocation_disable)
# def alloc_disable(sender, **kwargs):
#     allocation_id = kwargs.get("allocation_pk")
#     allocation_obj = get_object_or_404(Allocation, pk=allocation_id)
#     ldap_sam = LDAPModify()
#     for resource in allocation_obj.resources.all():
#         ldap_group_name = resource.get_attribute("ldap-group-name")
#         groups = ldap_sam.search_a_group(ldap_group_name, objectClass="groups")
#         for user in allocation_obj.project.projectuser_set.filter(
#             ~Q(status__name="Active")
#         ):
#             ldap_sam.remove_user_from_group(ldap_group_name, user.user.username)


@receiver(allocation_activate)
def alloc_activate(sender, **kwargs):
    allocation_id = kwargs.get("allocation_pk")
    allocation_obj = get_object_or_404(Allocation, pk=allocation_id)

    # each project will only be able to have one group for each allocation resource type
    ldap_group_cn = get_group_name(allocation_obj)
    if ldap_group_cn is None:
        return

    ldap_sam = LDAPModify()
    groups = ldap_sam.search_a_group(ldap_group_cn, objectClass="groups")
    if len(groups) == 0:
        # Check gid is within range or taken
        gid_min = import_from_settings("LDAP_ALLOCS_GID_MIN", 0)
        gid_max = import_from_settings("LDAP_ALLOCS_GID_MAX", 2**32 - 1)
        gid = gid_min + allocation_id
        if gid > gid_max:
            gid = LDAPModify().get_next_gid()
            if gid is None:
                logger.critical("No more gids available in range")
        ldap_sam.create_group(
            ldap_group_cn,
            "posixGroup",
            {"gidNumber": gid},
        )
    if ldap_sam.conn.result["result"] == LDAP.RESULT_CONSTRAINT_VIOLATION:
        logger.warn("Trying again with a different gid...")
        # if we get a constraint violation, try again with a different GID
        gid = LDAPModify().get_next_gid()
        ldap_sam.create_group(
            ldap_group_cn,
            "posixGroup",
            {"gidNumber": gid},
        )
    if ldap_sam.conn.result["result"] != LDAP.RESULT_SUCCESS:
        logger.critical(f"Failed to create group {ldap_group_cn}")
        return

    logger.info(f"Successfully created group {ldap_group_cn} with gid {gid}")

    # create allocation attribute for the group cn
    aat_group_cn = AllocationAttributeType.objects.get(name="ldap-group-cn")
    AllocationAttribute.objects.get_or_create(
        allocation_attribute_type=aat_group_cn,
        allocation=allocation_obj,
        value=ldap_group_cn,
    )
