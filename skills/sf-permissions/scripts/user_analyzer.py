"""
User Permission Analyzer

Analyzes and displays all permissions assigned to a specific user,
tracing through both direct Permission Set assignments and
Permission Set Group memberships.
"""

from dataclasses import dataclass, field
from typing import Optional
from simple_salesforce import Salesforce


@dataclass
class UserInfo:
    """Basic user information."""
    id: str
    name: str
    username: str
    email: Optional[str] = None
    profile_name: Optional[str] = None
    profile_id: Optional[str] = None
    is_active: bool = True


@dataclass
class AssignedPermissionSet:
    """A Permission Set assigned to a user."""
    id: str
    name: str
    label: str
    description: Optional[str] = None
    assigned_via_group: bool = False
    group_name: Optional[str] = None
    group_label: Optional[str] = None


@dataclass
class UserPermissionAnalysis:
    """Complete permission analysis for a user."""
    user: UserInfo
    via_groups: list[dict] = field(default_factory=list)  # PSG with their PS
    direct_assignments: list[AssignedPermissionSet] = field(default_factory=list)
    total_permission_sets: int = 0


def analyze_user_permissions(
    sf: Salesforce,
    user_identifier: str
) -> UserPermissionAnalysis:
    """
    Analyze all permissions assigned to a specific user.

    Args:
        sf: Salesforce connection
        user_identifier: User ID (005...) or Username (email format)

    Returns:
        UserPermissionAnalysis with complete breakdown

    Example:
        >>> analysis = analyze_user_permissions(sf, 'john.smith@company.com')
        >>> print(f"User has {analysis.total_permission_sets} permission sets")
    """
    # Resolve user
    user = _get_user_info(sf, user_identifier)

    # Get all PS assignments for this user
    assignment_query = f"""
        SELECT
            PermissionSetId,
            PermissionSet.Name,
            PermissionSet.Label,
            PermissionSet.Description,
            PermissionSetGroupId,
            PermissionSetGroup.DeveloperName,
            PermissionSetGroup.MasterLabel
        FROM PermissionSetAssignment
        WHERE AssigneeId = '{user.id}'
        AND PermissionSet.IsOwnedByProfile = false
    """
    assignments = sf.query_all(assignment_query)

    # Organize by group vs direct
    via_groups = {}  # group_id -> {info, permission_sets}
    direct = []

    for a in assignments['records']:
        psg_id = a.get('PermissionSetGroupId')

        if psg_id:
            # This is an assignment via a Permission Set Group
            if psg_id not in via_groups:
                via_groups[psg_id] = {
                    'id': psg_id,
                    'name': a['PermissionSetGroup']['DeveloperName'],
                    'label': a['PermissionSetGroup']['MasterLabel'],
                    'permission_sets': [],
                }

            # Get the PS that are part of this group
            # (The assignment record doesn't directly tell us which PS,
            #  so we need to query PermissionSetGroupComponent)
        else:
            # Direct PS assignment
            if a.get('PermissionSetId'):
                direct.append(AssignedPermissionSet(
                    id=a['PermissionSetId'],
                    name=a['PermissionSet']['Name'],
                    label=a['PermissionSet']['Label'],
                    description=a['PermissionSet'].get('Description'),
                    assigned_via_group=False,
                ))

    # For each group, get the component Permission Sets
    if via_groups:
        group_ids = list(via_groups.keys())
        group_ids_str = "', '".join(group_ids)

        component_query = f"""
            SELECT
                PermissionSetGroupId,
                PermissionSetId,
                PermissionSet.Name,
                PermissionSet.Label,
                PermissionSet.Description
            FROM PermissionSetGroupComponent
            WHERE PermissionSetGroupId IN ('{group_ids_str}')
        """
        components = sf.query_all(component_query)

        for c in components['records']:
            psg_id = c['PermissionSetGroupId']
            if psg_id in via_groups:
                via_groups[psg_id]['permission_sets'].append({
                    'id': c['PermissionSetId'],
                    'name': c['PermissionSet']['Name'],
                    'label': c['PermissionSet']['Label'],
                    'description': c['PermissionSet'].get('Description'),
                })

    # Calculate total unique PS
    all_ps_ids = set()
    for g in via_groups.values():
        for ps in g['permission_sets']:
            all_ps_ids.add(ps['id'])
    for ps in direct:
        all_ps_ids.add(ps.id)

    return UserPermissionAnalysis(
        user=user,
        via_groups=list(via_groups.values()),
        direct_assignments=direct,
        total_permission_sets=len(all_ps_ids),
    )


