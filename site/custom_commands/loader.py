"""
Shared bulk-load logic used by both the REST API views and the management command.
"""

import csv
import io
import secrets
import string

from django.contrib.auth.models import User
from django.db import transaction


def random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def parse_csv(file_content):
    """Parse CSV string content into a list of dicts."""
    return list(csv.DictReader(io.StringIO(file_content)))


def load_users(rows, is_teacher=False, dry_run=False):
    """
    Bulk-create user accounts from a list of row dicts.

    Returns dict with keys: created, skipped, errors, credentials.
    """
    from judge.models import Profile, Organization

    role = 'teacher' if is_teacher else 'student'
    created = 0
    skipped = 0
    errors = []
    credentials = []

    if not rows:
        return {'created': 0, 'skipped': 0, 'errors': ['CSV file is empty'], 'credentials': []}

    required = {'username'}
    headers = set(rows[0].keys())
    missing = required - headers
    if missing:
        return {
            'created': 0, 'skipped': 0,
            'errors': [f'Missing required CSV columns: {", ".join(missing)}'],
            'credentials': [],
        }

    for i, row in enumerate(rows, start=2):
        username = row.get('username', '').strip()
        if not username:
            errors.append(f'Row {i}: empty username, skipped')
            continue

        if User.objects.filter(username=username).exists():
            errors.append(f'Row {i}: user "{username}" already exists, skipped')
            skipped += 1
            continue

        password = row.get('password', '').strip()
        generated_pw = False
        if not password:
            password = random_password()
            generated_pw = True

        email = row.get('email', '').strip()
        first_name = row.get('first_name', '').strip()
        last_name = row.get('last_name', '').strip()
        org_slug = row.get('organization', '').strip()

        if dry_run:
            credentials.append({
                'username': username,
                'password': '(dry-run)',
                'generated': generated_pw,
            })
            created += 1
            continue

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=is_teacher,
                )

                profile, _ = Profile.objects.get_or_create(user=user)

                if org_slug:
                    try:
                        org = Organization.objects.get(slug=org_slug)
                        org.members.add(profile)
                        if is_teacher:
                            org.admins.add(profile)
                    except Organization.DoesNotExist:
                        errors.append(
                            f'Row {i}: organization "{org_slug}" not found, '
                            f'user "{username}" created without organization'
                        )

                credentials.append({
                    'username': username,
                    'password': password,
                    'generated': generated_pw,
                })
                created += 1

        except Exception as e:
            errors.append(f'Row {i}: failed to create "{username}": {e}')

    return {
        'role': role,
        'created': created,
        'skipped': skipped,
        'errors': errors,
        'credentials': credentials,
    }


def load_problems(rows, dry_run=False):
    """
    Bulk-create problems from a list of row dicts.

    Returns dict with keys: created, skipped, errors.
    """
    from judge.models import Problem, ProblemGroup

    created = 0
    skipped = 0
    errors = []

    if not rows:
        return {'created': 0, 'skipped': 0, 'errors': ['CSV file is empty']}

    required = {'code', 'name'}
    headers = set(rows[0].keys())
    missing = required - headers
    if missing:
        return {
            'created': 0, 'skipped': 0,
            'errors': [f'Missing required CSV columns: {", ".join(missing)}'],
        }

    for i, row in enumerate(rows, start=2):
        code = row.get('code', '').strip()
        name = row.get('name', '').strip()

        if not code or not name:
            errors.append(f'Row {i}: empty code or name, skipped')
            continue

        if Problem.objects.filter(code=code).exists():
            errors.append(f'Row {i}: problem "{code}" already exists, skipped')
            skipped += 1
            continue

        description = row.get('description', '').strip() or f'Problem: {name}'

        try:
            time_limit = float(row.get('time_limit', '2.0').strip() or '2.0')
        except ValueError:
            time_limit = 2.0

        try:
            memory_limit = int(row.get('memory_limit', '262144').strip() or '262144')
        except ValueError:
            memory_limit = 262144

        try:
            points = float(row.get('points', '1.0').strip() or '1.0')
        except ValueError:
            points = 1.0

        group_name = row.get('group', '').strip() or 'Uncategorized'

        if dry_run:
            created += 1
            continue

        try:
            with transaction.atomic():
                group, _ = ProblemGroup.objects.get_or_create(name=group_name)

                Problem.objects.create(
                    code=code,
                    name=name,
                    description=description,
                    time_limit=time_limit,
                    memory_limit=memory_limit,
                    points=points,
                    group=group,
                )
                created += 1

        except Exception as e:
            errors.append(f'Row {i}: failed to create "{code}": {e}')

    return {
        'created': created,
        'skipped': skipped,
        'errors': errors,
    }
