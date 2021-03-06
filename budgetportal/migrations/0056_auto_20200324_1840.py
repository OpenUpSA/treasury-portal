# Generated by Django 2.2.10 on 2020-03-24 18:40

import wagtail.core.blocks
import wagtail.core.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("budgetportal", "0055_merge_20200323_1505"),
    ]

    operations = [
        migrations.AlterField(
            model_name="custompage",
            name="body",
            field=wagtail.core.fields.StreamField(
                [
                    (
                        "section",
                        wagtail.core.blocks.StructBlock(
                            [
                                (
                                    "presentation_class",
                                    wagtail.core.blocks.ChoiceBlock(
                                        choices=[
                                            ("is-default", "Default"),
                                            ("is-invisible", "No background/border"),
                                            ("is-bevel", "Bevel"),
                                        ]
                                    ),
                                ),
                                (
                                    "heading",
                                    wagtail.core.blocks.CharBlock(required=False),
                                ),
                                ("content", wagtail.core.blocks.RichTextBlock()),
                            ]
                        ),
                    ),
                    ("html", wagtail.core.blocks.RawHTMLBlock()),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="guidepage",
            name="body",
            field=wagtail.core.fields.StreamField(
                [
                    (
                        "section",
                        wagtail.core.blocks.StructBlock(
                            [
                                (
                                    "presentation_class",
                                    wagtail.core.blocks.ChoiceBlock(
                                        choices=[
                                            ("is-default", "Default"),
                                            ("is-invisible", "No background/border"),
                                            ("is-bevel", "Bevel"),
                                        ]
                                    ),
                                ),
                                (
                                    "heading",
                                    wagtail.core.blocks.CharBlock(required=False),
                                ),
                                ("content", wagtail.core.blocks.RichTextBlock()),
                            ]
                        ),
                    ),
                    ("html", wagtail.core.blocks.RawHTMLBlock()),
                    (
                        "chart_embed",
                        wagtail.core.blocks.StructBlock(
                            [
                                (
                                    "heading",
                                    wagtail.core.blocks.CharBlock(required=False),
                                ),
                                ("description", wagtail.core.blocks.RichTextBlock()),
                                ("embed_code", wagtail.core.blocks.RawHTMLBlock()),
                            ]
                        ),
                    ),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="postpage",
            name="body",
            field=wagtail.core.fields.StreamField(
                [
                    (
                        "section",
                        wagtail.core.blocks.StructBlock(
                            [
                                (
                                    "presentation_class",
                                    wagtail.core.blocks.ChoiceBlock(
                                        choices=[
                                            ("is-default", "Default"),
                                            ("is-invisible", "No background/border"),
                                            ("is-bevel", "Bevel"),
                                        ]
                                    ),
                                ),
                                (
                                    "heading",
                                    wagtail.core.blocks.CharBlock(required=False),
                                ),
                                ("content", wagtail.core.blocks.RichTextBlock()),
                            ]
                        ),
                    ),
                    ("html", wagtail.core.blocks.RawHTMLBlock()),
                ]
            ),
        ),
    ]
