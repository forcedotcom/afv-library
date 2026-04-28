"""
Permission Hierarchy Viewer

Builds and displays the complete Permission Set and Permission Set Group
hierarchy for an org. Shows which PS belong to which PSG, and identifies
standalone Permission Sets.
"""

from dataclasses import dataclass, field
from typing import Optional
from simple_salesforce import Salesforce


@dataclass
class PermissionSetInfo:
    """Information about a Permission Set."""
    id: str
    name: str
    label: str
    description: Optional[str] = None
    is_owned_by_profile: bool = False
    is_custom: bool = True
    license_name: Optional[str] = None
    assigned_user_count: int = 0


@dataclass
class PermissionSetGroupInfo:
    """Information about a Permission Set Group."""
    id: str
    developer_name: str
    master_label: str
    description: Optional[str] = None
    status: str = "Active"  # Active, Outdated, etc.
    permission_sets: list[PermissionSetInfo] = field(default_factory=list)
    assigned_user_count: int = 0


@dataclass
class OrgPermissionHierarchy:
    """Complete permission hierarchy for an org."""
    permission_set_groups: list[PermissionSetGroupInfo]
    standalone_permission_sets: list[PermissionSetInfo]
    profile_permission_sets: list[PermissionSetInfo]
    total_ps_count: int = 0
    total_psg_count: int = 0


def get_org_permission_hierarchy(sf: Salesforce) -> OrgPermissionHierarchy:
    """
    Build the complete Permission Set and Permission Set Group hierarchy.

    This queries:
    1. All Permission Set Groups
    2. All Permission Sets in each group (via PermissionSetGroupComponent)
    3. All standalone Permission Sets (not in any group)
    4. Profile-owned Permission Sets (for reference)

    Args:
        sf: Salesforce connection

    Returns:
        OrgPermissionHierarchy containing the full structure

    Example:
        >>> hierarchy = get_org_permission_hierarchy(sf)
        >>> print(f"Found {hierarchy.total_psg_count} groups, {hierarchy.total_ps_count} permission sets")
    """
    # Step 1: Get all Permission Set Groups
    psg_query = """
        SELECT Id, DeveloperName, MasterLabel, Description, Status
        FROM PermissionSetGroup
        ORDER BY MasterLabel
    """
    psg_results = sf.query_all(psg_query)

    # Step 2: Get all PSG components (PS -> PSG mapping)
    component_query = """
        SELECT
            PermissionSetGroupId,
            PermissionSetId,
            PermissionSet.Name,
            PermissionSet.Label,
            PermissionSet.Description
        FROM PermissionSetGroupComponent
    """
    component_results = sf.query_all(component_query)

    # Build a map of PSG ID -> list of PS
    psg_to_ps = {}
    ps_in_groups = set()
    for comp in component_results['records']:
        psg_id = comp['PermissionSetGroupId']
        if psg_id not in psg_to_ps:
            psg_to_ps[psg_id] = []

        ps_info = PermissionSetInfo(
            id=comp['PermissionSetId'],
            name=comp['PermissionSet']['Name'],
            label=comp['PermissionSet']['Label'],
            description=comp['PermissionSet'].get('Description'),
        )
        psg_to_ps[psg_id].append(ps_info)
        ps_in_groups.add(comp['PermissionSetId'])

    # Step 3: Get all Permission Sets (to find standalone ones)
    ps_query = """
        SELECT Id, Name, Label, Description, IsOwnedByProfile, IsCustom,
               License.Name
        FROM PermissionSet
        WHERE Type != 'Group'
        ORDER BY Label
    """
    ps_results = sf.query_all(ps_query)

    # Step 4: Get user assignment counts for all PS and PSG
    ps_counts = _get_ps_user_counts(sf)
    psg_counts = _get_psg_user_counts(sf)

    # Build the hierarchy
    permission_set_groups = []
    for psg in psg_results['records']:
        psg_id = psg['Id']
        ps_list = psg_to_ps.get(psg_id, [])

        # Update user counts for PS in this group
        for ps in ps_list:
            ps.assigned_user_count = ps_counts.get(ps.id, 0)

        psg_info = PermissionSetGroupInfo(
            id=psg_id,
            developer_name=psg['DeveloperName'],
            master_label=psg['MasterLabel'],
            description=psg.get('Description'),
            status=psg.get('Status', 'Active'),
            permission_sets=ps_list,
            assigned_user_count=psg_counts.get(psg_id, 0),
        )
        permission_set_groups.append(psg_info)

    # Separate standalone and profile-owned PS
    standalone_ps = []
    profile_ps = []

    for ps in ps_results['records']:
        ps_id = ps['Id']

        # Skip PS that are in groups
        if ps_id in ps_in_groups:
            continue

        license_name = None
        if ps.get('License'):
            license_name = ps['License'].get('Name')

        ps_info = PermissionSetInfo(
            id=ps_id,
            name=ps['Name'],
            label=ps['Label'],
            description=ps.get('Description'),
            is_owned_by_profile=ps['IsOwnedByProfile'],
            is_custom=ps.get('IsCustom', True),
            license_name=license_name,
            assigned_user_count=ps_counts.get(ps_id, 0),
        )

        if ps['IsOwnedByProfile']:
            profile_ps.append(ps_info)
        else:
            standalone_ps.append(ps_info)

    return OrgPermissionHierarchy(
        permission_set_groups=permission_set_groups,
        standalone_permission_sets=standalone_ps,
        profile_permission_sets=profile_ps,
        total_ps_count=len(ps_results['records']),
        total_psg_count=len(psg_results['records']),
    )


