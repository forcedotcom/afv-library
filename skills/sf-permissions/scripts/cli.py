#!/usr/bin/env python3
"""
sf-permissions CLI

Main command-line interface for the sf-permissions skill.
Provides commands for hierarchy viewing, permission detection,
user analysis, and exporting.

Usage:
    python cli.py hierarchy [--target-org ALIAS] [--format ascii|mermaid]
    python cli.py detect object Account --access delete
    python cli.py detect field Account.AnnualRevenue --access edit
    python cli.py detect apex MyApexClass
    python cli.py detect custom Can_Approve_Expenses
    python cli.py user john.smith@company.com
    python cli.py export Sales_Manager --output /tmp/sales_manager.csv
"""

import argparse
import sys
from typing import Optional

# Import our modules
from auth import get_sf_connection
from hierarchy_viewer import get_org_permission_hierarchy, get_permission_set_details, get_psg_details
from permission_detector import (
    detect_object_permission,
    detect_field_permission,
    detect_apex_class_permission,
    detect_vf_page_permission,
    detect_flow_permission,
    detect_custom_permission,
    detect_system_permission,
)
from user_analyzer import analyze_user_permissions, get_users_with_permission_set
from permission_exporter import export_permission_set_to_csv, export_permission_set_to_json
from renderers.ascii_tree import (
    render_hierarchy_tree,
    render_user_tree,
    render_detection_table,
    render_summary_panel,
)
from renderers.mermaid import render_hierarchy_mermaid, render_user_mermaid


def cmd_hierarchy(args):
    """Display org permission hierarchy."""
    sf = get_sf_connection(args.target_org)

    print("🔍 Building permission hierarchy...")
    hierarchy = get_org_permission_hierarchy(sf)

    if args.format == 'mermaid':
        output = render_hierarchy_mermaid(hierarchy)
        print(output)
    else:
        render_hierarchy_tree(hierarchy)


def cmd_detect(args):
    """Detect who has access to something."""
    sf = get_sf_connection(args.target_org)

    perm_type = args.type
    name = args.name

    # Parse access types if provided
    access_types = None
    if hasattr(args, 'access') and args.access:
        access_types = [a.strip() for a in args.access.split(',')]

    print(f"🔍 Detecting {perm_type} permissions for: {name}")

    results = []

    if perm_type == 'object':
        results = detect_object_permission(sf, name, access_types)
    elif perm_type == 'field':
        # Field name should be in format Object.Field
        if '.' in name:
            obj, field = name.rsplit('.', 1)
        else:
            print("❌ Field permission requires format: Object.Field")
            return 1
        results = detect_field_permission(sf, obj, field, access_types)
    elif perm_type == 'apex':
        results = detect_apex_class_permission(sf, name)
    elif perm_type == 'vf':
        results = detect_vf_page_permission(sf, name)
    elif perm_type == 'flow':
        results = detect_flow_permission(sf, name)
    elif perm_type == 'custom':
        results = detect_custom_permission(sf, name)
    elif perm_type == 'system':
        results = detect_system_permission(sf, name)
    else:
        print(f"❌ Unknown permission type: {perm_type}")
        return 1

    if not results:
        print(f"\n⚠️  No Permission Sets found with {perm_type} access to {name}")
        return 0

    # Build query description
    query_desc = f"{perm_type.title()} access to {name}"
    if access_types:
        query_desc += f" ({', '.join(access_types)})"

    render_detection_table(results, query_desc)
    return 0


def cmd_user(args):
    """Analyze user permissions."""
    sf = get_sf_connection(args.target_org)

    print(f"🔍 Analyzing permissions for: {args.user}")
    analysis = analyze_user_permissions(sf, args.user)

    if args.format == 'mermaid':
        output = render_user_mermaid(analysis)
        print(output)
    else:
        render_user_tree(analysis)


def cmd_export(args):
    """Export Permission Set to file."""
    sf = get_sf_connection(args.target_org)

    ps_name = args.permission_set
    output_path = args.output

    # Determine format from extension or argument
    if output_path.endswith('.json'):
        export_format = 'json'
    else:
        export_format = 'csv'

    print(f"📤 Exporting {ps_name} to {output_path}...")

    if export_format == 'json':
        result_path = export_permission_set_to_json(sf, ps_name, output_path)
    else:
        result_path = export_permission_set_to_csv(sf, ps_name, output_path)

    print(f"✅ Exported to: {result_path}")


def cmd_ps_details(args):
    """Show details of a Permission Set."""
    sf = get_sf_connection(args.target_org)

    print(f"🔍 Getting details for Permission Set: {args.name}")
    details = get_permission_set_details(sf, args.name)

    render_summary_panel(
        title=f"Permission Set: {details['info']['label']}",
        data={
            'Name': details['info']['name'],
            'ID': details['info']['id'],
            'Description': details['info'].get('description') or '(none)',
            'Object Permissions': len(details['object_permissions']),
            'Field Permissions': len(details['field_permissions']),
            'Setup Entity Access': len(details['setup_entity_access']),
        }
    )


