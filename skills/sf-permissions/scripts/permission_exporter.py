"""
Permission Set Exporter

Exports Permission Set configurations to CSV for documentation,
auditing, and analysis purposes.
"""

import csv
import json
from pathlib import Path
from typing import Optional
from simple_salesforce import Salesforce


def export_permission_set_to_csv(
    sf: Salesforce,
    ps_name: str,
    output_path: str
) -> str:
    """
    Export a Permission Set's full configuration to CSV.

    Args:
        sf: Salesforce connection
        ps_name: Permission Set Name or ID
        output_path: Path to output CSV file

    Returns:
        Path to the created CSV file

    Example:
        >>> path = export_permission_set_to_csv(sf, 'Sales_Manager', '/tmp/sales_manager.csv')
        >>> print(f"Exported to: {path}")
    """
    # Get PS info
    if ps_name.startswith('0PS'):
        ps_query = f"SELECT Id, Name, Label FROM PermissionSet WHERE Id = '{ps_name}'"
    else:
        ps_query = f"SELECT Id, Name, Label FROM PermissionSet WHERE Name = '{ps_name}'"

    ps_result = sf.query(ps_query)
    if not ps_result['records']:
        raise ValueError(f"Permission Set not found: {ps_name}")

    ps = ps_result['records'][0]
    ps_id = ps['Id']

    # Get all permission types
    object_perms = _get_object_permissions(sf, ps_id)
    field_perms = _get_field_permissions(sf, ps_id)
    setup_access = _get_setup_entity_access(sf, ps_id)
    system_perms = _get_system_permissions(sf, ps_id)

    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Name', 'Permission', 'Value', 'Notes'])

        # Write header info
        writer.writerow(['Info', 'Permission Set Name', '', ps['Name'], ''])
        writer.writerow(['Info', 'Permission Set Label', '', ps['Label'], ''])
        writer.writerow(['Info', 'Permission Set ID', '', ps['Id'], ''])
        writer.writerow([])  # Empty row as separator

        # System permissions
        for perm in system_perms:
            writer.writerow(['System', perm['name'], 'Enabled', 'true', perm.get('description', '')])

        if system_perms:
            writer.writerow([])

        # Object permissions
        for op in object_perms:
            obj_name = op['SobjectType']
            for perm_type, value in [
                ('Create', op['PermissionsCreate']),
                ('Read', op['PermissionsRead']),
                ('Edit', op['PermissionsEdit']),
                ('Delete', op['PermissionsDelete']),
                ('ViewAll', op['PermissionsViewAllRecords']),
                ('ModifyAll', op['PermissionsModifyAllRecords']),
            ]:
                if value:
                    writer.writerow(['Object', obj_name, perm_type, 'true', ''])

        if object_perms:
            writer.writerow([])

        # Field permissions
        for fp in field_perms:
            field_name = fp['Field']
            if fp['PermissionsRead']:
                writer.writerow(['Field', field_name, 'Read', 'true', ''])
            if fp['PermissionsEdit']:
                writer.writerow(['Field', field_name, 'Edit', 'true', ''])

        if field_perms:
            writer.writerow([])

        # Setup entity access
        for sea in setup_access:
            entity_type = sea['entity_type']
            entity_name = sea['entity_name']
            writer.writerow([entity_type, entity_name, 'Access', 'true', ''])

    return output_path


