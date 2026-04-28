"""
Metadata Fetcher

Provides helper functions to retrieve available objects, fields,
Apex classes, Visualforce pages, Flows, and Custom Permissions
from a Salesforce org.

Useful for autocomplete, validation, and discovery.
"""

from typing import Optional
from simple_salesforce import Salesforce


def get_available_objects(
    sf: Salesforce,
    customizable_only: bool = True
) -> list[dict]:
    """
    Get all objects available in the org.

    Args:
        sf: Salesforce connection
        customizable_only: If True, only return objects that support FLS/permissions

    Returns:
        List of dicts with 'api_name', 'label', 'is_custom'

    Example:
        >>> objects = get_available_objects(sf)
        >>> for obj in objects[:5]:
        ...     print(f"{obj['api_name']}: {obj['label']}")
    """
    if customizable_only:
        query = """
            SELECT QualifiedApiName, Label, IsCustomSetting
            FROM EntityDefinition
            WHERE IsCustomizable = true
            ORDER BY Label
        """
    else:
        query = """
            SELECT QualifiedApiName, Label, IsCustomSetting
            FROM EntityDefinition
            ORDER BY Label
        """

    results = sf.query_all(query)

    return [
        {
            'api_name': r['QualifiedApiName'],
            'label': r['Label'],
            'is_custom': r['QualifiedApiName'].endswith('__c'),
            'is_custom_setting': r.get('IsCustomSetting', False),
        }
        for r in results['records']
    ]


def get_object_fields(
    sf: Salesforce,
    object_name: str,
    permissionable_only: bool = True
) -> list[dict]:
    """
    Get all fields for a specific object.

    Args:
        sf: Salesforce connection
        object_name: API name of the object
        permissionable_only: If True, only return fields that can have FLS set

    Returns:
        List of dicts with 'api_name', 'label', 'data_type', 'is_custom'

    Example:
        >>> fields = get_object_fields(sf, 'Account')
        >>> for f in fields[:5]:
        ...     print(f"{f['api_name']}: {f['data_type']}")
    """
    query = f"""
        SELECT QualifiedApiName, Label, DataType, IsCompound
        FROM FieldDefinition
        WHERE EntityDefinition.QualifiedApiName = '{object_name}'
        ORDER BY Label
    """

    results = sf.query_all(query)

    fields = []
    for r in results['records']:
        # Skip compound fields if only getting permissionable ones
        if permissionable_only and r.get('IsCompound', False):
            continue

        fields.append({
            'api_name': r['QualifiedApiName'],
            'label': r['Label'],
            'data_type': r['DataType'],
            'is_custom': r['QualifiedApiName'].endswith('__c'),
        })

    return fields


def get_apex_classes(sf: Salesforce) -> list[dict]:
    """
    Get all Apex classes in the org.

    Returns:
        List of dicts with 'id', 'name', 'namespace', 'is_valid'
    """
    query = """
        SELECT Id, Name, NamespacePrefix, IsValid, Status
        FROM ApexClass
        ORDER BY Name
    """

    results = sf.query_all(query)

    return [
        {
            'id': r['Id'],
            'name': r['Name'],
            'namespace': r.get('NamespacePrefix'),
            'is_valid': r.get('IsValid', True),
            'status': r.get('Status'),
        }
        for r in results['records']
    ]


def get_visualforce_pages(sf: Salesforce) -> list[dict]:
    """
    Get all Visualforce pages in the org.

    Returns:
        List of dicts with 'id', 'name', 'namespace', 'description'
    """
    query = """
        SELECT Id, Name, NamespacePrefix, Description
        FROM ApexPage
        ORDER BY Name
    """

    results = sf.query_all(query)

    return [
        {
            'id': r['Id'],
            'name': r['Name'],
            'namespace': r.get('NamespacePrefix'),
            'description': r.get('Description'),
        }
        for r in results['records']
    ]


def get_flows(sf: Salesforce, active_only: bool = True) -> list[dict]:
    """
    Get all Flows in the org.

    Args:
        sf: Salesforce connection
        active_only: If True, only return flows with an active version

    Returns:
        List of dicts with 'id', 'name', 'label', 'process_type', 'has_active_version'
    """
    if active_only:
        query = """
            SELECT Id, DeveloperName, MasterLabel, ProcessType, ActiveVersionId
            FROM FlowDefinition
            WHERE ActiveVersionId != null
            ORDER BY MasterLabel
        """
    else:
        query = """
            SELECT Id, DeveloperName, MasterLabel, ProcessType, ActiveVersionId
            FROM FlowDefinition
            ORDER BY MasterLabel
        """

    results = sf.query_all(query)

    return [
        {
            'id': r['Id'],
            'name': r['DeveloperName'],
            'label': r['MasterLabel'],
            'process_type': r.get('ProcessType'),
            'has_active_version': r.get('ActiveVersionId') is not None,
        }
        for r in results['records']
    ]


def get_custom_permissions(sf: Salesforce) -> list[dict]:
    """
    Get all Custom Permissions in the org.

    Returns:
        List of dicts with 'id', 'name', 'label', 'description', 'namespace'
    """
    query = """
        SELECT Id, DeveloperName, MasterLabel, Description, NamespacePrefix
        FROM CustomPermission
        ORDER BY MasterLabel
    """

    results = sf.query_all(query)

    return [
        {
            'id': r['Id'],
            'name': r['DeveloperName'],
            'label': r['MasterLabel'],
            'description': r.get('Description'),
            'namespace': r.get('NamespacePrefix'),
        }
        for r in results['records']
    ]


