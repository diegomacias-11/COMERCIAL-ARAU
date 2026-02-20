from django.core.management.base import BaseCommand
from django.db.models import Q

from leads.models import LinkedInLead, MetaLead


class Command(BaseCommand):
    help = (
        "Rellena platform en leads historicos cuando viene vacio. "
        "MetaLead -> Meta, LinkedInLead -> LinkedIn."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo muestra cuantos registros se actualizarian, sin escribir en DB.",
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))

        meta_missing_qs = MetaLead.objects.filter(Q(platform__isnull=True) | Q(platform__exact=""))
        linkedin_missing_qs = LinkedInLead.objects.filter(Q(platform__isnull=True) | Q(platform__exact=""))

        meta_missing = meta_missing_qs.count()
        linkedin_missing = linkedin_missing_qs.count()

        self.stdout.write(f"MetaLead sin platform: {meta_missing}")
        self.stdout.write(f"LinkedInLead sin platform: {linkedin_missing}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: no se realizaron cambios."))
            return

        updated_meta = meta_missing_qs.update(platform="Meta")
        updated_linkedin = linkedin_missing_qs.update(platform="LinkedIn")

        self.stdout.write(self.style.SUCCESS(f"MetaLead actualizados: {updated_meta}"))
        self.stdout.write(self.style.SUCCESS(f"LinkedInLead actualizados: {updated_linkedin}"))
