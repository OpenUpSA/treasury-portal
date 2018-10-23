"""
Admin View for bulk uploading
"""

from django import forms
from django.shortcuts import render
from django.utils.text import slugify
from io import BytesIO
from openpyxl import load_workbook
from budgetportal.models import (
    Sphere,
    Government,
    Department,
)
import logging

logger = logging.getLogger(__name__)


class FileForm(forms.Form):
    sphere_queryset = Sphere.objects.all()
    sphere = forms.ModelChoiceField(queryset=sphere_queryset, empty_label=None)
    file = forms.FileField()


def bulk_upload_view(request):
    form = None
    file = None
    valid = None
    preview = None

    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            valid = True
            sphere = form.cleaned_data['sphere']
            metadata_file = request.FILES['file']
            preview = Preview(sphere, metadata_file)
            form = FileForm(initial = {'sphere': sphere.pk })
        else:
            valid = False
    else:
        valid = True
        form = FileForm()

    return render(request, "admin/bulk_upload.html", {
        'valid': valid,
        'file': file,
        'form': form,
        'preview': preview,
    })


class Preview:

    def __init__(self, sphere, metadata_file):
        self.rows = []

        with BytesIO(metadata_file.read()) as bytes_io:
            wb = load_workbook(filename=bytes_io, read_only=True)
            ws = wb['Resources']

            for row_idx, ws_row in enumerate(ws.rows):

                if not ws_row[0].value:
                    continue

                if row_idx == 0:
                    heading_index = {}
                    for i, cell in enumerate(ws_row):
                        if cell.value:
                            heading_index[cell.value] = i

                    government_idx = heading_index['government']
                    department_name_idx = heading_index[u'department_name']
                    dataset_name_idx = heading_index['dataset_name']
                    dataset_title_idx = heading_index['dataset_title']
                    group_id_idx = heading_index['group_id']
                    resource_name_idx = heading_index['resource_name']
                    resource_format_idx = heading_index['resource_format']
                    resource_url_idx = heading_index['resource_url']

                else:
                    government = Government.objects.get(sphere=sphere,
                                                        name=ws_row[government_idx].value)
                    department = Department.objects.get(government=government,
                                                        name=ws_row[department_name_idx].value)
                    self.rows.append({
                        'government': {
                            'object': government,
                            'label': government.name,
                        },
                        'department': {
                            'object': department,
                            'label': department.name,
                        },
                        'dataset': {
                            'name': slugify(ws_row[dataset_name_idx].value),
                            'label': ws_row[dataset_title_idx].value,
                        },
                        'group': {
                            'name': slugify(ws_row[group_id_idx].value),
                        },
                        'resource': {
                            'name': ws_row[resource_name_idx].value,
                            'format': ws_row[resource_format_idx].value,
                            'url': ws_row[resource_url_idx].value,
                            'valid': True,
                        },
                    })