def _get_ps_user_counts(sf: Salesforce) -> dict:
    """Get user assignment counts for all Permission Sets."""
    query = """
        SELECT PermissionSetId, COUNT(AssigneeId) userCount
        FROM PermissionSetAssignment
        WHERE PermissionSetId != null
        GROUP BY PermissionSetId
    """
    results = sf.query_all(query)

    return {r['PermissionSetId']: r['userCount'] for r in results['records']}


def _get_psg_user_counts(sf: Salesforce) -> dict:
    """Get user assignment counts for all Permission Set Groups."""
    query = """
        SELECT PermissionSetGroupId, COUNT(AssigneeId) userCount
        FROM PermissionSetAssignment
        WHERE PermissionSetGroupId != null
        GROUP BY PermissionSetGroupId
    """
    results = sf.query_all(query)

    return {r['PermissionSetGroupId']: r['userCount'] for r in results['records']}


def get_permission_set_details(sf: Salesforce, ps_name: str) -> dict:
    """
    Get detailed information about a specific Permission Set.

    Returns object permissions, field permissions, and setup entity access.

    Args:
        sf: Salesforce connection
        ps_name: Name or ID of the Permission Set

    Returns:
        Dict with 'info', 'object_permissions', 'field_permissions', 'setup_entity_access'
    """
    # Get PS info
    if ps_name.startswith('0PS'):
        ps_query = f"SELECT Id, Name, Label, Description FROM PermissionSet WHERE Id = '{ps_name}'"
    else:
        ps_query = f"SELECT Id, Name, Label, Description FROM PermissionSet WHERE Name = '{ps_name}'"

    ps_result = sf.query(ps_query)
    if not ps_result['records']:
        raise ValueError(f"Permission Set not found: {ps_name}")

    ps = ps_result['records'][0]
    ps_id = ps['Id']

    # Get object permissions
    obj_query = f"""
        SELECT SobjectType, PermissionsCreate, PermissionsRead, PermissionsEdit,
               PermissionsDelete, PermissionsViewAllRecords, PermissionsModifyAllRecords
        FROM ObjectPermissions
        WHERE ParentId = '{ps_id}'
        ORDER BY SobjectType
    """
    obj_results = sf.query_all(obj_query)

    # Get field permissions
    field_query = f"""
        SELECT Field, PermissionsRead, PermissionsEdit
        FROM FieldPermissions
        WHERE ParentId = '{ps_id}'
        ORDER BY Field
    """
    field_results = sf.query_all(field_query)

    # Get setup entity access (Apex, VF, etc.)
    entity_query = f"""
        SELECT SetupEntityType, SetupEntityId
        FROM SetupEntityAccess
        WHERE ParentId = '{ps_id}'
    """
    entity_results = sf.query_all(entity_query)

    return {
        'info': {
            'id': ps['Id'],
            'name': ps['Name'],
            'label': ps['Label'],
            'description': ps.get('Description'),
        },
        'object_permissions': obj_results['records'],
        'field_permissions': field_results['records'],
        'setup_entity_access': entity_results['records'],
    }


