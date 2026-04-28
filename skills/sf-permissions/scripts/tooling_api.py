"""
Tooling API Integration

Provides access to metadata not available through standard SOQL,
such as tab visibility settings and certain system permissions.

The Tooling API is a REST-based API that provides access to the
metadata in a Salesforce org, similar to the Metadata API but
with a REST interface.
"""

from typing import Optional
from simple_salesforce import Salesforce


def tooling_query(sf: Salesforce, query: str) -> dict:
    """
    Execute a Tooling API query.

    The Tooling API supports SOQL queries against metadata objects
    that aren't available in the standard API.

    Args:
        sf: Salesforce connection
        query: SOQL query string

    Returns:
        Query result dict with 'records', 'totalSize', 'done'

    Example:
        >>> results = tooling_query(sf, "SELECT Id, Name FROM ApexClass LIMIT 5")
        >>> for record in results['records']:
        ...     print(record['Name'])
    """
    # simple_salesforce provides toolingexecute for Tooling API
    # But we need to properly encode the query
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    result = sf.toolingexecute(f"query/?q={encoded_query}")
    return result


def get_tab_settings(sf: Salesforce, ps_id: str) -> list[dict]:
    """
    Get tab visibility settings for a Permission Set.

    Tab visibility controls whether a tab appears in the app launcher
    and navigation for users with this Permission Set.

    Args:
        sf: Salesforce connection
        ps_id: Permission Set ID

    Returns:
        List of dicts with 'name', 'visibility'
        Visibility values: 'DefaultOn', 'DefaultOff', 'Hidden'

    Example:
        >>> tabs = get_tab_settings(sf, '0PS...')
        >>> for tab in tabs:
        ...     print(f"{tab['name']}: {tab['visibility']}")
    """
    query = f"""
        SELECT Name, Visibility
        FROM PermissionSetTabSetting
        WHERE ParentId = '{ps_id}'
    """

    try:
        result = tooling_query(sf, query)
        return [
            {
                'name': r.get('Name'),
                'visibility': r.get('Visibility'),
            }
            for r in result.get('records', [])
        ]
    except Exception as e:
        # Tooling API might not be available or query might fail
        return []


def get_record_type_settings(sf: Salesforce, ps_id: str) -> list[dict]:
    """
    Get record type visibility settings for a Permission Set.

    Args:
        sf: Salesforce connection
        ps_id: Permission Set ID

    Returns:
        List of dicts with 'record_type', 'sobject', 'is_visible', 'is_default'
    """
    # Record type settings are available via standard API too
    query = f"""
        SELECT RecordTypeId, RecordType.Name, RecordType.SobjectType,
               RecordType.DeveloperName
        FROM RecordTypePermissions
        WHERE ParentId = '{ps_id}'
    """

    try:
        # Try standard API first
        result = sf.query_all(query)
        # Note: This query structure might not work as RecordTypePermissions
        # might need Tooling API
        return [
            {
                'record_type_id': r['RecordTypeId'],
                'name': r['RecordType']['Name'] if r.get('RecordType') else None,
                'sobject': r['RecordType']['SobjectType'] if r.get('RecordType') else None,
            }
            for r in result['records']
        ]
    except Exception:
        # Fall back to empty if not available
        return []


def get_application_visibility(sf: Salesforce, ps_id: str) -> list[dict]:
    """
    Get application (App) visibility settings for a Permission Set.

    Args:
        sf: Salesforce connection
        ps_id: Permission Set ID

    Returns:
        List of dicts with 'app_name', 'is_visible', 'is_default'
    """
    query = f"""
        SELECT ApplicationId, IsVisible
        FROM PermissionSetApplicationVisibility
        WHERE ParentId = '{ps_id}'
    """

    try:
        # This might require Tooling API
        result = tooling_query(sf, query)
        return [
            {
                'app_id': r.get('ApplicationId'),
                'is_visible': r.get('IsVisible'),
            }
            for r in result.get('records', [])
        ]
    except Exception:
        return []


def get_system_permissions_metadata(sf: Salesforce) -> list[dict]:
    """
    Get metadata about all available system permissions.

    This uses the Tooling API to describe the PermissionSet object
    and extract information about permission fields.

    Returns:
        List of dicts with 'name', 'label', 'description'
    """
    try:
        # Use describe on PermissionSet to get all fields
        describe = sf.PermissionSet.describe()

        permissions = []
        for field in describe.get('fields', []):
            name = field.get('name', '')
            if name.startswith('Permissions') and field.get('type') == 'boolean':
                permissions.append({
                    'api_name': name,
                    'label': field.get('label', name),
                    'description': field.get('inlineHelpText', ''),
                })

        return permissions
    except Exception:
        return []