def cmd_psg_details(args):
    """Show details of a Permission Set Group."""
    sf = get_sf_connection(args.target_org)

    print(f"🔍 Getting details for Permission Set Group: {args.name}")
    details = get_psg_details(sf, args.name)

    render_summary_panel(
        title=f"Permission Set Group: {details['info']['master_label']}",
        data={
            'Developer Name': details['info']['developer_name'],
            'ID': details['info']['id'],
            'Status': details['info']['status'],
            'Description': details['info'].get('description') or '(none)',
            'Permission Sets': len(details['permission_sets']),
            'Assigned Users': len(details['assigned_users']),
        }
    )

    # Show component PS
    if details['permission_sets']:
        print("\n📋 Component Permission Sets:")
        for ps in details['permission_sets']:
            print(f"   • {ps['label']} ({ps['name']})")

    # Show users (first 10)
    if details['assigned_users']:
        print(f"\n👥 Assigned Users ({len(details['assigned_users'])} shown):")
        for user in details['assigned_users'][:10]:
            status = "✅" if user['is_active'] else "❌"
            print(f"   {status} {user['name']} ({user['username']})")


def cmd_users_with_ps(args):
    """List users with a specific Permission Set."""
    sf = get_sf_connection(args.target_org)

    print(f"🔍 Finding users with Permission Set: {args.permission_set}")
    users = get_users_with_permission_set(sf, args.permission_set)

    if not users:
        print(f"\n⚠️  No users found with Permission Set: {args.permission_set}")
        return

    print(f"\n👥 Users with {args.permission_set} ({len(users)} total):")
    for user in users:
        status = "✅" if user.is_active else "❌"
        profile = f" [{user.profile_name}]" if user.profile_name else ""
        print(f"   {status} {user.name} ({user.username}){profile}")


def main():
    parser = argparse.ArgumentParser(
        description='sf-permissions: Salesforce Permission Set Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s hierarchy                           # Show org permission hierarchy
  %(prog)s detect object Account --access delete   # Who can delete Accounts?
  %(prog)s detect apex MyApexClass             # Who has access to an Apex class?
  %(prog)s user john@company.com               # What permissions does John have?
  %(prog)s export Sales_Manager -o /tmp/sm.csv # Export PS to CSV
        """
    )

    parser.add_argument(
        '--target-org', '-o',
        help='Target org alias or username (default: current default org)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Hierarchy command
    hierarchy_parser = subparsers.add_parser(
        'hierarchy',
        help='Display org permission hierarchy'
    )
    hierarchy_parser.add_argument(
        '--format', '-f',
        choices=['ascii', 'mermaid'],
        default='ascii',
        help='Output format (default: ascii)'
    )
    hierarchy_parser.set_defaults(func=cmd_hierarchy)

    # Detect command
    detect_parser = subparsers.add_parser(
        'detect',
        help='Detect who has access to something'
    )
    detect_parser.add_argument(
        'type',
        choices=['object', 'field', 'apex', 'vf', 'flow', 'custom', 'system'],
        help='Type of permission to detect'
    )
    detect_parser.add_argument(
        'name',
        help='Name of object/field/class/permission (for field: Object.Field)'
    )
    detect_parser.add_argument(
        '--access', '-a',
        help='Access types to check, comma-separated (e.g., create,read,edit,delete)'
    )
    detect_parser.set_defaults(func=cmd_detect)

    # User command
    user_parser = subparsers.add_parser(
        'user',
        help='Analyze user permissions'
    )
    user_parser.add_argument(
        'user',
        help='User ID or username'
    )
    user_parser.add_argument(
        '--format', '-f',
        choices=['ascii', 'mermaid'],
        default='ascii',
        help='Output format (default: ascii)'
    )
    user_parser.set_defaults(func=cmd_user)

    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export Permission Set to file'
    )
    export_parser.add_argument(
        'permission_set',
        help='Permission Set name or ID'
    )
    export_parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output file path (.csv or .json)'
    )
    export_parser.set_defaults(func=cmd_export)

    # PS details command
    ps_parser = subparsers.add_parser(
        'ps',
        help='Show Permission Set details'
    )
    ps_parser.add_argument(
        'name',
        help='Permission Set name or ID'
    )
    ps_parser.set_defaults(func=cmd_ps_details)

    # PSG details command
    psg_parser = subparsers.add_parser(
        'psg',
        help='Show Permission Set Group details'
    )
    psg_parser.add_argument(
        'name',
        help='Permission Set Group name or ID'
    )
    psg_parser.set_defaults(func=cmd_psg_details)

    # Users with PS command
    users_parser = subparsers.add_parser(
        'users',
        help='List users with a Permission Set'
    )
    users_parser.add_argument(
        'permission_set',
        help='Permission Set name or ID'
    )
    users_parser.set_defaults(func=cmd_users_with_ps)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        return args.func(args) or 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
