"""
Tests of models.Department
"""
import mock

from budgetportal.models import (
    FinancialYear,
    Sphere,
    Government,
    Department,
)
from budgetportal import models
from django.test import TestCase
from mock import Mock
import json

with open('budgetportal/tests/test_data/budget_and_actual.json', 'r') as DEPARTMENT_MOCK_DATA:
    DEPARTMENT_MOCK_DATA = json.load(DEPARTMENT_MOCK_DATA)

with open('budgetportal/tests/test_data/test_treemap_expenditure_national.json', 'r') as TREEMAP_MOCK_DATA:
    TREEMAP_MOCK_DATA = json.load(TREEMAP_MOCK_DATA)

with open('budgetportal/tests/test_data/test_national_department_preview.json', 'r') as NATIONAL_DEPARTMENT_PREVIEW_MOCK_DATA:
    NATIONAL_DEPARTMENT_PREVIEW_MOCK_DATA = json.load(NATIONAL_DEPARTMENT_PREVIEW_MOCK_DATA)


class AdjustedBudgetMissingTestCase(TestCase):
    """Unit tests of adjusted budget data summary for a department"""

    def setUp(self):
        year = FinancialYear(slug="2030-31")
        sphere = Sphere(financial_year=year, name="A sphere")
        government = Government(sphere=sphere, name="A government")
        self.department = Department(
            government=government,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
        )
        self.department.get_adjusted_estimates_expenditure_dataset = Mock(return_value=None)

    def test_missing_dataset(self):
        self.assertEqual(self.department.get_adjusted_budget_summary(), None)


class AdjustedBudgetOpenSpendingMissingTestCase(TestCase):
    """Unit tests of adjusted budget data summary for a department"""

    def setUp(self):
        year = FinancialYear(slug="2030-31")
        sphere = Sphere(financial_year=year, name="A sphere")
        government = Government(sphere=sphere, name="A government")
        self.department = Department(
            government=government,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
        )
        mock_dataset = Mock()
        mock_dataset.get_openspending_api = Mock(return_value=None)
        self.department.get_adjusted_estimates_expenditure_dataset = Mock(return_value=mock_dataset)

    def test_missing_openspending_dataset(self):
        self.assertEqual(self.department.get_adjusted_budget_summary(), None)


class AdjustedBudgetTestCase(TestCase):
    """Unit tests of adjusted budget data summary for a department"""

    def setUp(self):
        year = FinancialYear(slug="2030-31")
        sphere = Sphere(financial_year=year, name="A sphere")
        government = Government(sphere=sphere, name="A government")
        self.department = Department(
            government=government,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
        )
        mock_dataset = Mock()
        mock_openspending_api = Mock()
        self.mock_openspending_api = mock_openspending_api
        mock_openspending_api.get_adjustment_kind_ref = Mock
        mock_openspending_api.get_phase_ref = Mock
        mock_openspending_api.get_programme_name_ref = Mock
        mock_openspending_api.get_department_name_ref = Mock(return_value='department_name_ref')
        mock_openspending_api.get_financial_year_ref = Mock(return_value="financial_year_ref")
        mock_openspending_api.aggregate = Mock
        mock_openspending_api.filter_dept = Mock(return_value={'cells': []})
        mock_openspending_api.filter_by_ref_exclusion = Mock
        mock_openspending_api.aggregate_by_refs = Mock
        mock_openspending_api.aggregate_url = Mock
        mock_dataset.get_openspending_api = Mock(return_value=mock_openspending_api)
        self.department.get_adjusted_estimates_expenditure_dataset = Mock(return_value=mock_dataset)
        self.department.get_financial_year = Mock(return_value=year)
        self.department._get_adjustments_by_econ_class = Mock(return_value=Mock())
        self.department._get_adjustments_by_programme = Mock(return_value=Mock())
        self.department._get_adjustments_by_type = Mock(return_value=Mock())
        self.department._get_budget_virements = Mock(return_value=Mock())
        self.department._get_budget_special_appropriations = Mock(return_value=Mock())
        self.department._get_budget_direct_charges = Mock(return_value=Mock())
        models.csv_url = Mock(return_value=Mock())

    def test_no_adjustment(self):
        self.department._get_total_budget_adjustment = Mock(return_value=(123, 0))
        result = self.department.get_adjusted_budget_summary()
        self.assertEqual(result['total_change']['amount'], 0)
        self.assertEqual(result['total_change']['percentage'], 0)

    def test_adjustment(self):
        self.department._get_total_budget_adjustment = Mock(return_value=(100, 11))
        result = self.department.get_adjusted_budget_summary()
        self.assertEqual(result['total_change']['amount'], 11)
        self.assertEqual(result['total_change']['percentage'], 11)


