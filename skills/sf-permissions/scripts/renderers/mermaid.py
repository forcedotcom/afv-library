"""
Mermaid Diagram Renderer

Generates Mermaid diagram syntax for embedding in Markdown documentation.
Mermaid diagrams can be rendered in GitHub, GitLab, Notion, and many
other documentation platforms.
"""

from typing import Optional


def render_hierarchy_mermaid(hierarchy) -> str:
    """
    Render the org permission hierarchy as a Mermaid diagram.

    Args:
        hierarchy: OrgPermissionHierarchy object

    Returns:
        Mermaid diagram syntax as a string

    Example output:
        ```mermaid
        graph TD
            subgraph Permission Set Groups
                PSG1[Sales_Cloud_User]
            end
        ```
    """
    lines = [
        "```mermaid",
        "graph TD",
        "",
    ]

    # Add PSG subgraph
    if hierarchy.permission_set_groups:
        lines.append("    subgraph PSGs[Permission Set Groups]")
        for i, psg in enumerate(hierarchy.permission_set_groups[:10]):  # Limit for readability
            status_class = "active" if psg.status == "Active" else "outdated"
            lines.append(f"        PSG{i}[{_escape_mermaid(psg.master_label)}]:::{status_class}")
        if len(hierarchy.permission_set_groups) > 10:
            lines.append(f"        PSG_more[...and {len(hierarchy.permission_set_groups) - 10} more]")
        lines.append("    end")
        lines.append("")

    # Add PS subgraph
    all_ps_in_groups = {}
    ps_index = 0

    for i, psg in enumerate(hierarchy.permission_set_groups[:10]):
        for ps in psg.permission_sets[:5]:  # Limit PS per group
            ps_key = f"PS{ps_index}"
            all_ps_in_groups[ps.id] = ps_key
            ps_index += 1

    if all_ps_in_groups:
        lines.append("    subgraph PSs[Permission Sets in Groups]")
        ps_index = 0
        for i, psg in enumerate(hierarchy.permission_set_groups[:10]):
            for ps in psg.permission_sets[:5]:
                lines.append(f"        PS{ps_index}[{_escape_mermaid(ps.label)}]")
                ps_index += 1
        lines.append("    end")
        lines.append("")

    # Add connections
    ps_index = 0
    for i, psg in enumerate(hierarchy.permission_set_groups[:10]):
        for j, ps in enumerate(psg.permission_sets[:5]):
            lines.append(f"    PSG{i} --> PS{ps_index}")
            ps_index += 1

    # Add standalone PS
    if hierarchy.standalone_permission_sets:
        lines.append("")
        lines.append("    subgraph Standalone[Standalone Permission Sets]")
        for i, ps in enumerate(hierarchy.standalone_permission_sets[:10]):
            lines.append(f"        SPS{i}[{_escape_mermaid(ps.label)}]")
        if len(hierarchy.standalone_permission_sets) > 10:
            lines.append(f"        SPS_more[...and {len(hierarchy.standalone_permission_sets) - 10} more]")
        lines.append("    end")

    # Add styling
    lines.extend([
        "",
        "    %% Styling",
        "    classDef active fill:#90EE90,stroke:#228B22",
        "    classDef outdated fill:#FFB6C1,stroke:#DC143C",
    ])

    lines.append("```")

    return "\n".join(lines)


def render_user_mermaid(analysis) -> str:
    """
    Render user permission analysis as a Mermaid diagram.

    Args:
        analysis: UserPermissionAnalysis object

    Returns:
        Mermaid diagram syntax as a string
    """
    user = analysis.user

    lines = [
        "```mermaid",
        "graph TD",
        "",
        f"    User[👤 {_escape_mermaid(user.name)}]",
        "",
    ]

    # Via groups
    if analysis.via_groups:
        lines.append("    subgraph Groups[Via Permission Set Groups]")
        for i, group in enumerate(analysis.via_groups):
            lines.append(f"        G{i}[🔒 {_escape_mermaid(group['label'])}]")
        lines.append("    end")
        lines.append("")

        # Connect user to groups
        for i in range(len(analysis.via_groups)):
            lines.append(f"    User --> G{i}")

        # Add PS in groups
        lines.append("")
        ps_index = 0
        for i, group in enumerate(analysis.via_groups):
            for ps in group['permission_sets'][:3]:
                lines.append(f"    G{i} --> GPS{ps_index}[{_escape_mermaid(ps['label'])}]")
                ps_index += 1

    # Direct assignments
    if analysis.direct_assignments:
        lines.append("")
        lines.append("    subgraph Direct[Direct Permission Sets]")
        for i, ps in enumerate(analysis.direct_assignments[:5]):
            lines.append(f"        DPS{i}[{_escape_mermaid(ps.label)}]")
        if len(analysis.direct_assignments) > 5:
            lines.append(f"        DPS_more[...and {len(analysis.direct_assignments) - 5} more]")
        lines.append("    end")
        lines.append("")

        # Connect user to direct PS
        for i in range(min(5, len(analysis.direct_assignments))):
            lines.append(f"    User --> DPS{i}")

    lines.append("```")

    return "\n".join(lines)


