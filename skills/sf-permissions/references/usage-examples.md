<!-- Parent: sf-permissions/SKILL.md -->
# sf-permissions Usage Examples

Real-world examples of using sf-permissions for permission analysis.

## CLI Examples

### 1. View Org Permission Hierarchy

```bash
# ASCII tree output (default)
python cli.py hierarchy

# Mermaid diagram for documentation
python cli.py hierarchy --format mermaid > hierarchy.md

# Specify target org
python cli.py hierarchy --target-org my-sandbox
```

### 2. Permission Detection

#### Object Permissions

```bash
# Who has delete access to Account?
python cli.py detect object Account --access delete

# Who has any access to a custom object?
python cli.py detect object My_Custom_Object__c

# Who has Create, Read, Update access to Opportunity?
python cli.py detect object Opportunity --access create,read,edit
```

#### Field Permissions

```bash
# Who can edit Account.AnnualRevenue?
python cli.py detect field Account.AnnualRevenue --access edit

# Who has read access to a sensitive field?
python cli.py detect field Contact.SSN__c --access read
```

#### Apex Class Access

```bash
# Who has access to a specific Apex class?
python cli.py detect apex MyApexController
```

#### Custom Permissions

```bash
# Who has a custom permission?
python cli.py detect custom Can_Approve_Expenses
```

#### System Permissions

```bash
# Who has ModifyAllData (dangerous permission)?
python cli.py detect system ModifyAllData

# Who can view setup?
python cli.py detect system ViewSetup
```

### 3. User Analysis

```bash
# Analyze permissions for a specific user
python cli.py user john.smith@company.com

# Use user ID
python cli.py user 005xx000001234AAA

# Mermaid output
python cli.py user john.smith@company.com --format mermaid
```

### 4. Export Permission Sets

```bash
# Export to CSV
python cli.py export Sales_Manager -o /tmp/sales_manager.csv

# Export to JSON
python cli.py export Sales_Manager -o /tmp/sales_manager.json
```

### 5. Permission Set Details

```bash
# View Permission Set details
python cli.py ps Sales_Manager

# View Permission Set Group details
python cli.py psg Sales_Cloud_User

# List users with a Permission Set
python cli.py users Sales_Manager
```

---

## Python API Examples

### Connect to Salesforce

```python
from auth import get_sf_connection

# Use default org
sf = get_sf_connection()

# Use specific org
sf = get_sf_connection('my-sandbox')
```

### Build Permission Hierarchy

```python
from hierarchy_viewer import get_org_permission_hierarchy

hierarchy = get_org_permission_hierarchy(sf)

print(f"PSGs: {hierarchy.total_psg_count}")
print(f"Total PS: {hierarchy.total_ps_count}")

for psg in hierarchy.permission_set_groups:
    print(f"  {psg.master_label} ({len(psg.permission_sets)} PS)")
```

### Detect Permissions

```python
from permission_detector import (
    detect_object_permission,
    detect_field_permission,
    detect_apex_class_permission,
    detect_custom_permission,
)

# Find PS with Account delete
results = detect_object_permission(sf, 'Account', ['delete'])

for r in results:
    print(f"{r.permission_set_label}: {r.assigned_user_count} users")
    if r.is_in_group:
        print(f"  In group: {r.group_label}")

# Find PS with field edit access
results = detect_field_permission(sf, 'Account', 'AnnualRevenue', ['edit'])

# Find PS with Apex access
results = detect_apex_class_permission(sf, 'MyController')

# Find PS with custom permission
results = detect_custom_permission(sf, 'Can_Approve_Expenses')
```

### Analyze User Permissions

```python
from user_analyzer import analyze_user_permissions, compare_user_permissions

# Analyze single user
analysis = analyze_user_permissions(sf, 'john@company.com')

print(f"User: {analysis.user.name}")
print(f"Profile: {analysis.user.profile_name}")
print(f"Total PS: {analysis.total_permission_sets}")

# Via groups
for group in analysis.via_groups:
    print(f"Via {group['label']}:")
    for ps in group['permission_sets']:
        print(f"  - {ps['label']}")

# Direct assignments
for ps in analysis.direct_assignments:
    print(f"Direct: {ps.label}")

# Compare two users
comparison = compare_user_permissions(sf, 'user1@company.com', 'user2@company.com')
print(f"Shared: {len(comparison['shared'])} PS")
print(f"User1 only: {len(comparison['ps1_only'])} PS")
print(f"User2 only: {len(comparison['ps2_only'])} PS")
```

### Export to Files

```python
from permission_exporter import (
    export_permission_set_to_csv,
    export_permission_set_to_json,
    compare_permission_sets,
)

# Export to CSV
path = export_permission_set_to_csv(sf, 'Sales_Manager', '/tmp/sm.csv')

# Export to JSON
path = export_permission_set_to_json(sf, 'Sales_Manager', '/tmp/sm.json')

# Compare two PS
diff = compare_permission_sets(sf, 'Sales_Manager', 'Sales_Rep')
print(f"Differences: {len(diff['ps1_only'])} in SM only")
```

### Render Output

```python
from renderers.ascii_tree import (
    render_hierarchy_tree,
    render_detection_table,
    render_user_tree,
)
from renderers.mermaid import (
    render_hierarchy_mermaid,
    render_user_mermaid,
)

# ASCII output (Rich library)
render_hierarchy_tree(hierarchy)
render_user_tree(analysis)
render_detection_table(results, "Account delete access")

# Mermaid diagrams
mermaid_code = render_hierarchy_mermaid(hierarchy)
print(mermaid_code)  # Paste into markdown
```

---

## Common Workflows

### Security Audit

```python
# 1. Find all PS with dangerous permissions
dangerous_perms = ['ModifyAllData', 'ViewAllData', 'ManageUsers']

for perm in dangerous_perms:
    results = detect_system_permission(sf, perm)
    print(f"\n{perm}: {len(results)} PS")
    for r in results:
        if r.assigned_user_count > 0:
            print(f"  ⚠️  {r.permission_set_label}: {r.assigned_user_count} users")
```

### User Provisioning Check

```python
# Verify a user has expected permissions
expected_ps = ['Sales_Account_Access', 'Report_Runner', 'API_Access']

analysis = analyze_user_permissions(sf, 'new.user@company.com')
user_ps_names = set()

for g in analysis.via_groups:
    for ps in g['permission_sets']:
        user_ps_names.add(ps['name'])
for ps in analysis.direct_assignments:
    user_ps_names.add(ps.name)

missing = set(expected_ps) - user_ps_names
if missing:
    print(f"Missing PS: {missing}")
else:
    print("All expected PS assigned ✅")
```

### Documentation Generation

```python
# Generate permission documentation

hierarchy = get_org_permission_hierarchy(sf)

# Create markdown documentation
doc = "# Org Permission Structure\n\n"
doc += render_hierarchy_mermaid(hierarchy) + "\n\n"

doc += "## Permission Set Groups\n\n"
for psg in hierarchy.permission_set_groups:
    doc += f"### {psg.master_label}\n"
    doc += f"- Status: {psg.status}\n"
    doc += f"- Users: {psg.assigned_user_count}\n"
    doc += f"- Permission Sets:\n"
    for ps in psg.permission_sets:
        doc += f"  - {ps.label}\n"
    doc += "\n"

with open('/tmp/permissions-doc.md', 'w') as f:
    f.write(doc)
```