class BudgetedAndActualExpenditureProgrammeTestCase(TestCase):
    """Unit tests of budgeted and actual expenditure summary for a department"""

    def setUp(self):
        self.mock_data = DEPARTMENT_MOCK_DATA
        year = FinancialYear(slug="2018-19")
        sphere = Sphere(financial_year=year, name="A sphere")
        government = Government(sphere=sphere, name="A government")
        self.department = Department(
            government=government,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
        )
        mock_dataset = Mock()
        self.mock_openspending_api = Mock()
        self.mock_openspending_api.get_adjustment_kind_ref = Mock(return_value='adjustment_kind_ref')
        self.mock_openspending_api.get_phase_ref = Mock(return_value='budget_phase.budget_phase')
        self.mock_openspending_api.get_programme_name_ref = Mock(return_value='programme_number.programme')
        self.mock_openspending_api.get_department_name_ref = Mock(return_value='department_name_ref')
        self.mock_openspending_api.get_financial_year_ref = Mock(return_value="financial_year.financial_year")
        self.mock_openspending_api.aggregate = Mock(return_value={'cells': [{'value.sum': 1, '_count': 0}]})
        self.mock_openspending_api.filter_dept = Mock(return_value={'cells': self.mock_data['program_test_cells_complete']})
        self.mock_openspending_api.aggregate_url = Mock
        mock_dataset.get_openspending_api = Mock(return_value=self.mock_openspending_api)
        self.department.get_expenditure_time_series_dataset = Mock(return_value=mock_dataset)
        self.department.get_financial_year = Mock(return_value=year)

    def test_no_cells_null_response(self):
        self.mock_openspending_api.filter_dept = Mock(return_value={'cells': []})
        result = self.department.get_expenditure_time_series_by_programme()
        self.assertEqual(result, None)

    def test_complete_data_no_notices(self):
        result = self.department.get_expenditure_time_series_by_programme()
        self.assertEqual(result['notices'], [])

    def test_missing_data_prog_did_not_exist(self):
        """ Here we feed an incomplete set of cells and expect it to tell us that the department did not exist
        (removed 2018 data) """
        self.mock_openspending_api.aggregate = Mock(return_value={'cells': [{'value.sum': 1, '_count': 0}]})
        self.mock_openspending_api.filter_dept = Mock(return_value={'cells': self.mock_data['program_test_cells_missing_2018_revenue_admin']})
        result = self.department.get_expenditure_time_series_by_programme()
        self.assertEqual(result['notices'], ['One or more programmes did not exist for some years displayed.'])


class BudgetedAndActualExpenditureSummaryTestCase(TestCase):
    """Unit tests of budgeted and actual expenditure summary for a department"""

    def setUp(self):
        self.mock_data = DEPARTMENT_MOCK_DATA
        year = FinancialYear(slug="2018-19")
        sphere = Sphere(financial_year=year, name="A sphere")
        government = Government(sphere=sphere, name="A government")
        self.department = Department(
            government=government,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
        )
        mock_dataset = Mock()
        self.mock_openspending_api = Mock()
        self.mock_openspending_api.get_adjustment_kind_ref = Mock(return_value='adjustment_kind_ref')
        self.mock_openspending_api.get_phase_ref = Mock(return_value='budget_phase.budget_phase')
        self.mock_openspending_api.get_programme_name_ref = Mock
        self.mock_openspending_api.get_department_name_ref = Mock(return_value='department_name_ref')
        self.mock_openspending_api.get_financial_year_ref = Mock(return_value="financial_year.financial_year")
        self.mock_openspending_api.aggregate = Mock(return_value={'cells': [{'value.sum': 1, '_count': 0}]})
        self.mock_openspending_api.filter_dept = Mock(return_value={'cells': []})
        self.mock_openspending_api.filter_by_ref_exclusion = Mock
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=self.mock_data['test_cells_data_complete'])
        self.mock_openspending_api.aggregate_url = Mock
        mock_dataset.get_openspending_api = Mock(return_value=self.mock_openspending_api)
        self.department.get_expenditure_time_series_dataset = Mock(return_value=mock_dataset)
        self.department.get_financial_year = Mock(return_value=year)

    def test_no_cells_null_response(self):
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=[])
        result = self.department.get_expenditure_time_series_summary()
        self.assertEqual(result, None)

    def test_complete_data_no_notices(self):
        result = self.department.get_expenditure_time_series_summary()
        self.assertEqual(result['notices'], [])

    def test_missing_data_not_published(self):
        """ Here we feed an incomplete set of cells and expect it to tell us that 2018 data has not been published """
        self.mock_openspending_api.aggregate = Mock(return_value={'cells': [{'value.sum': 0, '_count': 0}]})
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=self.mock_data['test_cells_data_missing_2018'])
        result = self.department.get_expenditure_time_series_summary()
        self.assertEqual(result['notices'], ['Please note that the data for 2018 has not been published on vulekamali.'])

    def test_missing_data_dept_did_not_exist(self):
        """ Here we feed an incomplete set of cells and expect it to tell us that the department did not exist
        (removed 2018 data) """
        self.mock_openspending_api.aggregate = Mock(return_value={'cells': [{'value.sum': 1, '_count': 0}]})
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=self.mock_data['test_cells_data_missing_2018'])
        result = self.department.get_expenditure_time_series_summary()
        self.assertEqual(result['notices'], ['This department did not exist for some years displayed.'])


