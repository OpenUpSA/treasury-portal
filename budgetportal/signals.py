from budgetportal import models
from django.db.models.signals import post_save
import prov_infra_projects
from django.dispatch import receiver
from django.contrib import messages


#@receiver([post_save], sender=models.IRMSnapshot)
#def handle_irm_snapshot_post_save(sender, instance, created, raw, using, update_fields, **kwargs):