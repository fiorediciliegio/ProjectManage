from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from app01.models import Person


class Command(BaseCommand):
    help = "Create or update a dedicated local account for load testing."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="loadtest_user")
        parser.add_argument("--password", default="loadtest123456")

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        user.is_active = True
        user.set_password(password)
        user.save(update_fields=["password", "is_active"])

        person, _ = Person.objects.update_or_create(
            user=user,
            defaults={
                "sys_role": "admin",
                "NAME_Person": "LoadTest",
                "NUM_Person": "LOADTEST-001",
                "MAIL_Person": "loadtest@example.com",
                "POS_Person": "系统管理员",
                "DESC_Person": "Local account for ProjectManage load testing.",
            },
        )

        action = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} load test user '{user.username}' with person id {person.id}"
            )
        )
