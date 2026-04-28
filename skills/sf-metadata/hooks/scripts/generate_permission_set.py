#!/usr/bin/env python3
"""
Permission Set Generator for sf-metadata plugin.

Generates Permission Set XML for custom objects, automatically including
eligible custom fields and filtering out categories Salesforce commonly
excludes from Permission Set metadata in modern API versions:
- Universally required fields
- Name fields / always-visible fields
- Master-Detail fields

Usage:
    python3 generate_permission_set.py <object_directory> [--output <path>]

Example:
    python3 generate_permission_set.py force-app/main/default/objects/Customer_Feedback__c

Output:
    force-app/main/default/permissionsets/Customer_Feedback_Access.permissionset-meta.xml
"""

import os
import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple


# XML Namespace for Salesforce metadata
SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"
NS = {"sf": SF_NAMESPACE}


def find_element(root, tag_name: str, ns: dict) -> ET.Element:
    """Find element with or without namespace prefix."""
    # Try with namespace first
    elem = root.find(f'.//sf:{tag_name}', ns)
    if elem is not None:
        return elem
    # Try without namespace (default namespace)
    elem = root.find(f'.//{{{SF_NAMESPACE}}}{tag_name}')
    if elem is not None:
        return elem
    # Try plain tag
    elem = root.find(f'.//{tag_name}')
    return elem


def parse_field_metadata(field_path: str) -> Dict:
    """
    Parse a field metadata XML file and extract relevant information.

    Returns dict with:
        - api_name: Field API name
        - required: Whether field is required
        - type: Field type (Text, Number, Picklist, etc.)
        - is_formula: Whether field is a formula
        - is_rollup: Whether field is a roll-up summary
        - is_master_detail: Whether field is a master-detail relationship
    """
    try:
        tree = ET.parse(field_path)
        root = tree.getroot()

        # Handle namespace
        ns = {"sf": SF_NAMESPACE}

        # Extract field name from filename
        filename = os.path.basename(field_path)
        api_name = filename.replace('.field-meta.xml', '')

        # Get field type
        field_type_elem = find_element(root, 'type', ns)
        field_type = field_type_elem.text if field_type_elem is not None else 'Unknown'

        # Check if required
        required_elem = find_element(root, 'required', ns)
        is_required = required_elem is not None and required_elem.text and required_elem.text.lower() == 'true'

        # Check for formula
        formula_elem = find_element(root, 'formula', ns)
        is_formula = formula_elem is not None and formula_elem.text and len(formula_elem.text.strip()) > 0

        # Check for roll-up summary
        is_rollup = field_type == 'Summary'

        # Check for master-detail
        is_master_detail = field_type == 'MasterDetail'

        return {
            'api_name': api_name,
            'required': is_required,
            'type': field_type,
            'is_formula': is_formula,
            'is_rollup': is_rollup,
            'is_master_detail': is_master_detail,
            'path': field_path
        }

    except ET.ParseError as e:
        print(f"  ⚠️ Warning: Could not parse {field_path}: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️ Warning: Error processing {field_path}: {e}")
        return None


def get_object_name(object_dir: str) -> str:
    """Extract object API name from directory path."""
    return os.path.basename(object_dir.rstrip('/'))


def scan_fields(object_dir: str) -> List[Dict]:
    """Scan all field metadata files in an object directory."""
    fields_dir = os.path.join(object_dir, 'fields')
    fields = []

    if not os.path.exists(fields_dir):
        print(f"  ℹ️ No fields directory found at {fields_dir}")
        return fields

    for filename in os.listdir(fields_dir):
        if filename.endswith('.field-meta.xml'):
            field_path = os.path.join(fields_dir, filename)
            field_info = parse_field_metadata(field_path)
            if field_info:
                fields.append(field_info)

    return fields


