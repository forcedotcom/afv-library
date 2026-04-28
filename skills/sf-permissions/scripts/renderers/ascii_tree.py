"""
ASCII Tree Renderer

Provides terminal-friendly output using the Rich library.
Creates beautiful trees, tables, and panels for displaying
permission data in the terminal.
"""

from typing import Optional

try:
    from rich.console import Console
    from rich.tree import Tree
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Create console instance
console = Console() if RICH_AVAILABLE else None


def render_hierarchy_tree(hierarchy) -> None:
    """
    Render the org permission hierarchy as an ASCII tree.

    Args:
        hierarchy: OrgPermissionHierarchy object from hierarchy_viewer
    """
    if not RICH_AVAILABLE:
        _render_hierarchy_fallback(hierarchy)
        return

    # Create root tree
    root = Tree(
        "📦 [bold cyan]ORG PERMISSION HIERARCHY[/bold cyan]",
        guide_style="dim"
    )

    # Summary branch
    summary = root.add("📊 [bold]Summary[/bold]")
    summary.add(f"Permission Set Groups: {hierarchy.total_psg_count}")
    summary.add(f"Total Permission Sets: {hierarchy.total_ps_count}")
    summary.add(f"Standalone PS: {len(hierarchy.standalone_permission_sets)}")

    # PSG branch
    psg_branch = root.add(f"📁 [bold]Permission Set Groups[/bold] ({len(hierarchy.permission_set_groups)})")
    for psg in hierarchy.permission_set_groups:
        status_icon = "✅" if psg.status == "Active" else "⚠️"
        users_text = f" ({psg.assigned_user_count} users)" if psg.assigned_user_count else ""
        psg_node = psg_branch.add(
            f"{status_icon} [cyan]{psg.master_label}[/cyan]{users_text}"
        )
        for ps in psg.permission_sets[:5]:  # Show first 5
            psg_node.add(f"[dim]└── {ps.label}[/dim]")
        if len(psg.permission_sets) > 5:
            psg_node.add(f"[dim]└── ... and {len(psg.permission_sets) - 5} more[/dim]")

    # Standalone PS branch
    standalone_branch = root.add(
        f"📋 [bold]Standalone Permission Sets[/bold] ({len(hierarchy.standalone_permission_sets)})"
    )
    for ps in hierarchy.standalone_permission_sets[:10]:  # Show first 10
        users_text = f" ({ps.assigned_user_count} users)" if ps.assigned_user_count else ""
        standalone_branch.add(f"[dim]{ps.label}{users_text}[/dim]")
    if len(hierarchy.standalone_permission_sets) > 10:
        standalone_branch.add(
            f"[dim]... and {len(hierarchy.standalone_permission_sets) - 10} more[/dim]"
        )

    console.print(root)


def _render_hierarchy_fallback(hierarchy) -> None:
    """Fallback rendering without Rich."""
    print("\n📦 ORG PERMISSION HIERARCHY")
    print("═" * 50)

    print(f"\n📊 Summary:")
    print(f"   Permission Set Groups: {hierarchy.total_psg_count}")
    print(f"   Total Permission Sets: {hierarchy.total_ps_count}")
    print(f"   Standalone PS: {len(hierarchy.standalone_permission_sets)}")

    print(f"\n📁 Permission Set Groups ({len(hierarchy.permission_set_groups)}):")
    for psg in hierarchy.permission_set_groups:
        status = "✅" if psg.status == "Active" else "⚠️"
        print(f"   {status} {psg.master_label}")
        for ps in psg.permission_sets[:3]:
            print(f"      └── {ps.label}")
        if len(psg.permission_sets) > 3:
            print(f"      └── ... and {len(psg.permission_sets) - 3} more")

    print(f"\n📋 Standalone Permission Sets ({len(hierarchy.standalone_permission_sets)}):")
    for ps in hierarchy.standalone_permission_sets[:10]:
        print(f"   • {ps.label}")
    if len(hierarchy.standalone_permission_sets) > 10:
        print(f"   ... and {len(hierarchy.standalone_permission_sets) - 10} more")


