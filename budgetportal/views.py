import urllib
import urlparse

import requests
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from slugify import slugify

from budgetportal.csv_gen import generate_csv_response
from budgetportal.openspending import PAGE_SIZE
from models import FinancialYear, Sphere, Dataset, Category, Department, InfrastructureProject
import yaml
import logging
from . import revenue
from csv import DictWriter

logger = logging.getLogger(__name__)

COMMON_DESCRIPTION = "South Africa's National and Provincial budget data "
COMMON_DESCRIPTION_ENDING = "from National Treasury in partnership with IMALI YETHU."


def homepage(request, financial_year_id, phase_slug, sphere_slug):
    """ The data for the vulekamali home page treemaps """
    dept = Department.objects.filter(government__sphere__slug=sphere_slug)[0]
    if sphere_slug == 'national':
        context = dept.get_national_expenditure_treemap(financial_year_id, phase_slug)
    elif sphere_slug == 'provincial':
        context = dept.get_provincial_expenditure_treemap(financial_year_id, phase_slug)
    else:
        return HttpResponse("Unknown government sphere.", status=400)
    response_yaml = yaml.safe_dump(context, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def department_preview(request, financial_year_id, sphere_slug, government_slug, phase_slug):
    dept = Department.objects.filter(government__sphere__slug=sphere_slug)[0]
    context = dept.get_preview_page(financial_year_id, phase_slug, government_slug, sphere_slug)
    response_yaml = yaml.safe_dump(context, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def year_home(request, financial_year_id):
    """
    View of a financial year homepage, e.g. /2017-18
    """
    year = get_object_or_404(FinancialYear, slug=financial_year_id)
    revenue_data = year.get_budget_revenue()

    context = {
        'financial_years': [],
        'revenue': revenue.sort_categories(revenue_data),
        'selected_financial_year': financial_year_id,
        'selected_tab': 'homepage',
        'slug': financial_year_id,
        'title': "South African Government Budgets %s - vulekamali" % year.slug,
        'description': COMMON_DESCRIPTION + COMMON_DESCRIPTION_ENDING,
        'url_path': year.get_url_path(),
    }
    for year in FinancialYear.get_available_years():
        is_selected = year.slug == financial_year_id
        context['financial_years'].append({
            'id': year.slug,
            'is_selected': is_selected,
            'closest_match': {
                'is_exact_match': True,
                'url_path': "/%s" % year.slug,
            },
        })

    response_yaml = yaml.safe_dump(context,
                                   default_flow_style=False,
                                   encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


class FinancialYearPage(View):
    """
    Generic page data for pages specific to a financial year
    """
    slug = None
    selected_tab = None

    def get(self, request, financial_year_id):
        context = {
            'financial_years': [],
            'selected_financial_year': financial_year_id,
            'selected_tab': self.selected_tab,
            'slug': self.slug,
            'title': "Search Result - vulekamali",
            'description': COMMON_DESCRIPTION + COMMON_DESCRIPTION_ENDING,
            'url_path': '/%s/%s' % (financial_year_id, self.slug),
        }

        for year in FinancialYear.get_available_years():
            is_selected = year.slug == financial_year_id
            context['financial_years'].append({
                'id': year.slug,
                'is_selected': is_selected,
                'closest_match': {
                    'is_exact_match': True,
                    'url_path': "/%s/%s" % (year.slug, self.slug),
                },
            })

        response_yaml = yaml.safe_dump(
            context,
            default_flow_style=False,
            encoding='utf-8'
        )
        return HttpResponse(response_yaml, content_type='text/x-yaml')


def programme_list_csv(request, financial_year_id, sphere_slug):
    sphere = get_object_or_404(Sphere, financial_year__slug=financial_year_id, slug=sphere_slug)
    filename = "programmes-%s-%s.csv" % (financial_year_id, sphere_slug)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    fieldnames = [
        'government_name',
        'department_name',
        'programme_name',
        'programme_number',
    ]
    writer = DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    for government in sphere.governments.all():
        for department in government.departments.all():
            for programme in department.programmes.all():
                row = {
                    'government_name': government.name.encode("utf-8"),
                    'department_name': department.name.encode("utf-8"),
                    'programme_name': programme.name.encode("utf-8"),
                    'programme_number': programme.programme_number,
                }
                writer.writerow(row)
    return response


def department_list_csv(request, financial_year_id):
    selected_year = get_object_or_404(FinancialYear, slug=financial_year_id)

    filename = "departments-%s.csv" % (financial_year_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    fieldnames = [
        'government',
        'department_name',
        'vote_number',
        'is_vote_primary',
        'intro',
        'website_url',
    ]
    writer = DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()

    for sphere_name in ('national', 'provincial'):
        for government in selected_year.spheres.filter(slug=sphere_name).first().governments.all():
            for department in government.departments.all():
                writer.writerow({
                    'government': government.name.encode("utf-8"),
                    'department_name': department.name.encode("utf-8"),
                    'vote_number': department.vote_number,
                    'is_vote_primary': department.is_vote_primary,
                    'intro': department.intro.encode("utf-8"),
                    'website_url': department.get_latest_website_url(),
                })

    return response


def department_list(request, financial_year_id):
    selected_year = get_object_or_404(FinancialYear, slug=financial_year_id)
    context = {
        'financial_years': [],
        'selected_financial_year': selected_year.slug,
        'selected_tab': 'departments',
        'slug': 'departments',
        'title': 'Department Budgets for %s - vulekamali' % selected_year.slug,
        'description': "Department budgets for the %s financial year %s" % (
         selected_year.slug, COMMON_DESCRIPTION_ENDING),
    }

    for year in FinancialYear.get_available_years():
        is_selected = year.slug == financial_year_id
        context['financial_years'].append({
            'id': year.slug,
            'is_selected': is_selected,
            'closest_match': {
                'is_exact_match': True,
                'url_path': "/%s/departments" % year.slug,
            },
        })

    for sphere_name in ('national', 'provincial'):
        context[sphere_name] = []
        for government in selected_year.spheres.filter(slug=sphere_name).first().governments.all():
            departments = []
            for department in government.departments.all():
                departments.append({
                    'name': department.name,
                    'slug': str(department.slug),
                    'vote_number': department.vote_number,
                    'url_path': department.get_url_path(),
                    'website_url': department.get_latest_website_url(),
                })
            departments = sorted(departments, key=lambda d: d['vote_number'])
            context[sphere_name].append({
                'name': government.name,
                'slug': str(government.slug),
                'departments': departments,
            })

    response_yaml = yaml.safe_dump(context, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def department(request, financial_year_id, sphere_slug, government_slug, department_slug):
    department = None
    selected_year = get_object_or_404(FinancialYear, slug=financial_year_id)

    years = FinancialYear.get_available_years()
    for year in years:
        if year.slug == financial_year_id:
            selected_year = year
            sphere = selected_year \
                     .spheres \
                     .filter(slug=sphere_slug) \
                     .first()
            government = sphere \
                         .governments \
                         .filter(slug=government_slug) \
                         .first()
            department = government \
                         .departments \
                         .filter(slug=department_slug) \
                         .first()

    financial_years_context = []
    for year in years:
        closest_match, closest_is_exact = year.get_closest_match(department)
        financial_years_context.append({
            'id': year.slug,
            'is_selected': year.slug == financial_year_id,
            'closest_match': {
                'url_path': closest_match.get_url_path(),
                'is_exact_match': closest_is_exact,
            },
        })

    contributed_datasets = []
    for dataset in department.get_contributed_datasets():
        contributed_datasets.append({
            'name': dataset.name,
            'contributor': dataset.get_organization()['name'],
            'url_path': dataset.get_url_path(),
        })

    #======== programmes =========================
    programmes = department.get_programme_budgets()
    if not programmes:
        programmes = {}
    if (not programmes) or (not programmes['programme_budgets']):
        programmes['programme_budgets'] = [
            {'name': p.name, 'total_budget': None}
            for p in department.programmes.order_by('programme_number')
        ]

    # ======= main budget docs =========================
    budget_dataset = department.get_dataset(
        group_name='budget-vote-documents')
    if budget_dataset:
        document_resource = budget_dataset.get_resource(format='PDF')
        if document_resource:
            document_resource = resource_fields(document_resource)
        tables_resource = (budget_dataset.get_resource(format='XLS') \
                           or budget_dataset.get_resource(format='XLSX'))
        if tables_resource:
            tables_resource = resource_fields(tables_resource)
        department_budget = {
            'name': budget_dataset.name,
            'document': document_resource,
            'tables': tables_resource,
        }
    else:
        department_budget = None

    # ======= adjusted budget docs =========================
    adjusted_budget_dataset = department.get_dataset(
        group_name='adjusted-budget-vote-documents')
    if adjusted_budget_dataset:
        document_resource = adjusted_budget_dataset.get_resource(format='PDF')
        if document_resource:
            document_resource = resource_fields(document_resource)
        tables_resource = (adjusted_budget_dataset.get_resource(format='XLS') \
                           or adjusted_budget_dataset.get_resource(format='XLSX'))
        if tables_resource:
            tables_resource = resource_fields(tables_resource)
        department_adjusted_budget = {
            'name': adjusted_budget_dataset.name,
            'document': document_resource,
            'tables': tables_resource,
        }
    else:
        department_adjusted_budget = None

    primary_department = department.get_primary_department()

    if department.government.sphere.slug == 'national':
        description_govt = "National"
    elif department.government.sphere.slug == 'provincial':
        description_govt = department.government.name


    context = {
        'economic_classification_by_programme': department.get_econ_by_programme_budgets(),
        'programme_by_economic_classification': department.get_prog_by_econ_budgets(),
        'subprogramme_by_programme': department.get_subprog_budgets(),
        'expenditure_over_time': department.get_expenditure_over_time(),
        'budget_actual': department.get_expenditure_time_series_summary(),
        'budget_actual_programmes': department.get_expenditure_time_series_by_programme(),
        'adjusted_budget_summary': department.get_adjusted_budget_summary(),
        'contributed_datasets': contributed_datasets if contributed_datasets else None,
        'financial_years': financial_years_context,
        'government': {
            'name': department.government.name,
            'slug': str(department.government.slug),
        },
        'government_functions': [f.name for f in department.get_govt_functions()],
        'intro': department.intro,
        'is_vote_primary': department.is_vote_primary,
        'name': department.name,
        'slug': str(department.slug),
        'sphere': {
            'name': department.government.sphere.name,
            'slug': department.government.sphere.slug,
        },
        'programmes': programmes,
        'selected_financial_year': financial_year_id,
        'selected_tab': 'departments',
        'title': "%s budget %s  - vulekamali" % (
            department.name, selected_year.slug),
        'description': "%s department: %s budget data for the %s financial year %s" % (
            description_govt,
            department.name,
            selected_year.slug,
            COMMON_DESCRIPTION_ENDING,
        ),
        'department_budget': department_budget,
        'department_adjusted_budget': department_adjusted_budget,
        'vote_number': department.vote_number,
        'vote_primary': {
            'url_path': primary_department.get_url_path(),
            'name': primary_department.name,
            'slug': primary_department.slug
        },
        'website_url': department.get_latest_website_url(),
    }

    response_yaml = yaml.safe_dump(context, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def dataset_category_list(request):
    context = {
        'categories': [category_fields(c) for c in Category.get_all()],
        'selected_tab': 'datasets',
        'slug': 'datasets',
        'name': 'Datasets and Analysis',
        'title': 'Datasets and Analysis - vulekamali',
        'url_path': '/datasets',
    }

    response_yaml = yaml.safe_dump(context, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def dataset_category(request, category_slug):
    category = Category.get_by_slug(category_slug)
    context = {
        'datasets': [],
        'selected_tab': 'datasets',
        'slug': category.slug,
        'name': category.name,
        'title': '%s - vulekamali' % category.name,
        'description': category.description,
        'url_path': category.get_url_path(),
    }

    for dataset in category.get_datasets():
        field_subset = dataset_fields(dataset)
        field_subset['description'] = field_subset.pop('intro')
        del field_subset['methodology']
        del field_subset['key_points']
        del field_subset['use_for']
        del field_subset['usage']
        context['datasets'].append(field_subset)

    response_yaml = yaml.safe_dump(context, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def dataset(request, category_slug, dataset_slug):
    dataset = Dataset.fetch(dataset_slug)
    assert(dataset.category.slug == category_slug)

    if category_slug == 'contributed':
        description = ("Data and/or documentation related to South African"
                       " government budgets contributed by %s and hosted"
                       " by National Treasury in partnership with IMALI YETHU"
        ) % dataset.get_organization()['name']
    else:
        description = dataset.intro

    context = {
        'selected_tab': 'datasets',
        'title': "%s - vulekamali" % dataset.name,
        'description': description,
    }

    context.update(dataset_fields(dataset))

    response_yaml = yaml.safe_dump(context, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def infrastructure_projects_overview(request):
    """ Overview page to showcase all featured infrastructure projects """
    infrastructure_projects = InfrastructureProject.get_featured_projects_from_resource()
    if infrastructure_projects is None:
        return HttpResponse(status=404)
    projects = []
    for project in infrastructure_projects:
        departments = Department.objects.filter(
            slug=slugify(project.department_name),
            government__sphere__slug='national'
        )
        department_url = None
        if departments:
            department_url = departments[0].get_latest_department_instance().get_url_path()

        projects.append({
            'name': project.name,
            'coordinates': project.cleaned_coordinates,
            'projected_budget': project.projected_expenditure,
            'stage': project.stage,
            'description': project.description,
            'provinces': project.get_provinces(),
            'total_budget': project.total_budget,
            'detail': project.get_url_path(),
            'dataset_url': InfrastructureProject.get_dataset().get_url_path(),
            'slug': project.get_url_path(),
            'page_title': '{} - vulekamali'.format(project.name),
            'department': {
                'name': project.department_name,
                'url': department_url,
                'budget_document': project.get_budget_document_url()
            },
            'nature_of_investment': project.nature_of_investment,
            'infrastructure_type': project.infrastructure_type,
            'expenditure': sorted(project.complete_expenditure, key=lambda e: e['year'])
        })
    projects = sorted(projects, key=lambda p: p['name'])
    response = {
        'dataset_url': InfrastructureProject.get_dataset().get_url_path(),
        'projects': projects,
        'description': 'Infrastructure projects in South Africa for 2019-20',
        'slug': 'infrastructure-projects',
        'selected_tab': 'infrastructure-projects',
        'title': 'Infrastructure Projects - vulekamali',
    }
    response_yaml = yaml.safe_dump(response, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def infrastructure_project_detail(request, project_slug):
    project = InfrastructureProject.get_project_from_resource(project_slug)
    if project is None:
        return HttpResponse(status=404)
    departments = Department.objects.filter(
        slug=slugify(project.department_name),
        government__sphere__slug='national'
    )
    department_url = None
    if departments:
        department_url = departments[0].get_latest_department_instance().get_url_path()

    project = {
        'dataset_url': InfrastructureProject.get_dataset().get_url_path(),
        'description': project.description,
        'selected_tab': 'infrastructure-projects',
        'slug': project.get_url_path(),
        'title': '{} - vulekamali'.format(project.name),
        'name': project.name,
        'coordinates': project.cleaned_coordinates,
        'projected_budget': project.projected_expenditure,
        'stage': project.stage,
        'department': {
            'name': project.department_name,
            'url': department_url,
            'budget_document': project.get_budget_document_url()
        },
        'provinces': project.get_provinces(),
        'total_budget': project.total_budget,
        'nature_of_investment': project.nature_of_investment,
        'infrastructure_type': project.infrastructure_type,
        'expenditure': sorted(project.complete_expenditure, key=lambda e: e['year'])
    }

    response_yaml = yaml.safe_dump(project, default_flow_style=False, encoding='utf-8')
    return HttpResponse(response_yaml, content_type='text/x-yaml')


def openspending_csv(request):
    """
    Ensure that API call is to OpenSpending *
    Get result from API call
    Feed dict result to CSV generator
    Return streaming http response
    :param request: HttpRequest
    :return: StreamingHttpResponse
    """
    api_url = urllib.unquote(str(request.GET.get('api_url')))

    parsed_url = urlparse.urlparse(api_url)
    domain = '{uri.netloc}'.format(uri=parsed_url)
    if domain != 'openspending.org':
        return HttpResponse("Invalid domain received: %s (Only openspending.org is allowed)" % domain,
                            status=403)

    result = requests.get(api_url)
    logger.info(
        "request %s took %dms",
        api_url,
        result.elapsed.microseconds / 1000
    )
    result.raise_for_status()
    if result.json()['total_cell_count'] > PAGE_SIZE:
        raise Exception("More cells than expected - perhaps we should start paging")
    return generate_csv_response(result.json())


def dataset_fields(dataset):
    return {
        'slug': dataset.slug,
        'name': dataset.name,
        'resources': [resource_fields(r) for r in dataset.resources],
        'organization': dataset.get_organization(),
        'author': dataset.author,
        'created': dataset.created_date,
        'last_updated': dataset.last_updated_date,
        'license': dataset.license,
        'intro': dataset.intro,
        'intro_short': dataset.intro_short,
        'key_points': dataset.key_points,
        'use_for': dataset.use_for,
        'usage': dataset.usage,
        'methodology': dataset.methodology,
        'url_path': dataset.get_url_path(),
        'category': category_fields(dataset.category),
    }


def resource_fields(resource):
    return {
        'name': resource['name'],
        'url': resource['url'],
        'description': resource['description'],
        'format': resource['format'],
    }


def category_fields(category):
    return {
        'name': category.name,
        'slug': category.slug,
        'url_path': category.get_url_path(),
        'description': category.description,
    }
