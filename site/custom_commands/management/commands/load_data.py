"""
Management command wrapper around the shared loader module.

Usage:
  python manage.py load_data --type students --file students.csv
  python manage.py load_data --type teachers --file teachers.csv --dry-run
  python manage.py load_data --type problems --file problems.csv
"""

import sys

from django.core.management.base import BaseCommand, CommandError

from custom_commands.loader import load_problems, load_users, parse_csv


class Command(BaseCommand):
    help = 'Bulk-load students, teachers, or problems from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--type', required=True, choices=['students', 'teachers', 'problems'],
                            help='Type of data to load')
        parser.add_argument('--file', required=True, help='Path to CSV file (use "-" for stdin)')
        parser.add_argument('--dry-run', action='store_true', help='Validate without saving')

    def handle(self, *args, **options):
        data_type = options['type']
        file_path = options['file']
        dry_run = options['dry_run']

        if file_path == '-':
            content = sys.stdin.read()
        else:
            try:
                with open(file_path, newline='', encoding='utf-8') as fh:
                    content = fh.read()
            except FileNotFoundError:
                raise CommandError(f'File not found: {file_path}')

        rows = parse_csv(content)
        if not rows:
            raise CommandError('CSV file is empty or has no data rows')

        if data_type in ('students', 'teachers'):
            result = load_users(rows, is_teacher=(data_type == 'teachers'), dry_run=dry_run)
        else:
            result = load_problems(rows, dry_run=dry_run)

        # Print summary
        role = result.get('role', 'problem')
        prefix = '[DRY RUN] ' if dry_run else ''

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'{prefix}Would create {result["created"]} {role}(s), {result["skipped"]} skipped'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Created {result["created"]} {role}(s), {result["skipped"]} skipped'))

        if result['errors']:
            self.stdout.write(self.style.ERROR(f'{len(result["errors"])} error(s):'))
            for e in result['errors']:
                self.stderr.write(f'  {e}')

        # Print generated credentials for user imports
        credentials = result.get('credentials', [])
        gen_creds = [c for c in credentials if c['generated'] and not dry_run]
        if gen_creds:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Generated credentials (save these!):'))
            self.stdout.write(f'  {"username":<20} {"password"}')
            self.stdout.write(f'  {"\u2500" * 20} {"\u2500" * 14}')
            for c in gen_creds:
                self.stdout.write(f'  {c["username"]:<20} {c["password"]}')
