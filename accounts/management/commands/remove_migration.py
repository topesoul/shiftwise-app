# /workspace/shiftwise/account/management/commands/remove_migration.py

from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings

class Command(BaseCommand):
    help = 'Remove a specific migration record from django_migrations'

    def add_arguments(self, parser):
        parser.add_argument('app_label', type=str, help='App label of the migration')
        parser.add_argument('migration_name', type=str, help='Name of the migration to remove')

    def handle(self, *args, **options):
        app_label = options['app_label']
        migration_name = options['migration_name']

        with connections['default'].cursor() as cursor:
            cursor.execute(
                "DELETE FROM django_migrations WHERE app = %s AND name = %s;",
                [app_label, migration_name]
            )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully removed migration '{migration_name}' from app '{app_label}'."
        ))