def filter_fields_for_permission_set(fields: List[Dict], object_name: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter fields to determine which should be included in the generated Permission Set.

    Returns:
        (included_fields, excluded_fields)
    """
    included = []
    excluded = []

    for field in fields:
        exclude_reason = None

        # Rule 1: Universally required fields are commonly excluded from
        # Permission Set metadata in modern API versions.
        if field['required']:
            exclude_reason = "Required field (commonly excluded from Permission Set metadata)"

        # Rule 2: Master-Detail fields are commonly treated as parent-controlled.
        elif field['is_master_detail']:
            exclude_reason = "Master-Detail field (commonly parent-controlled / excluded)"

        # Rule 3: Name field is always visible
        elif field['api_name'].lower() == 'name':
            exclude_reason = "Name field (always visible)"

        if exclude_reason:
            field['exclude_reason'] = exclude_reason
            excluded.append(field)
        else:
            included.append(field)

    return included, excluded


def generate_permission_set_xml(object_name: str, included_fields: List[Dict]) -> str:
    """Generate Permission Set XML content."""

    # Create label from object name (remove __c, add spaces)
    label_name = object_name.replace('__c', '').replace('_', ' ')
    perm_set_name = object_name.replace('__c', '') + '_Access'

    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Auto-generated: Grants full access to {label_name} object and eligible custom fields</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>{label_name} Access</label>

    <!-- Object Permissions: Full CRUD access -->
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>{object_name}</object>
        <viewAllRecords>true</viewAllRecords>
    </objectPermissions>
'''

    # Add field permissions
    if included_fields:
        xml_content += '''
    <!-- Field Permissions -->
    <!-- NOTE: Some field categories are excluded because Salesforce commonly omits them from Permission Set metadata -->
    <!-- NOTE: Formula/Roll-Up fields have editable=false -->
'''
        for field in sorted(included_fields, key=lambda x: x['api_name']):
            # Formula and Roll-Up fields can only be readable
            editable = "false" if (field['is_formula'] or field['is_rollup']) else "true"

            xml_content += f'''    <fieldPermissions>
        <editable>{editable}</editable>
        <field>{object_name}.{field['api_name']}</field>
        <readable>true</readable>
    </fieldPermissions>
'''

    xml_content += '''</PermissionSet>
'''

    return xml_content


def main():
    parser = argparse.ArgumentParser(
        description='Generate Permission Set for a custom object using eligible-field filtering'
    )
    parser.add_argument(
        'object_dir',
        help='Path to object directory (e.g., force-app/main/default/objects/MyObject__c)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output path for Permission Set file (default: auto-generated in permissionsets/)',
        default=None
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print XML to stdout instead of writing to file'
    )

    args = parser.parse_args()

    object_dir = args.object_dir.rstrip('/')

    # Validate object directory exists
    if not os.path.exists(object_dir):
        print(f"❌ Error: Object directory not found: {object_dir}")
        sys.exit(1)

    object_name = get_object_name(object_dir)
    print(f"\n🔧 Generating Permission Set for: {object_name}")
    print("=" * 60)

    # Scan fields
    print("\n📁 Scanning fields...")
    fields = scan_fields(object_dir)
    print(f"   Found {len(fields)} custom fields")

    # Filter fields
    print("\n🔍 Filtering fields for Permission Set...")
    included, excluded = filter_fields_for_permission_set(fields, object_name)

    # Report excluded fields
    if excluded:
        print(f"\n⚠️ Excluded fields ({len(excluded)}):")
        for field in excluded:
            print(f"   ❌ {field['api_name']}: {field['exclude_reason']}")

    # Report included fields
    if included:
        print(f"\n✅ Included fields ({len(included)}):")
        for field in included:
            field_type = "read-only" if (field['is_formula'] or field['is_rollup']) else "read/write"
            print(f"   ✓ {field['api_name']} ({field_type})")
    else:
        print("\n⚠️ No fields to include in Permission Set")

    # Generate XML
    xml_content = generate_permission_set_xml(object_name, included)

    if args.dry_run:
        print("\n📄 Generated XML (dry-run):")
        print("-" * 60)
        print(xml_content)
        return

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default: create in permissionsets directory at same level as objects
        base_dir = os.path.dirname(os.path.dirname(object_dir))  # Go up from objects/
        perm_sets_dir = os.path.join(base_dir, 'permissionsets')
        perm_set_name = object_name.replace('__c', '') + '_Access'
        output_path = os.path.join(perm_sets_dir, f"{perm_set_name}.permissionset-meta.xml")

    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write file
    with open(output_path, 'w') as f:
        f.write(xml_content)

    print(f"\n✅ Permission Set generated successfully!")
    print(f"   📁 Location: {output_path}")
    print(f"\n💡 Next steps:")
    print(f"   1. Deploy: sf project deploy start --source-dir {os.path.dirname(output_path)} --target-org <alias>")
    print(f"   2. Assign: sf org assign permset --name {object_name.replace('__c', '')}_Access --target-org <alias>")


if __name__ == "__main__":
    main()