def export_permission_set_to_json(
    sf: Salesforce,
    ps_name: str,
    output_path: str
) -> str:
    """
    Export a Permission Set's full configuration to JSON.

    Args:
        sf: Salesforce connection
        ps_name: Permission Set Name or ID
        output_path: Path to output JSON file

    Returns:
        Path to the created JSON file
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

    # Build the export structure
    export_data = {
        'permission_set': {
            'id': ps['Id'],
            'name': ps['Name'],
            'label': ps['Label'],
            'description': ps.get('Description'),
        },
        'system_permissions': _get_system_permissions(sf, ps_id),
        'object_permissions': _get_object_permissions(sf, ps_id),
        'field_permissions': _get_field_permissions(sf, ps_id),
        'setup_entity_access': _get_setup_entity_access(sf, ps_id),
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)

    return output_path


def _get_object_permissions(sf: Salesforce, ps_id: str) -> list[dict]:
    """Get object permissions for a Permission Set."""
    query = f"""
        SELECT SobjectType, PermissionsCreate, PermissionsRead, PermissionsEdit,
               PermissionsDelete, PermissionsViewAllRecords, PermissionsModifyAllRecords
        FROM ObjectPermissions
        WHERE ParentId = '{ps_id}'
        ORDER BY SobjectType
    """
    results = sf.query_all(query)
    return results['records']


def _get_field_permissions(sf: Salesforce, ps_id: str) -> list[dict]:
    """Get field permissions for a Permission Set."""
    query = f"""
        SELECT Field, PermissionsRead, PermissionsEdit
        FROM FieldPermissions
        WHERE ParentId = '{ps_id}'
        ORDER BY Field
    """
    results = sf.query_all(query)
    return results['records']


def _get_setup_entity_access(sf: Salesforce, ps_id: str) -> list[dict]:
    """Get setup entity access (Apex, VF, Flow, Custom Permissions) for a PS."""
    query = f"""
        SELECT SetupEntityType, SetupEntityId
        FROM SetupEntityAccess
        WHERE ParentId = '{ps_id}'
    """
    results = sf.query_all(query)

    # Resolve entity names
    entities = []
    entity_ids_by_type = {}

    for r in results['records']:
        entity_type = r['SetupEntityType']
        entity_id = r['SetupEntityId']

        if entity_type not in entity_ids_by_type:
            entity_ids_by_type[entity_type] = []
        entity_ids_by_type[entity_type].append(entity_id)

    # Resolve names for each type
    type_queries = {
        'ApexClass': "SELECT Id, Name FROM ApexClass WHERE Id IN ('{ids}')",
        'ApexPage': "SELECT Id, Name FROM ApexPage WHERE Id IN ('{ids}')",
        'CustomPermission': "SELECT Id, DeveloperName FROM CustomPermission WHERE Id IN ('{ids}')",
    }

    entity_names = {}
    for entity_type, ids in entity_ids_by_type.items():
        if entity_type in type_queries and ids:
            ids_str = "', '".join(ids)
            query = type_queries[entity_type].replace('{ids}', ids_str)
            try:
                names_result = sf.query_all(query)
                for n in names_result['records']:
                    name_field = 'DeveloperName' if entity_type == 'CustomPermission' else 'Name'
                    entity_names[n['Id']] = n.get(name_field, n['Id'])
            except Exception:
                pass

    for r in results['records']:
        entity_id = r['SetupEntityId']
        entities.append({
            'entity_type': r['SetupEntityType'],
            'entity_id': entity_id,
            'entity_name': entity_names.get(entity_id, entity_id),
        })

    return entities


def _get_system_permissions(sf: Salesforce, ps_id: str) -> list[dict]:
    """Get enabled system permissions for a Permission Set."""
    # Query the PS with all permission fields
    # Note: This is a subset of common system permissions
    system_perm_fields = [
        ('PermissionsApiEnabled', 'API Enabled'),
        ('PermissionsViewSetup', 'View Setup'),
        ('PermissionsModifyAllData', 'Modify All Data'),
        ('PermissionsViewAllData', 'View All Data'),
        ('PermissionsManageUsers', 'Manage Users'),
        ('PermissionsResetPasswords', 'Reset Passwords'),
        ('PermissionsRunReports', 'Run Reports'),
        ('PermissionsExportReport', 'Export Reports'),
        ('PermissionsEditBillingInfo', 'Edit Billing Info'),
        ('PermissionsManageCategories', 'Manage Categories'),
        ('PermissionsConvertLeads', 'Convert Leads'),
        ('PermissionsCreateMultiforce', 'Create Multiforce'),
        ('PermissionsEditOppLineItemUnitPrice', 'Edit Opportunity Line Item Unit Price'),
        ('PermissionsEditReadonlyFields', 'Edit Read Only Fields'),
        ('PermissionsViewAllUsers', 'View All Users'),
        ('PermissionsAssignTopics', 'Assign Topics'),
        ('PermissionsAuthorApex', 'Author Apex'),
        ('PermissionsBulkApiHardDelete', 'Bulk API Hard Delete'),
        ('PermissionsCanUseNewDashboardBuilder', 'Use New Dashboard Builder'),
        ('PermissionsChatterInternalUser', 'Chatter Internal User'),
        ('PermissionsEditMyDashboards', 'Edit My Dashboards'),
        ('PermissionsEditMyReports', 'Edit My Reports'),
        ('PermissionsFlowUFLRequired', 'Flow User Feature License Required'),
        ('PermissionsImportLeads', 'Import Leads'),
        ('PermissionsInstallPackaging', 'Install Packages'),
        ('PermissionsLightningConsoleAllowedForUser', 'Lightning Console User'),
        ('PermissionsManageCustomReportTypes', 'Manage Custom Report Types'),
        ('PermissionsManageDashboards', 'Manage Dashboards'),
        ('PermissionsManageReportsInPubFolders', 'Manage Reports in Public Folders'),
        ('PermissionsMassInlineEdit', 'Mass Inline Edit'),
        ('PermissionsModifyMetadata', 'Modify Metadata'),
        ('PermissionsRunFlow', 'Run Flows'),
        ('PermissionsScheduleReports', 'Schedule Reports'),
        ('PermissionsSubmitMacrosAllowed', 'Submit Macros'),
        ('PermissionsTransferAnyEntity', 'Transfer Any Entity'),
        ('PermissionsTransferAnyLead', 'Transfer Any Lead'),
        ('PermissionsViewDataCategories', 'View Data Categories'),
        ('PermissionsViewMyTeamsDashboards', 'View My Teams Dashboards'),
    ]

    field_names = [f[0] for f in system_perm_fields]
    field_str = ', '.join(field_names)

    query = f"SELECT {field_str} FROM PermissionSet WHERE Id = '{ps_id}'"

    try:
        result = sf.query(query)
        if not result['records']:
            return []

        ps = result['records'][0]
        enabled = []

        for field_name, description in system_perm_fields:
            if ps.get(field_name, False):
                enabled.append({
                    'name': field_name.replace('Permissions', ''),
                    'description': description,
                })

        return enabled

    except Exception:
        # If query fails (maybe field doesn't exist), return empty
        return []


def compare_permission_sets(
    sf: Salesforce,
    ps1_name: str,
    ps2_name: str,
    output_path: Optional[str] = None
) -> dict:
    """
    Compare two Permission Sets and show differences.

    Args:
        sf: Salesforce connection
        ps1_name: First Permission Set Name or ID
        ps2_name: Second Permission Set Name or ID
        output_path: Optional path to write comparison CSV

    Returns:
        Dict with 'ps1_only', 'ps2_only', 'both' permissions
    """
    # Get both PS configurations
    ps1_data = _get_full_permissions(sf, ps1_name)
    ps2_data = _get_full_permissions(sf, ps2_name)

    # Compare
    ps1_set = set(ps1_data['all_permissions'])
    ps2_set = set(ps2_data['all_permissions'])

    comparison = {
        'ps1': {
            'name': ps1_data['name'],
            'label': ps1_data['label'],
        },
        'ps2': {
            'name': ps2_data['name'],
            'label': ps2_data['label'],
        },
        'ps1_only': sorted(list(ps1_set - ps2_set)),
        'ps2_only': sorted(list(ps2_set - ps1_set)),
        'both': sorted(list(ps1_set & ps2_set)),
    }

    if output_path:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Permission', ps1_data['name'], ps2_data['name'], 'Status'])

            for perm in comparison['both']:
                writer.writerow([perm, 'Yes', 'Yes', 'Both'])
            for perm in comparison['ps1_only']:
                writer.writerow([perm, 'Yes', 'No', f"Only in {ps1_data['name']}"])
            for perm in comparison['ps2_only']:
                writer.writerow([perm, 'No', 'Yes', f"Only in {ps2_data['name']}"])

    return comparison


def _get_full_permissions(sf: Salesforce, ps_name: str) -> dict:
    """Get all permissions as a set of strings for comparison."""
    # Get PS info
    if ps_name.startswith('0PS'):
        ps_query = f"SELECT Id, Name, Label FROM PermissionSet WHERE Id = '{ps_name}'"
    else:
        ps_query = f"SELECT Id, Name, Label FROM PermissionSet WHERE Name = '{ps_name}'"

    ps_result = sf.query(ps_query)
    if not ps_result['records']:
        raise ValueError(f"Permission Set not found: {ps_name}")

    ps = ps_result['records'][0]
    ps_id = ps['Id']

    all_permissions = []

    # Object permissions
    for op in _get_object_permissions(sf, ps_id):
        obj = op['SobjectType']
        if op['PermissionsCreate']:
            all_permissions.append(f"Object:{obj}:Create")
        if op['PermissionsRead']:
            all_permissions.append(f"Object:{obj}:Read")
        if op['PermissionsEdit']:
            all_permissions.append(f"Object:{obj}:Edit")
        if op['PermissionsDelete']:
            all_permissions.append(f"Object:{obj}:Delete")
        if op['PermissionsViewAllRecords']:
            all_permissions.append(f"Object:{obj}:ViewAll")
        if op['PermissionsModifyAllRecords']:
            all_permissions.append(f"Object:{obj}:ModifyAll")

    # Field permissions
    for fp in _get_field_permissions(sf, ps_id):
        field = fp['Field']
        if fp['PermissionsRead']:
            all_permissions.append(f"Field:{field}:Read")
        if fp['PermissionsEdit']:
            all_permissions.append(f"Field:{field}:Edit")

    # Setup entity access
    for sea in _get_setup_entity_access(sf, ps_id):
        all_permissions.append(f"{sea['entity_type']}:{sea['entity_name']}:Access")

    # System permissions
    for sp in _get_system_permissions(sf, ps_id):
        all_permissions.append(f"System:{sp['name']}")

    return {
        'name': ps['Name'],
        'label': ps['Label'],
        'all_permissions': all_permissions,
    }


if __name__ == '__main__':
    import sys
    from auth import get_sf_connection

    sf = get_sf_connection()

    if len(sys.argv) < 2:
        print("Usage: python permission_exporter.py <PermissionSetName> [output.csv]")
        sys.exit(1)

    ps_name = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else f'/tmp/{ps_name}.csv'

    print(f"Exporting {ps_name} to {output_path}...")
    result_path = export_permission_set_to_csv(sf, ps_name, output_path)
    print(f"✅ Exported to: {result_path}")
