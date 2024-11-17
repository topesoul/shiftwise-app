# /workspace/shiftwise/accounts/management/commands/assign_groups.py

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Assign users to specified groups."

    def add_arguments(self, parser):
        parser.add_argument(
            "username", type=str, help="Username of the user to assign."
        )
        parser.add_argument(
            "group_name", type=str, help="Name of the group to assign the user to."
        )

    def handle(self, *args, **kwargs):
        username = kwargs["username"]
        group_name = kwargs["group_name"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' does not exist."))
            return

        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Group '{group_name}' does not exist."))
            return

        user.groups.add(group)
        self.stdout.write(
            self.style.SUCCESS(
                f"User '{username}' has been added to group '{group_name}'."
            )
        )