def render_user_tree(analysis) -> None:
    """
    Render user permission analysis as an ASCII tree.

    Args:
        analysis: UserPermissionAnalysis object from user_analyzer
    """
    if not RICH_AVAILABLE:
        _render_user_fallback(analysis)
        return

    user = analysis.user

    # Create root tree
    status = "[green]Active[/green]" if user.is_active else "[red]Inactive[/red]"
    root = Tree(
        f"👤 [bold]{user.name}[/bold] ({user.username}) - {status}",
        guide_style="dim"
    )

    # Profile info
    info = root.add("ℹ️  [bold]Info[/bold]")
    info.add(f"Profile: {user.profile_name or 'N/A'}")
    info.add(f"Total Permission Sets: {analysis.total_permission_sets}")

    # Via groups
    if analysis.via_groups:
        groups_branch = root.add(
            f"📁 [bold]Via Permission Set Groups[/bold] ({len(analysis.via_groups)})"
        )
        for group in analysis.via_groups:
            group_node = groups_branch.add(f"🔒 [cyan]{group['label']}[/cyan]")
            for ps in group['permission_sets'][:5]:
                group_node.add(f"[dim]└── {ps['label']}[/dim]")
            if len(group['permission_sets']) > 5:
                group_node.add(f"[dim]└── ... and {len(group['permission_sets']) - 5} more[/dim]")

    # Direct assignments
    if analysis.direct_assignments:
        direct_branch = root.add(
            f"📋 [bold]Direct Permission Sets[/bold] ({len(analysis.direct_assignments)})"
        )
        for ps in analysis.direct_assignments:
            direct_branch.add(f"[dim]{ps.label}[/dim]")

    console.print(root)


def _render_user_fallback(analysis) -> None:
    """Fallback rendering without Rich."""
    user = analysis.user

    print(f"\n👤 {user.name} ({user.username})")
    print("═" * 50)
    print(f"   Profile: {user.profile_name or 'N/A'}")
    print(f"   Status: {'Active' if user.is_active else 'Inactive'}")
    print(f"   Total Permission Sets: {analysis.total_permission_sets}")

    if analysis.via_groups:
        print(f"\n📁 Via Permission Set Groups ({len(analysis.via_groups)}):")
        for group in analysis.via_groups:
            print(f"   🔒 {group['label']}")
            for ps in group['permission_sets'][:3]:
                print(f"      └── {ps['label']}")

    if analysis.direct_assignments:
        print(f"\n📋 Direct Permission Sets ({len(analysis.direct_assignments)}):")
        for ps in analysis.direct_assignments:
            print(f"   • {ps.label}")


