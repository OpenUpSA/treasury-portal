from adminplus.sites import AdminSitePlus

from budgetportal.views import openspending_csv
from discourse.views import sso
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.views.decorators.cache import cache_page
from . import views
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from . import bulk_upload

admin.site = AdminSitePlus()
admin.autodiscover()

CACHE_SECS = 0


def permission_denied(request):
    raise PermissionDenied()


urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html')),

    # National and provincial treemap data
    url(r'^(?P<financial_year_id>\d{4}-\d{2})'
        '/(?P<sphere_slug>[\w-]+)'
        '/(?P<phase_slug>[\w-]+).yaml$', cache_page(CACHE_SECS)(views.homepage)),

    # Preview pages
    url(r'^(?P<financial_year_id>\d{4}-\d{2})'
        '/previews'
        '/(?P<sphere_slug>[\w-]+)'
        '/(?P<government_slug>[\w-]+)'
        '/(?P<phase_slug>[\w-]+).yaml$', cache_page(CACHE_SECS)(views.department_preview)),

    # Home Page
    url(r'^(?P<financial_year_id>\d{4}-\d{2}).yaml$',
        cache_page(CACHE_SECS)(views.year_home)),

    # Search results
    url(r'^(?P<financial_year_id>\d{4}-\d{2})/search-result.yaml',
        cache_page(CACHE_SECS)(views.FinancialYearPage.as_view(
            slug='search-result',
        ))),

    # Department List
    url(r'^(?P<financial_year_id>\d{4}-\d{2})'
        '/departments.yaml', cache_page(CACHE_SECS)(views.department_list)),

    # Department list as CSV
    url(r'^(?P<financial_year_id>\d{4}-\d{2})'
        '/departments.csv$', cache_page(CACHE_SECS)(views.department_list_csv)),

    # Programme list as CSV
    url(r'^(?P<financial_year_id>\d{4}-\d{2})'
        '/(?P<sphere_slug>[\w-]+)'
        '/programmes.csv$', cache_page(CACHE_SECS)(views.programme_list_csv)),

    # Department
    url(r'^(?P<financial_year_id>\d{4}-\d{2})'
        '/national'
        '/departments'
        '/(?P<department_slug>[\w-]+).yaml$', cache_page(CACHE_SECS)(views.department),
        kwargs={'sphere_slug': 'national', 'government_slug': 'south-africa'}),
    url(r'^(?P<financial_year_id>[\w-]+)'
        '/(?P<sphere_slug>[\w-]+)'
        '/(?P<government_slug>[\w-]+)'
        '/departments'
        '/(?P<department_slug>[\w-]+).yaml$', cache_page(CACHE_SECS)(views.department)),


    url(r'^datasets.yaml$', cache_page(CACHE_SECS)(views.dataset_category_list)),
    url(r'^infrastructure-projects.yaml$', cache_page(CACHE_SECS)(views.infrastructure_projects_overview)),
    url(r'^infrastructure-projects/(?P<project_slug>[\w-]+).yaml$', cache_page(CACHE_SECS)(views.infrastructure_project_detail)),
    url(r'^datasets'
        '/(?P<category_slug>[\w-]+).yaml$', cache_page(CACHE_SECS)(views.dataset_category)),
    url(r'^datasets'
        '/(?P<category_slug>[\w-]+)'
        '/(?P<dataset_slug>[\w-]+).yaml$', cache_page(CACHE_SECS)(views.dataset)),

    # Authentication
    url(r'^accounts/email.*', permission_denied),
    url(r'^accounts/', include('allauth.urls')),

    # SSO Provider
    url(r'^(?P<client_id>\w+)/sso$', sso),

    # CSV
    url(r'^csv/$', openspending_csv, name='openspending_csv'),

    # Admin
    url(r'^admin/', admin.site.urls),
    url(r'^admin/bulk_upload/template', bulk_upload.template_view),

]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