def _get_user_info(sf: Salesforce, user_identifier: str) -> UserInfo:
    """
    Get user information from ID or username.

    Args:
        sf: Salesforce connection
        user_identifier: User ID (005...) or Username

    Returns:
        UserInfo object

    Raises:
        ValueError: If user is not found
    """
    if user_identifier.startswith('005'):
        where_clause = f"Id = '{user_identifier}'"
    else:
        where_clause = f"Username = '{user_identifier}'"

    query = f"""
        SELECT Id, Name, Username, Email, IsActive,
               Profile.Name, ProfileId
        FROM User
        WHERE {where_clause}
    """

    result = sf.query(query)

    if not result['records']:
        raise ValueError(f"User not found: {user_identifier}")

    u = result['records'][0]
    return UserInfo(
        id=u['Id'],
        name=u['Name'],
        username=u['Username'],
        email=u.get('Email'),
        profile_name=u['Profile']['Name'] if u.get('Profile') else None,
        profile_id=u.get('ProfileId'),
        is_active=u['IsActive'],
    )


def get_users_with_permission_set(
    sf: Salesforce,
    ps_name: str
) -> list[UserInfo]:
    """
    Find all users who have a specific Permission Set assigned.

    Args:
        sf: Salesforce connection
        ps_name: Permission Set Name or ID

    Returns:
        List of UserInfo objects
    """
    # Get PS ID if name provided
    if not ps_name.startswith('0PS'):
        ps_query = f"SELECT Id FROM PermissionSet WHERE Name = '{ps_name}'"
        ps_result = sf.query(ps_query)
        if not ps_result['records']:
            raise ValueError(f"Permission Set not found: {ps_name}")
        ps_id = ps_result['records'][0]['Id']
    else:
        ps_id = ps_name

    # Get all assignments
    query = f"""
        SELECT
            Assignee.Id,
            Assignee.Name,
            Assignee.Username,
            Assignee.Email,
            Assignee.IsActive,
            Assignee.Profile.Name
        FROM PermissionSetAssignment
        WHERE PermissionSetId = '{ps_id}'
    """

    results = sf.query_all(query)

    users = []
    for r in results['records']:
        a = r['Assignee']
        users.append(UserInfo(
            id=a['Id'],
            name=a['Name'],
            username=a['Username'],
            email=a.get('Email'),
            profile_name=a['Profile']['Name'] if a.get('Profile') else None,
            is_active=a['IsActive'],
        ))

    return users


def get_users_with_permission_set_group(
    sf: Salesforce,
    psg_name: str
) -> list[UserInfo]:
    """
    Find all users who are assigned a specific Permission Set Group.

    Args:
        sf: Salesforce connection
        psg_name: Permission Set Group DeveloperName or ID

    Returns:
        List of UserInfo objects
    """
    # Get PSG ID if name provided
    if not psg_name.startswith('0PG'):
        psg_query = f"SELECT Id FROM PermissionSetGroup WHERE DeveloperName = '{psg_name}'"
        psg_result = sf.query(psg_query)
        if not psg_result['records']:
            raise ValueError(f"Permission Set Group not found: {psg_name}")
        psg_id = psg_result['records'][0]['Id']
    else:
        psg_id = psg_name

    query = f"""
        SELECT
            Assignee.Id,
            Assignee.Name,
            Assignee.Username,
            Assignee.Email,
            Assignee.IsActive,
            Assignee.Profile.Name
        FROM PermissionSetAssignment
        WHERE PermissionSetGroupId = '{psg_id}'
    """

    results = sf.query_all(query)

    users = []
    for r in results['records']:
        a = r['Assignee']
        users.append(UserInfo(
            id=a['Id'],
            name=a['Name'],
            username=a['Username'],
            email=a.get('Email'),
            profile_name=a['Profile']['Name'] if a.get('Profile') else None,
            is_active=a['IsActive'],
        ))

    return users