def render_detection_mermaid(results, query_description: str) -> str:
    """
    Render permission detection results as a Mermaid diagram.

    Args:
        results: List of DetectionResult objects
        query_description: Human-readable description of the query

    Returns:
        Mermaid diagram syntax as a string
    """
    lines = [
        "```mermaid",
        "graph LR",
        "",
        f"    Query[🔍 {_escape_mermaid(query_description)}]",
        "",
    ]

    # Group results by PSG membership
    in_groups = [r for r in results if r.is_in_group]
    standalone = [r for r in results if not r.is_in_group]

    # PSG-assigned PS
    if in_groups:
        # Group by PSG
        psg_map = {}
        for r in in_groups:
            psg_name = r.group_name or "Unknown"
            if psg_name not in psg_map:
                psg_map[psg_name] = {
                    'label': r.group_label or psg_name,
                    'results': []
                }
            psg_map[psg_name]['results'].append(r)

        lines.append("    subgraph InGroups[In Permission Set Groups]")
        for i, (psg_name, psg_data) in enumerate(psg_map.items()):
            lines.append(f"        PSG{i}[🔒 {_escape_mermaid(psg_data['label'])}]")
        lines.append("    end")
        lines.append("")

        # Connect query to PSGs
        for i in range(len(psg_map)):
            lines.append(f"    Query --> PSG{i}")

    # Standalone PS
    if standalone:
        lines.append("")
        lines.append("    subgraph StandalonePS[Standalone Permission Sets]")
        for i, r in enumerate(standalone[:5]):
            lines.append(f"        SPS{i}[{_escape_mermaid(r.permission_set_label)}]")
        if len(standalone) > 5:
            lines.append(f"        SPS_more[...and {len(standalone) - 5} more]")
        lines.append("    end")
        lines.append("")

        # Connect query to standalone PS
        for i in range(min(5, len(standalone))):
            lines.append(f"    Query --> SPS{i}")

    lines.append("```")

    return "\n".join(lines)


def render_comparison_mermaid(comparison: dict) -> str:
    """
    Render Permission Set comparison as a Mermaid diagram.

    Args:
        comparison: Dict from compare_permission_sets

    Returns:
        Mermaid diagram syntax as a string
    """
    ps1 = comparison['ps1']['name']
    ps2 = comparison['ps2']['name']

    lines = [
        "```mermaid",
        "graph TD",
        "",
        f"    PS1[{_escape_mermaid(ps1)}]",
        f"    PS2[{_escape_mermaid(ps2)}]",
        f"    Shared[Shared: {len(comparison['both'])} permissions]",
        f"    PS1Only[Only in {_escape_mermaid(ps1)}: {len(comparison['ps1_only'])}]",
        f"    PS2Only[Only in {_escape_mermaid(ps2)}: {len(comparison['ps2_only'])}]",
        "",
        "    PS1 --> Shared",
        "    PS2 --> Shared",
        "    PS1 --> PS1Only",
        "    PS2 --> PS2Only",
        "",
        "    style Shared fill:#90EE90",
        "    style PS1Only fill:#FFB6C1",
        "    style PS2Only fill:#ADD8E6",
        "```"
    ]

    return "\n".join(lines)


def _escape_mermaid(text: str) -> str:
    """
    Escape special characters for Mermaid syntax.

    Mermaid has issues with certain characters in node labels.
    """
    if not text:
        return ""

    # Replace problematic characters
    text = text.replace('"', "'")
    text = text.replace('[', '(')
    text = text.replace(']', ')')
    text = text.replace('{', '(')
    text = text.replace('}', ')')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('&', '&amp;')

    # Truncate if too long
    if len(text) > 30:
        text = text[:27] + "..."

    return text


def generate_flowchart_url(mermaid_code: str) -> str:
    """
    Generate a Mermaid Live Editor URL for the diagram.

    Args:
        mermaid_code: The Mermaid diagram code (without fence markers)

    Returns:
        URL to the Mermaid Live Editor with the diagram preloaded

    Note:
        This creates a URL that opens the diagram in mermaid.live
    """
    import base64
    import json

    # Remove code fences if present
    code = mermaid_code.strip()
    if code.startswith("```mermaid"):
        code = code[10:]
    if code.endswith("```"):
        code = code[:-3]
    code = code.strip()

    # Create the state object
    state = {
        "code": code,
        "mermaid": {"theme": "default"},
        "updateEditor": True
    }

    # Encode to base64
    json_str = json.dumps(state)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()

    return f"https://mermaid.live/edit#base64:{encoded}"