class DepartmentWebsiteUrlTestCase(TestCase):
    """ Integration test to verify that website urls are retrieved and output correctly """

    def setUp(self):
        year_old = FinancialYear.objects.create(slug="2017-18")
        year_new = FinancialYear.objects.create(slug="2018-19")
        sphere_old = Sphere.objects.create(financial_year=year_old, name="A sphere")
        sphere_new = Sphere.objects.create(financial_year=year_new, name="A sphere")
        government_old = Government.objects.create(sphere=sphere_old, name="A government")
        government_new = Government.objects.create(sphere=sphere_new, name="A government")
        self.department = Department.objects.create(
            government=government_old,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
            website_url='https://governmentwebsite.co.za',
        )
        self.new_department = Department.objects.create(
            government=government_new,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
            website_url=None,
        )

    def test_website_url_always_returns_latest_department_year(self):
        """ Make sure that any given department for any given year always returns the website url of the
        latest department instance in that sphere, where it is not null """
        self.assertEqual(self.department.get_latest_website_url(), 'https://governmentwebsite.co.za')
        new_url = 'https://newwebsite.com'
        self.new_department.website_url = new_url
        self.new_department.save()
        self.assertEqual(self.department.get_latest_website_url(), new_url)


class NationalTreemapExpenditureByDepartmentTestCase(TestCase):
    """ Unit tests for the treemap expenditure by department function. """

    def setUp(self):
        self.mock_data = TREEMAP_MOCK_DATA
        year = FinancialYear.objects.create(slug="2019-20")
        sphere = Sphere.objects.create(financial_year=year, name="national")
        government = Government.objects.create(sphere=sphere, name="A government")
        self.department = Department(
            government=government,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
        )
        mock_dataset = Mock()
        self.mock_openspending_api = Mock()
        self.mock_openspending_api.get_adjustment_kind_ref = Mock(return_value='adjustment_kind_ref')
        self.mock_openspending_api.get_phase_ref = Mock(return_value='budget_phase.budget_phase')
        self.mock_openspending_api.get_programme_name_ref = Mock(return_value='programme_number.programme')
        self.mock_openspending_api.get_department_name_ref = Mock(return_value='vote_number.department')
        self.mock_openspending_api.get_financial_year_ref = Mock(return_value="financial_year.financial_year")
        self.mock_openspending_api.aggregate = Mock(return_value={'cells': [{'value.sum': 1, '_count': 0}]})
        self.mock_openspending_api.filter_by_ref_exclusion = Mock
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=self.mock_data['complete'])
        self.mock_openspending_api.aggregate_url = Mock
        mock_dataset.get_openspending_api = Mock(return_value=self.mock_openspending_api)
        self.department.get_expenditure_time_series_dataset = Mock(return_value=mock_dataset)

        vote_number = 1
        for mock_object in self.mock_data['complete']:
            Department.objects.create(
                government=government,
                is_vote_primary=True,
                name=mock_object['vote_number.department'],
                vote_number=vote_number
            )
            vote_number += 1

    @mock.patch('budgetportal.models.Department.get_all_budget_totals_by_year_and_phase', return_value=mock.MagicMock())
    def test_no_cells_null_response(self, total_budgets_mock):
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=[])
        result = self.department.get_national_expenditure_treemap(financial_year_id='2018-19', budget_phase='original')
        self.assertEqual(result, None)

    @mock.patch('budgetportal.models.Department.get_all_budget_totals_by_year_and_phase', return_value=mock.MagicMock())
    def test_complete_data(self, total_budgets_mock):
        result = self.department.get_national_expenditure_treemap(financial_year_id='2019-20', budget_phase='original')
        data = result['data']
        self.assertEqual(len(data), 2)
        data_keys = data.keys()
        self.assertIn('items', data_keys)
        self.assertIn('total', data_keys)
        expenditure_keys = data['items'][0].keys()
        self.assertIn('name', expenditure_keys)
        self.assertIn('amount', expenditure_keys)
        self.assertIn('percentage_of_total', expenditure_keys)
        self.assertIn('url', expenditure_keys)
        self.assertIn('province', expenditure_keys)


