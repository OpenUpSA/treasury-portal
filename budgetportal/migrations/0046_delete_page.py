# Generated by Django 2.2.10 on 2020-03-10 21:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailredirects', '0006_redirect_increase_max_length'),
        ('wagtailforms', '0004_add_verbose_name_plural'),
        ('wagtailcore', '0045_assign_unlock_grouppagepermission'),
        ('budgetportal', '0045_auto_20200310_2042'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Page',
        ),
    ]