def get_user_license_info(sf: Salesforce) -> list[dict]:
    """
    Get information about User Licenses in the org.

    Useful for understanding which licenses support which permissions.

    Returns:
        List of dicts with license info
    """
    query = """
        SELECT Id, Name, TotalLicenses, UsedLicenses, Status
        FROM UserLicense
        ORDER BY Name
    """

    result = sf.query_all(query)
    return [
        {
            'id': r['Id'],
            'name': r['Name'],
            'total': r['TotalLicenses'],
            'used': r['UsedLicenses'],
            'status': r['Status'],
        }
        for r in result['records']
    ]


def get_permission_set_license_info(sf: Salesforce) -> list[dict]:
    """
    Get information about Permission Set Licenses in the org.

    Permission Set Licenses are required for certain features
    (like Einstein, Field Service, etc.).

    Returns:
        List of dicts with license info
    """
    query = """
        SELECT Id, DeveloperName, MasterLabel, TotalLicenses, UsedLicenses,
               PermissionSetLicenseKey, Status
        FROM PermissionSetLicense
        ORDER BY MasterLabel
    """

    try:
        result = sf.query_all(query)
        return [
            {
                'id': r['Id'],
                'name': r['DeveloperName'],
                'label': r['MasterLabel'],
                'total': r['TotalLicenses'],
                'used': r['UsedLicenses'],
                'key': r.get('PermissionSetLicenseKey'),
                'status': r['Status'],
            }
            for r in result['records']
        ]
    except Exception:
        return []


def get_profile_metadata(sf: Salesforce, profile_name: str) -> dict:
    """
    Get metadata about a Profile using Tooling API.

    Args:
        sf: Salesforce connection
        profile_name: Profile name

    Returns:
        Dict with profile metadata
    """
    # Get Profile ID
    profile_query = f"SELECT Id, Name FROM Profile WHERE Name = '{profile_name}'"
    profile_result = sf.query(profile_query)

    if not profile_result['records']:
        raise ValueError(f"Profile not found: {profile_name}")

    profile_id = profile_result['records'][0]['Id']

    # Get the Permission Set that backs this Profile
    ps_query = f"""
        SELECT Id, Name, Label
        FROM PermissionSet
        WHERE ProfileId = '{profile_id}'
    """
    ps_result = sf.query(ps_query)

    if not ps_result['records']:
        return {'profile_name': profile_name, 'error': 'No backing Permission Set found'}

    ps = ps_result['records'][0]

    return {
        'profile_name': profile_name,
        'profile_id': profile_id,
        'backing_permission_set_id': ps['Id'],
        'backing_permission_set_name': ps['Name'],
    }


def describe_sobject_permissions(sf: Salesforce, sobject_name: str) -> dict:
    """
    Get information about what permissions are possible for an SObject.

    Args:
        sf: Salesforce connection
        sobject_name: API name of the object

    Returns:
        Dict with object permission capabilities
    """
    try:
        describe = getattr(sf, sobject_name).describe()
        return {
            'name': describe.get('name'),
            'label': describe.get('label'),
            'createable': describe.get('createable'),
            'deletable': describe.get('deletable'),
            'updateable': describe.get('updateable'),
            'queryable': describe.get('queryable'),
            'searchable': describe.get('searchable'),
            'custom': describe.get('custom'),
            'fields': [
                {
                    'name': f.get('name'),
                    'label': f.get('label'),
                    'type': f.get('type'),
                    'updateable': f.get('updateable'),
                    'createable': f.get('createable'),
                    'nillable': f.get('nillable'),
                    'custom': f.get('custom'),
                }
                for f in describe.get('fields', [])
            ]
        }
    except Exception as e:
        raise ValueError(f"Cannot describe object {sobject_name}: {e}")


if __name__ == '__main__':
    from auth import get_sf_connection

    sf = get_sf_connection()

    print("📋 User Licenses:")
    licenses = get_user_license_info(sf)
    for lic in licenses[:5]:
        print(f"   • {lic['name']}: {lic['used']}/{lic['total']}")

    print("\n📋 Permission Set Licenses:")
    ps_licenses = get_permission_set_license_info(sf)
    for lic in ps_licenses[:5]:
        print(f"   • {lic['label']}: {lic['used']}/{lic['total']}")

    print("\n📋 Available System Permissions (sample):")
    sys_perms = get_system_permissions_metadata(sf)
    for perm in sys_perms[:10]:
        print(f"   • {perm['label']}")
