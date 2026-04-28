"""
Renderers for sf-permissions output.

Provides ASCII tree (terminal) and Mermaid (documentation) output formats.
"""

from .ascii_tree import (
    render_hierarchy_tree,
    render_user_tree,
    render_detection_table,
    render_summary_panel,
)
from .mermaid import (
    render_hierarchy_mermaid,
    render_user_mermaid,
)