def get_tabs(sf: Salesforce) -> list[dict]:
    """
    Get all Tabs in the org (requires describe call).

    Returns:
        List of dicts with 'name', 'label', 'url'
    """
    # Use describe to get tabs
    tabs = sf.describe()['tabs'] if hasattr(sf.describe(), '__getitem__') else []

    # Alternative: use REST API
    try:
        response = sf.restful('tabs')
        return [
            {
                'name': t.get('name'),
                'label': t.get('label'),
                'url': t.get('url'),
            }
            for t in response
        ]
    except Exception:
        # Fallback: query TabDefinition (might not be available in all orgs)
        try:
            query = "SELECT DurableId, Name, Label FROM TabDefinition ORDER BY Label"
            results = sf.query_all(query)
            return [
                {
                    'name': r['Name'],
                    'label': r['Label'],
                    'durable_id': r['DurableId'],
                }
                for r in results['records']
            ]
        except Exception:
            return []


def get_permission_sets(
    sf: Salesforce,
    include_profile_owned: bool = False
) -> list[dict]:
    """
    Get all Permission Sets in the org.

    Args:
        sf: Salesforce connection
        include_profile_owned: If True, include PS owned by profiles

    Returns:
        List of dicts with 'id', 'name', 'label', 'is_profile_owned', 'type'
    """
    if include_profile_owned:
        query = """
            SELECT Id, Name, Label, Description, IsOwnedByProfile, Type
            FROM PermissionSet
            ORDER BY Label
        """
    else:
        query = """
            SELECT Id, Name, Label, Description, IsOwnedByProfile, Type
            FROM PermissionSet
            WHERE IsOwnedByProfile = false
            ORDER BY Label
        """

    results = sf.query_all(query)

    return [
        {
            'id': r['Id'],
            'name': r['Name'],
            'label': r['Label'],
            'description': r.get('Description'),
            'is_profile_owned': r['IsOwnedByProfile'],
            'type': r.get('Type'),  # Regular, Session, Group
        }
        for r in results['records']
    ]


def get_permission_set_groups(sf: Salesforce) -> list[dict]:
    """
    Get all Permission Set Groups in the org.

    Returns:
        List of dicts with 'id', 'name', 'label', 'status', 'description'
    """
    query = """
        SELECT Id, DeveloperName, MasterLabel, Status, Description
        FROM PermissionSetGroup
        ORDER BY MasterLabel
    """

    results = sf.query_all(query)

    return [
        {
            'id': r['Id'],
            'name': r['DeveloperName'],
            'label': r['MasterLabel'],
            'status': r.get('Status', 'Active'),
            'description': r.get('Description'),
        }
        for r in results['records']
    ]


def search_metadata(
    sf: Salesforce,
    search_term: str,
    metadata_types: list[str] = None
) -> dict:
    """
    Search across multiple metadata types for a term.

    Args:
        sf: Salesforce connection
        search_term: Term to search for
        metadata_types: List of types to search. Options:
                       'objects', 'fields', 'apex', 'vf', 'flows', 'custom_permissions'
                       If None, searches all types.

    Returns:
        Dict with results for each metadata type
    """
    if metadata_types is None:
        metadata_types = ['objects', 'apex', 'vf', 'flows', 'custom_permissions']

    results = {}
    search_lower = search_term.lower()

    if 'objects' in metadata_types:
        objects = get_available_objects(sf)
        results['objects'] = [
            o for o in objects
            if search_lower in o['api_name'].lower() or search_lower in o['label'].lower()
        ]

    if 'apex' in metadata_types:
        apex = get_apex_classes(sf)
        results['apex_classes'] = [
            a for a in apex
            if search_lower in a['name'].lower()
        ]

    if 'vf' in metadata_types:
        vf = get_visualforce_pages(sf)
        results['vf_pages'] = [
            v for v in vf
            if search_lower in v['name'].lower()
        ]

    if 'flows' in metadata_types:
        flows = get_flows(sf, active_only=False)
        results['flows'] = [
            f for f in flows
            if search_lower in f['name'].lower() or search_lower in f['label'].lower()
        ]

    if 'custom_permissions' in metadata_types:
        perms = get_custom_permissions(sf)
        results['custom_permissions'] = [
            p for p in perms
            if search_lower in p['name'].lower() or search_lower in p['label'].lower()
        ]

    return results


if __name__ == '__main__':
    from auth import get_sf_connection

    sf = get_sf_connection()

    print("📋 Available Objects (first 10):")
    objects = get_available_objects(sf)
    for obj in objects[:10]:
        custom_tag = " (custom)" if obj['is_custom'] else ""
        print(f"   • {obj['api_name']}: {obj['label']}{custom_tag}")

    print(f"\n📋 Apex Classes: {len(get_apex_classes(sf))}")
    print(f"📋 VF Pages: {len(get_visualforce_pages(sf))}")
    print(f"📋 Flows: {len(get_flows(sf))}")
    print(f"📋 Custom Permissions: {len(get_custom_permissions(sf))}")