def get_psg_details(sf: Salesforce, psg_name: str) -> dict:
    """
    Get detailed information about a specific Permission Set Group.

    Args:
        sf: Salesforce connection
        psg_name: DeveloperName or ID of the Permission Set Group

    Returns:
        Dict with 'info', 'permission_sets', 'assigned_users'
    """
    # Get PSG info
    if psg_name.startswith('0PG'):
        psg_query = f"SELECT Id, DeveloperName, MasterLabel, Description, Status FROM PermissionSetGroup WHERE Id = '{psg_name}'"
    else:
        psg_query = f"SELECT Id, DeveloperName, MasterLabel, Description, Status FROM PermissionSetGroup WHERE DeveloperName = '{psg_name}'"

    psg_result = sf.query(psg_query)
    if not psg_result['records']:
        raise ValueError(f"Permission Set Group not found: {psg_name}")

    psg = psg_result['records'][0]
    psg_id = psg['Id']

    # Get component PS
    comp_query = f"""
        SELECT PermissionSetId, PermissionSet.Name, PermissionSet.Label
        FROM PermissionSetGroupComponent
        WHERE PermissionSetGroupId = '{psg_id}'
    """
    comp_results = sf.query_all(comp_query)

    # Get assigned users
    user_query = f"""
        SELECT Assignee.Name, Assignee.Username, Assignee.IsActive
        FROM PermissionSetAssignment
        WHERE PermissionSetGroupId = '{psg_id}'
        LIMIT 100
    """
    user_results = sf.query_all(user_query)

    return {
        'info': {
            'id': psg['Id'],
            'developer_name': psg['DeveloperName'],
            'master_label': psg['MasterLabel'],
            'description': psg.get('Description'),
            'status': psg.get('Status', 'Active'),
        },
        'permission_sets': [
            {
                'id': c['PermissionSetId'],
                'name': c['PermissionSet']['Name'],
                'label': c['PermissionSet']['Label'],
            }
            for c in comp_results['records']
        ],
        'assigned_users': [
            {
                'name': u['Assignee']['Name'],
                'username': u['Assignee']['Username'],
                'is_active': u['Assignee']['IsActive'],
            }
            for u in user_results['records']
        ],
    }


if __name__ == '__main__':
    from auth import get_sf_connection

    sf = get_sf_connection()

    print("Building org permission hierarchy...")
    hierarchy = get_org_permission_hierarchy(sf)

    print(f"\n📊 Summary:")
    print(f"   Permission Set Groups: {hierarchy.total_psg_count}")
    print(f"   Total Permission Sets: {hierarchy.total_ps_count}")
    print(f"   Standalone PS: {len(hierarchy.standalone_permission_sets)}")

    print(f"\n📁 Permission Set Groups:")
    for psg in hierarchy.permission_set_groups:
        status_icon = "✅" if psg.status == "Active" else "⚠️"
        print(f"   {status_icon} {psg.master_label} ({len(psg.permission_sets)} PS, {psg.assigned_user_count} users)")
        for ps in psg.permission_sets[:3]:
            print(f"      └── {ps.label}")
        if len(psg.permission_sets) > 3:
            print(f"      └── ... and {len(psg.permission_sets) - 3} more")