def compare_user_permissions(
    sf: Salesforce,
    user1_identifier: str,
    user2_identifier: str
) -> dict:
    """
    Compare permissions between two users.

    Args:
        sf: Salesforce connection
        user1_identifier: First user ID or username
        user2_identifier: Second user ID or username

    Returns:
        Dict with 'user1_only', 'user2_only', 'shared' permission sets
    """
    analysis1 = analyze_user_permissions(sf, user1_identifier)
    analysis2 = analyze_user_permissions(sf, user2_identifier)

    # Collect all PS IDs for each user
    def get_all_ps_ids(analysis: UserPermissionAnalysis) -> set:
        ids = set()
        for g in analysis.via_groups:
            for ps in g['permission_sets']:
                ids.add(ps['id'])
        for ps in analysis.direct_assignments:
            ids.add(ps.id)
        return ids

    ps1 = get_all_ps_ids(analysis1)
    ps2 = get_all_ps_ids(analysis2)

    user1_only = ps1 - ps2
    user2_only = ps2 - ps1
    shared = ps1 & ps2

    # Get PS names for the IDs
    all_ids = user1_only | user2_only | shared
    if all_ids:
        ids_str = "', '".join(all_ids)
        ps_query = f"SELECT Id, Name, Label FROM PermissionSet WHERE Id IN ('{ids_str}')"
        ps_results = sf.query_all(ps_query)
        ps_map = {p['Id']: {'name': p['Name'], 'label': p['Label']} for p in ps_results['records']}
    else:
        ps_map = {}

    return {
        'user1': {
            'id': analysis1.user.id,
            'name': analysis1.user.name,
            'username': analysis1.user.username,
        },
        'user2': {
            'id': analysis2.user.id,
            'name': analysis2.user.name,
            'username': analysis2.user.username,
        },
        'user1_only': [ps_map.get(id, {'id': id}) for id in user1_only],
        'user2_only': [ps_map.get(id, {'id': id}) for id in user2_only],
        'shared': [ps_map.get(id, {'id': id}) for id in shared],
    }


if __name__ == '__main__':
    import sys
    from auth import get_sf_connection

    sf = get_sf_connection()

    # Get current user if no argument provided
    if len(sys.argv) > 1:
        user_identifier = sys.argv[1]
    else:
        # Get current user
        identity = sf.query("SELECT Id, Username FROM User WHERE Id = 'me' LIMIT 1")
        user_identifier = identity['records'][0]['Username'] if identity['records'] else None

    if user_identifier:
        print(f"Analyzing permissions for: {user_identifier}")
        analysis = analyze_user_permissions(sf, user_identifier)

        print(f"\n👤 {analysis.user.name} ({analysis.user.username})")
        print(f"   Profile: {analysis.user.profile_name}")
        print(f"   Active: {'Yes' if analysis.user.is_active else 'No'}")

        print(f"\n📁 Via Permission Set Groups ({len(analysis.via_groups)}):")
        for g in analysis.via_groups:
            print(f"   🔒 {g['label']}")
            for ps in g['permission_sets']:
                print(f"      └── {ps['label']}")

        print(f"\n📋 Direct Permission Sets ({len(analysis.direct_assignments)}):")
        for ps in analysis.direct_assignments:
            print(f"   • {ps.label}")

        print(f"\n📊 Total unique Permission Sets: {analysis.total_permission_sets}")
