"""
Permission Detector - The "Who has access to X?" engine.

This is the crown jewel of sf-permissions. It answers questions like:
- "Who has delete access to Account?"
- "Which Permission Sets grant access to MyApexClass?"
- "Find all PS with Custom_Permission_X"

The detector queries various permission tables and enriches results
with Permission Set Group membership information.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from simple_salesforce import Salesforce


class PermissionType(Enum):
    """Types of permissions that can be detected."""
    OBJECT = "object"           # Object CRUD permissions
    FIELD = "field"             # Field-level security
    APEX_CLASS = "apex"         # Apex class access
    VF_PAGE = "vf"              # Visualforce page access
    FLOW = "flow"               # Flow access
    CUSTOM_PERMISSION = "custom"  # Custom permissions
    TAB = "tab"                 # Tab visibility


class ObjectAccess(Enum):
    """Object-level access types."""
    CREATE = "PermissionsCreate"
    READ = "PermissionsRead"
    EDIT = "PermissionsEdit"
    DELETE = "PermissionsDelete"
    VIEW_ALL = "PermissionsViewAllRecords"
    MODIFY_ALL = "PermissionsModifyAllRecords"


@dataclass
class DetectionResult:
    """A single permission detection result."""
    permission_set_id: str
    permission_set_name: str
    permission_set_label: str
    is_in_group: bool
    group_id: Optional[str]
    group_name: Optional[str]
    group_label: Optional[str]
    access_details: dict
    assigned_user_count: int = 0


def detect_object_permission(
    sf: Salesforce,
    object_name: str,
    access_types: list[str] = None
) -> list[DetectionResult]:
    """
    Find all Permission Sets that grant specific object access.

    Args:
        sf: Salesforce connection
        object_name: API name of the object (e.g., 'Account', 'Custom_Object__c')
        access_types: List of access types to check. Options:
                     'create', 'read', 'edit', 'delete', 'view_all', 'modify_all'
                     If None, checks for any access.

    Returns:
        List of DetectionResult with matching Permission Sets

    Example:
        >>> results = detect_object_permission(sf, 'Account', ['delete'])
        >>> for r in results:
        ...     print(f"{r.permission_set_name}: Delete={r.access_details.get('delete')}")
    """
    # Build the WHERE clause for access types
    if access_types:
        access_map = {
            'create': 'PermissionsCreate',
            'read': 'PermissionsRead',
            'edit': 'PermissionsEdit',
            'delete': 'PermissionsDelete',
            'view_all': 'PermissionsViewAllRecords',
            'modify_all': 'PermissionsModifyAllRecords',
        }
        conditions = [f"{access_map[a.lower()]} = true" for a in access_types if a.lower() in access_map]
        access_filter = f"AND ({' OR '.join(conditions)})" if conditions else ""
    else:
        # Any access
        access_filter = """AND (
            PermissionsCreate = true OR PermissionsRead = true OR
            PermissionsEdit = true OR PermissionsDelete = true OR
            PermissionsViewAllRecords = true OR PermissionsModifyAllRecords = true
        )"""

    query = f"""
        SELECT
            ParentId, Parent.Name, Parent.Label,
            SobjectType,
            PermissionsCreate, PermissionsRead, PermissionsEdit, PermissionsDelete,
            PermissionsViewAllRecords, PermissionsModifyAllRecords
        FROM ObjectPermissions
        WHERE SobjectType = '{object_name}'
        {access_filter}
    """

    results = sf.query_all(query)

    if not results['records']:
        return []

    # Get Permission Set IDs
    ps_ids = [r['ParentId'] for r in results['records']]

    # Get PSG membership for these Permission Sets
    psg_membership = _get_psg_membership(sf, ps_ids)

    # Get user counts
    user_counts = _get_user_counts(sf, ps_ids)

    # Build detection results
    detection_results = []
    for record in results['records']:
        ps_id = record['ParentId']
        psg_info = psg_membership.get(ps_id, {})

        detection_results.append(DetectionResult(
            permission_set_id=ps_id,
            permission_set_name=record['Parent']['Name'],
            permission_set_label=record['Parent']['Label'],
            is_in_group=bool(psg_info),
            group_id=psg_info.get('group_id'),
            group_name=psg_info.get('group_name'),
            group_label=psg_info.get('group_label'),
            access_details={
                'create': record['PermissionsCreate'],
                'read': record['PermissionsRead'],
                'edit': record['PermissionsEdit'],
                'delete': record['PermissionsDelete'],
                'view_all': record['PermissionsViewAllRecords'],
                'modify_all': record['PermissionsModifyAllRecords'],
            },
            assigned_user_count=user_counts.get(ps_id, 0)
        ))

    return detection_results


def detect_field_permission(
    sf: Salesforce,
    object_name: str,
    field_name: str,
    access_types: list[str] = None
) -> list[DetectionResult]:
    """
    Find all Permission Sets that grant specific field access.

    Args:
        sf: Salesforce connection
        object_name: API name of the object
        field_name: API name of the field
        access_types: List of access types: 'read', 'edit'. If None, checks for any access.

    Returns:
        List of DetectionResult with matching Permission Sets

    Example:
        >>> results = detect_field_permission(sf, 'Account', 'AnnualRevenue', ['edit'])
    """
    full_field_name = f"{object_name}.{field_name}"

    if access_types:
        conditions = []
        if 'read' in [a.lower() for a in access_types]:
            conditions.append("PermissionsRead = true")
        if 'edit' in [a.lower() for a in access_types]:
            conditions.append("PermissionsEdit = true")
        access_filter = f"AND ({' OR '.join(conditions)})" if conditions else ""
    else:
        access_filter = "AND (PermissionsRead = true OR PermissionsEdit = true)"

    query = f"""
        SELECT
            ParentId, Parent.Name, Parent.Label,
            Field, PermissionsRead, PermissionsEdit
        FROM FieldPermissions
        WHERE Field = '{full_field_name}'
        {access_filter}
    """

    results = sf.query_all(query)

    if not results['records']:
        return []

    ps_ids = [r['ParentId'] for r in results['records']]
    psg_membership = _get_psg_membership(sf, ps_ids)
    user_counts = _get_user_counts(sf, ps_ids)

    detection_results = []
    for record in results['records']:
        ps_id = record['ParentId']
        psg_info = psg_membership.get(ps_id, {})

        detection_results.append(DetectionResult(
            permission_set_id=ps_id,
            permission_set_name=record['Parent']['Name'],
            permission_set_label=record['Parent']['Label'],
            is_in_group=bool(psg_info),
            group_id=psg_info.get('group_id'),
            group_name=psg_info.get('group_name'),
            group_label=psg_info.get('group_label'),
            access_details={
                'read': record['PermissionsRead'],
                'edit': record['PermissionsEdit'],
            },
            assigned_user_count=user_counts.get(ps_id, 0)
        ))

    return detection_results


def detect_apex_class_permission(
    sf: Salesforce,
    class_name: str
) -> list[DetectionResult]:
    """
    Find all Permission Sets that grant access to an Apex class.

    Args:
        sf: Salesforce connection
        class_name: Name of the Apex class

    Returns:
        List of DetectionResult with matching Permission Sets
    """
    # First, get the Apex class ID
    class_query = f"SELECT Id, Name FROM ApexClass WHERE Name = '{class_name}'"
    class_result = sf.query(class_query)

    if not class_result['records']:
        return []

    class_id = class_result['records'][0]['Id']

    return _detect_setup_entity_access(sf, 'ApexClass', class_id, class_name)


def detect_vf_page_permission(
    sf: Salesforce,
    page_name: str
) -> list[DetectionResult]:
    """
    Find all Permission Sets that grant access to a Visualforce page.

    Args:
        sf: Salesforce connection
        page_name: Name of the Visualforce page

    Returns:
        List of DetectionResult with matching Permission Sets
    """
    # Get the VF page ID
    page_query = f"SELECT Id, Name FROM ApexPage WHERE Name = '{page_name}'"
    page_result = sf.query(page_query)

    if not page_result['records']:
        return []

    page_id = page_result['records'][0]['Id']

    return _detect_setup_entity_access(sf, 'ApexPage', page_id, page_name)


def detect_custom_permission(
    sf: Salesforce,
    permission_name: str
) -> list[DetectionResult]:
    """
    Find all Permission Sets that grant a custom permission.

    Args:
        sf: Salesforce connection
        permission_name: DeveloperName of the custom permission

    Returns:
        List of DetectionResult with matching Permission Sets
    """
    # Get the custom permission ID
    perm_query = f"SELECT Id, DeveloperName, MasterLabel FROM CustomPermission WHERE DeveloperName = '{permission_name}'"
    perm_result = sf.query(perm_query)

    if not perm_result['records']:
        return []

    perm_id = perm_result['records'][0]['Id']

    return _detect_setup_entity_access(sf, 'CustomPermission', perm_id, permission_name)


def detect_flow_permission(
    sf: Salesforce,
    flow_name: str
) -> list[DetectionResult]:
    """
    Find all Permission Sets that grant access to run a Flow.

    Args:
        sf: Salesforce connection
        flow_name: API name of the Flow

    Returns:
        List of DetectionResult with matching Permission Sets
    """
    # Get the Flow ID (use FlowDefinition for the API name)
    flow_query = f"""
        SELECT Id, DeveloperName, ActiveVersionId
        FROM FlowDefinition
        WHERE DeveloperName = '{flow_name}'
    """
    flow_result = sf.query(flow_query)

    if not flow_result['records']:
        return []

    # SetupEntityAccess uses the active version ID
    active_version_id = flow_result['records'][0].get('ActiveVersionId')
    if not active_version_id:
        return []

    return _detect_setup_entity_access(sf, 'Flow', active_version_id, flow_name)


def _detect_setup_entity_access(
    sf: Salesforce,
    entity_type: str,
    entity_id: str,
    entity_name: str
) -> list[DetectionResult]:
    """
    Generic detection for SetupEntityAccess (Apex, VF, Flow, CustomPermission).

    Args:
        sf: Salesforce connection
        entity_type: Type of entity (ApexClass, ApexPage, Flow, CustomPermission)
        entity_id: ID of the entity
        entity_name: Name of the entity (for display)

    Returns:
        List of DetectionResult
    """
    query = f"""
        SELECT
            ParentId, Parent.Name, Parent.Label,
            SetupEntityType, SetupEntityId
        FROM SetupEntityAccess
        WHERE SetupEntityType = '{entity_type}'
        AND SetupEntityId = '{entity_id}'
    """

    results = sf.query_all(query)

    if not results['records']:
        return []

    ps_ids = [r['ParentId'] for r in results['records']]
    psg_membership = _get_psg_membership(sf, ps_ids)
    user_counts = _get_user_counts(sf, ps_ids)

    detection_results = []
    for record in results['records']:
        ps_id = record['ParentId']
        psg_info = psg_membership.get(ps_id, {})

        detection_results.append(DetectionResult(
            permission_set_id=ps_id,
            permission_set_name=record['Parent']['Name'],
            permission_set_label=record['Parent']['Label'],
            is_in_group=bool(psg_info),
            group_id=psg_info.get('group_id'),
            group_name=psg_info.get('group_name'),
            group_label=psg_info.get('group_label'),
            access_details={
                'entity_type': entity_type,
                'entity_name': entity_name,
                'has_access': True,
            },
            assigned_user_count=user_counts.get(ps_id, 0)
        ))

    return detection_results


def _get_psg_membership(sf: Salesforce, ps_ids: list[str]) -> dict:
    """
    Get Permission Set Group membership for a list of Permission Set IDs.

    Returns a dict mapping PS ID -> {group_id, group_name, group_label}
    """
    if not ps_ids:
        return {}

    # Format IDs for IN clause
    ids_str = "', '".join(ps_ids)

    query = f"""
        SELECT
            PermissionSetId,
            PermissionSetGroupId,
            PermissionSetGroup.DeveloperName,
            PermissionSetGroup.MasterLabel
        FROM PermissionSetGroupComponent
        WHERE PermissionSetId IN ('{ids_str}')
    """

    results = sf.query_all(query)

    membership = {}
    for record in results['records']:
        ps_id = record['PermissionSetId']
        # A PS can be in multiple groups; we just take the first for simplicity
        if ps_id not in membership:
            membership[ps_id] = {
                'group_id': record['PermissionSetGroupId'],
                'group_name': record['PermissionSetGroup']['DeveloperName'],
                'group_label': record['PermissionSetGroup']['MasterLabel'],
            }

    return membership


def _get_user_counts(sf: Salesforce, ps_ids: list[str]) -> dict:
    """
    Get the count of users assigned to each Permission Set.

    Returns a dict mapping PS ID -> user count
    """
    if not ps_ids:
        return {}

    ids_str = "', '".join(ps_ids)

    query = f"""
        SELECT PermissionSetId, COUNT(AssigneeId) userCount
        FROM PermissionSetAssignment
        WHERE PermissionSetId IN ('{ids_str}')
        GROUP BY PermissionSetId
    """

    results = sf.query_all(query)

    counts = {}
    for record in results['records']:
        counts[record['PermissionSetId']] = record['userCount']

    return counts


def detect_system_permission(
    sf: Salesforce,
    permission_name: str
) -> list[DetectionResult]:
    """
    Find all Permission Sets that have a specific system permission enabled.

    System permissions are fields on the PermissionSet object itself,
    like PermissionsModifyAllData, PermissionsViewSetup, etc.

    Args:
        sf: Salesforce connection
        permission_name: Name of the system permission (e.g., 'ModifyAllData', 'ViewSetup')

    Returns:
        List of DetectionResult with matching Permission Sets
    """
    # Ensure the permission name has the Permissions prefix
    if not permission_name.startswith('Permissions'):
        field_name = f'Permissions{permission_name}'
    else:
        field_name = permission_name

    query = f"""
        SELECT Id, Name, Label, {field_name}
        FROM PermissionSet
        WHERE {field_name} = true
        AND IsOwnedByProfile = false
    """

    try:
        results = sf.query_all(query)
    except Exception as e:
        if 'INVALID_FIELD' in str(e):
            raise ValueError(f"Unknown system permission: {permission_name}")
        raise

    if not results['records']:
        return []

    ps_ids = [r['Id'] for r in results['records']]
    psg_membership = _get_psg_membership(sf, ps_ids)
    user_counts = _get_user_counts(sf, ps_ids)

    detection_results = []
    for record in results['records']:
        ps_id = record['Id']
        psg_info = psg_membership.get(ps_id, {})

        detection_results.append(DetectionResult(
            permission_set_id=ps_id,
            permission_set_name=record['Name'],
            permission_set_label=record['Label'],
            is_in_group=bool(psg_info),
            group_id=psg_info.get('group_id'),
            group_name=psg_info.get('group_name'),
            group_label=psg_info.get('group_label'),
            access_details={
                'system_permission': permission_name,
                'enabled': True,
            },
            assigned_user_count=user_counts.get(ps_id, 0)
        ))

    return detection_results


# Convenience function for natural language queries
def detect(
    sf: Salesforce,
    permission_type: str,
    name: str,
    field: str = None,
    access: list[str] = None
) -> list[DetectionResult]:
    """
    Unified detection function for natural language processing.

    Args:
        sf: Salesforce connection
        permission_type: One of 'object', 'field', 'apex', 'vf', 'flow', 'custom', 'system'
        name: Name of the object/class/page/permission
        field: Field name (only for field permissions)
        access: Access types to check (only for object/field permissions)

    Returns:
        List of DetectionResult

    Example:
        >>> detect(sf, 'object', 'Account', access=['delete'])
        >>> detect(sf, 'field', 'Account', field='AnnualRevenue', access=['edit'])
        >>> detect(sf, 'apex', 'MyApexClass')
        >>> detect(sf, 'custom', 'Can_Approve_Expenses')
    """
    ptype = permission_type.lower()

    if ptype == 'object':
        return detect_object_permission(sf, name, access)
    elif ptype == 'field':
        if not field:
            raise ValueError("Field name required for field permission detection")
        return detect_field_permission(sf, name, field, access)
    elif ptype == 'apex':
        return detect_apex_class_permission(sf, name)
    elif ptype == 'vf':
        return detect_vf_page_permission(sf, name)
    elif ptype == 'flow':
        return detect_flow_permission(sf, name)
    elif ptype == 'custom':
        return detect_custom_permission(sf, name)
    elif ptype == 'system':
        return detect_system_permission(sf, name)
    else:
        raise ValueError(f"Unknown permission type: {permission_type}")


if __name__ == '__main__':
    # Quick test
    import sys
    from auth import get_sf_connection

    sf = get_sf_connection()

    # Test object permission detection
    print("Testing: Who has delete access to Account?")
    results = detect_object_permission(sf, 'Account', ['delete'])

    for r in results:
        group_info = f" (in {r.group_name})" if r.is_in_group else " (standalone)"
        print(f"  • {r.permission_set_name}{group_info} - {r.assigned_user_count} users")