class NationalDepartmentPreviewTestCase(TestCase):
    """ Unit tests for the national department preview department function. """

    def setUp(self):
        self.mock_data = NATIONAL_DEPARTMENT_PREVIEW_MOCK_DATA
        year = FinancialYear.objects.create(slug="2019-20")
        sphere = Sphere.objects.create(financial_year=year, name="national")
        government = Government.objects.create(sphere=sphere, name="South Africa")
        self.department = Department(
            government=government,
            name="Fake",
            vote_number=1,
            is_vote_primary=True,
            intro="",
        )
        mock_dataset = Mock()
        self.mock_openspending_api = Mock()
        self.mock_openspending_api.get_adjustment_kind_ref = Mock(return_value='adjustment_kind_ref')
        self.mock_openspending_api.get_phase_ref = Mock(return_value='budget_phase.budget_phase')
        self.mock_openspending_api.get_programme_name_ref = Mock(return_value='programme_number.programme')
        self.mock_openspending_api.get_department_name_ref = Mock(return_value='vote_number.department')
        self.mock_openspending_api.get_geo_ref = Mock(return_value='government.government')
        self.mock_openspending_api.get_financial_year_ref = Mock(return_value="financial_year.financial_year")
        self.mock_openspending_api.aggregate = Mock(return_value={'cells': [{'value.sum': 1, '_count': 0}]})
        self.mock_openspending_api.filter_by_ref_exclusion = Mock(return_value=self.mock_data['programmes'])
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=self.mock_data['departments'])
        self.mock_openspending_api.aggregate_url = Mock
        mock_dataset.get_openspending_api = Mock(return_value=self.mock_openspending_api)
        self.department.get_expenditure_time_series_dataset = Mock(return_value=mock_dataset)

        vote_number = 1
        for mock_object in self.mock_data['departments']:
            Department.objects.create(
                government=government,
                is_vote_primary=True,
                name=mock_object['vote_number.department'],
                vote_number=vote_number
            )
            vote_number += 1

    @mock.patch('budgetportal.models.Department.get_all_budget_totals_by_year_and_phase', return_value=mock.MagicMock())
    def test_no_cells_null_response(self, total_budgets_mock):
        self.mock_openspending_api.aggregate_by_refs = Mock(return_value=[])
        result = self.department.get_national_expenditure_treemap(financial_year_id='2018-19', budget_phase='original')
        self.assertEqual(result, None)

    @mock.patch('budgetportal.models.Department.get_all_budget_totals_by_year_and_phase', return_value=mock.MagicMock())
    def test_complete_data(self, total_budgets_mock):
        result = self.department.get_preview_page(financial_year_id='2019-20', phase_slug='original',
                                                  government_slug='south-africa', sphere_slug='national')
        data = result['data']
        self.assertEqual(len(data), 1)
        data_keys = data.keys()
        self.assertIn('items', data_keys)
        expenditure_keys = data['items'][0].keys()
        self.assertIn('title', expenditure_keys)
        self.assertIn('description', expenditure_keys)
        self.assertIn('percentage_of_budget', expenditure_keys)
        self.assertIn('programmes', expenditure_keys)
        self.assertIn('slug', expenditure_keys)