def render_detection_table(results, query_description: str) -> None:
    """
    Render permission detection results as a table.

    Args:
        results: List of DetectionResult objects
        query_description: Human-readable description of the query
    """
    if not RICH_AVAILABLE:
        _render_detection_fallback(results, query_description)
        return

    # Create table
    table = Table(
        title=f"🔍 Permission Detection: {query_description}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    table.add_column("Permission Set", style="cyan")
    table.add_column("In Group?", justify="center")
    table.add_column("Group Name")
    table.add_column("Users", justify="right")
    table.add_column("Access", style="green")

    for r in results:
        # Format group info
        if r.is_in_group:
            in_group = "[green]✓[/green]"
            group_name = r.group_label or r.group_name
        else:
            in_group = "[dim]✗[/dim]"
            group_name = "[dim]Standalone[/dim]"

        # Format access details
        access_str = _format_access_details(r.access_details)

        table.add_row(
            r.permission_set_label,
            in_group,
            group_name,
            str(r.assigned_user_count),
            access_str
        )

    console.print(table)

    # Summary
    total_users = sum(r.assigned_user_count for r in results)
    console.print(
        f"\n📊 Found in [bold]{len(results)}[/bold] Permission Sets, "
        f"[bold]{total_users}[/bold] total user assignments"
    )


def _format_access_details(access_details: dict) -> str:
    """Format access details for display."""
    if not access_details:
        return ""

    # For object permissions
    if 'create' in access_details:
        perms = []
        if access_details.get('create'):
            perms.append('C')
        if access_details.get('read'):
            perms.append('R')
        if access_details.get('edit'):
            perms.append('U')
        if access_details.get('delete'):
            perms.append('D')
        if access_details.get('view_all'):
            perms.append('+VA')
        if access_details.get('modify_all'):
            perms.append('+MA')
        return ''.join(perms) if perms else 'None'

    # For field permissions
    if 'read' in access_details and 'edit' in access_details and len(access_details) == 2:
        perms = []
        if access_details.get('read'):
            perms.append('R')
        if access_details.get('edit'):
            perms.append('W')
        return ''.join(perms) if perms else 'None'

    # For entity access
    if access_details.get('has_access'):
        return "✓"

    # For system permissions
    if access_details.get('enabled'):
        return "Enabled"

    return str(access_details)


def _render_detection_fallback(results, query_description: str) -> None:
    """Fallback rendering without Rich."""
    print(f"\n🔍 Permission Detection: {query_description}")
    print("═" * 70)
    print(f"{'Permission Set':<25} │ {'In Group?':<12} │ {'Group':<15} │ Users")
    print("─" * 70)

    for r in results:
        in_group = "✓ Yes" if r.is_in_group else "✗ No"
        group_name = (r.group_label or r.group_name or "Standalone")[:15]
        print(f"{r.permission_set_label[:25]:<25} │ {in_group:<12} │ {group_name:<15} │ {r.assigned_user_count}")

    total_users = sum(r.assigned_user_count for r in results)
    print(f"\n📊 Found in {len(results)} Permission Sets, {total_users} total user assignments")


def render_summary_panel(title: str, data: dict) -> None:
    """
    Render a summary panel with key-value data.

    Args:
        title: Panel title
        data: Dict of key-value pairs to display
    """
    if not RICH_AVAILABLE:
        _render_summary_fallback(title, data)
        return

    # Build content
    content = ""
    for key, value in data.items():
        content += f"[bold]{key}:[/bold] {value}\n"

    panel = Panel(
        content.strip(),
        title=f"[bold]{title}[/bold]",
        border_style="cyan",
        box=box.ROUNDED
    )

    console.print(panel)


def _render_summary_fallback(title: str, data: dict) -> None:
    """Fallback rendering without Rich."""
    print(f"\n╭─ {title} ─╮")
    print("│")
    for key, value in data.items():
        print(f"│  {key}: {value}")
    print("│")
    print("╰" + "─" * (len(title) + 4) + "╯")


def render_comparison_table(comparison: dict) -> None:
    """
    Render a Permission Set comparison table.

    Args:
        comparison: Dict from compare_permission_sets
    """
    if not RICH_AVAILABLE:
        _render_comparison_fallback(comparison)
        return

    ps1_name = comparison['ps1']['name']
    ps2_name = comparison['ps2']['name']

    table = Table(
        title=f"🔄 Comparison: {ps1_name} vs {ps2_name}",
        box=box.ROUNDED
    )

    table.add_column("Category", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("Shared permissions", str(len(comparison['both'])))
    table.add_row(f"Only in {ps1_name}", str(len(comparison['ps1_only'])))
    table.add_row(f"Only in {ps2_name}", str(len(comparison['ps2_only'])))

    console.print(table)


def _render_comparison_fallback(comparison: dict) -> None:
    """Fallback comparison rendering."""
    ps1_name = comparison['ps1']['name']
    ps2_name = comparison['ps2']['name']

    print(f"\n🔄 Comparison: {ps1_name} vs {ps2_name}")
    print("═" * 50)
    print(f"   Shared permissions: {len(comparison['both'])}")
    print(f"   Only in {ps1_name}: {len(comparison['ps1_only'])}")
    print(f"   Only in {ps2_name}: {len(comparison['ps2_only'])}")
