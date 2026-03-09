from django.core.management.base import BaseCommand, CommandError
from judge.models import Language, Problem, ProblemGroup, ProblemType


class Command(BaseCommand):
    help = 'Create a problem in the database'

    def add_arguments(self, parser):
        parser.add_argument('--code', required=True, help='Problem code (slug)')
        parser.add_argument('--name', required=True, help='Display name')
        parser.add_argument('--description', default='', help='Problem statement')
        parser.add_argument('--time-limit', type=float, default=2.0, help='Time limit in seconds')
        parser.add_argument('--memory-limit', type=int, default=262144, help='Memory limit in KB')
        parser.add_argument('--points', type=float, default=1.0, help='Base points')
        parser.add_argument('--group', default='Uncategorized', help='Problem group/category')
        parser.add_argument('--languages', default='', help='Comma-separated language keys (default: all)')
        parser.add_argument('--types', default='', help='Comma-separated problem type tags (e.g. Recursion,Lists)')
        parser.add_argument('--private', action='store_true', help='Do not make the problem public')

    def handle(self, *args, **options):
        code = options['code']
        name = options['name']
        description = options['description'] or f'Problem: {name}'
        group_name = options['group']

        group, _ = ProblemGroup.objects.get_or_create(name=group_name, defaults={'full_name': group_name})

        prob, created = Problem.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'time_limit': options['time_limit'],
                'memory_limit': options['memory_limit'],
                'points': options['points'],
                'group': group,
                'is_public': not options['private'],
            },
        )

        if not created:
            self.stdout.write(f'Problem already exists: {prob.code}')
            return

        lang_keys = options['languages']
        if lang_keys:
            keys = [k.strip() for k in lang_keys.split(',')]
            langs = Language.objects.filter(key__in=keys)
            missing = set(keys) - set(langs.values_list('key', flat=True))
            if missing:
                raise CommandError(f'Unknown language keys: {", ".join(sorted(missing))}')
            prob.allowed_languages.set(langs)
        else:
            prob.allowed_languages.set(Language.objects.all())

        type_names = options['types']
        if type_names:
            names = [t.strip() for t in type_names.split(',')]
            types = []
            for t in names:
                obj, _ = ProblemType.objects.get_or_create(name=t, defaults={'full_name': t})
                types.append(obj)
            prob.types.set(types)

        lang_list = list(prob.allowed_languages.values_list('key', flat=True))
        type_list = list(prob.types.values_list('name', flat=True))
        self.stdout.write(f'Created problem: {prob.code} (languages: {lang_list}, types: {type_list})')
