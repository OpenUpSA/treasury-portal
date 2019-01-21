"""
Abstracts away some of the mechanics of querying OpenSpending and some of the
conventions of how we name fields in our Fiscal Data Packages.
"""
import urllib

from collections import OrderedDict
from django.conf import settings
from django.core.cache import cache
from hashlib import sha1
import logging
import random
import requests
import re

logger = logging.getLogger(__name__)

PAGE_SIZE = 10000


class BabbageFiscalDataset():
    def __init__(self, model_url):
        self.session = requests.Session()

        self.cube_url = cube_url(model_url)
        model_result = self.session.get(model_url)
        logger.info("request to %s took %dms", model_url,
                    model_result.elapsed.microseconds / 1000)
        model_result.raise_for_status()
        self.model = model_result.json()['model']

    def get_dimension(self, hierarchy_name, level=0):
        return self.model['hierarchies'][hierarchy_name]['levels'][level]

    def get_ref(self, dimension_name, ref_type):
        return self.model['dimensions'][dimension_name][ref_type + "_ref"]

    def get_all_drilldowns(self):
        drilldowns = []
        for key, value in self.model['dimensions'].iteritems():
            drilldowns.append(self.get_ref(key, 'key'))
            drilldowns.append(self.get_ref(key, 'label'))
        # Enforce uniqueness
        # Enforce ordering to produce URLs more consistently to improve caching
        # and reduce diffs when written to file.
        return sorted(list(set(drilldowns)))

    @staticmethod
    def filter_by_ref_exclusion(cells, filter_ref, filter_exclusion_value):
        filtered_cells = filter(lambda cell: cell[filter_ref] != filter_exclusion_value, cells)
        return filtered_cells

    def aggregate_url(self, cuts=None, drilldowns=None, order=None):
        params = {
            'pagesize': PAGE_SIZE,
        }

        if settings.BUST_OPENSPENDING_CACHE:
            params['cache_bust'] = random.randint(1, 1000000)
        if cuts is not None and cuts:
            params['cut'] = "|".join(cuts)
        if drilldowns is not None:
            params['drilldown'] = "|".join(drilldowns)
        if order is not None:
            params['order'] = "|".join(order)
        url = self.cube_url + 'aggregate/'
        sorted_params = OrderedDict(sorted(params.items(), key=lambda t: t[0]))
        return url + '?' + urllib.urlencode(sorted_params)

    def aggregate(self, cuts=None, drilldowns=None, order=None):
        url = self.aggregate_url(cuts=cuts, drilldowns=drilldowns, order=order)
        cached_result = cache.get(cache_key(url))
        if cached_result:
            logger.info('cache HIT for %s', url)
            aggregate_result = cached_result
        else:
            logger.info('cache MISS for %s', url)
            aggregate_result = self.session.get(url)
            logger.info("request %s took %dms", aggregate_result.url,
                        aggregate_result.elapsed.microseconds / 1000)
            aggregate_result.raise_for_status()
            aggregate_result = aggregate_result.json()
            if aggregate_result['total_cell_count'] > PAGE_SIZE:
                raise Exception(
                    "More cells than expected - perhaps we should start paging"
                )
            cache.set(cache_key(url), aggregate_result)
        return aggregate_result

    def filter_dept(self, result, dept_name):
        filtered_results = []
        for budget in result['cells']:
            if budget[self.get_department_name_ref()] == dept_name:
                filtered_results.append(budget)
        return {'cells': filtered_results}

    @staticmethod
    def aggregate_by_ref(aggregate_ref_list, cells):
        """ Simulates a basic version of aggregation via Open Spending API
        Accepts a list of cells and a variable length list of column references. """
        assert isinstance(aggregate_ref_list, list)

        aggregated_cells = list()
        unique_reference_sets = list()
        for cell in cells:
            combo = [cell[ref] for ref in aggregate_ref_list]
            if combo not in unique_reference_sets:
                unique_reference_sets.append(combo)

        for unique_reference_set in unique_reference_sets:
            value_sum = 0
            count_sum = 0
            ex_cell = None
            for cell in cells:
                match = True
                for i in range(len(aggregate_ref_list)):
                    if not cell[aggregate_ref_list[i]] == unique_reference_set[i]:
                        match = False

                if match:
                    if not ex_cell:
                        ex_cell = {}
                        for i in range(len(aggregate_ref_list)):
                            ex_cell[aggregate_ref_list[i]] = cell[aggregate_ref_list[i]]
                    value_sum += cell['value.sum']
                    count_sum += cell['_count']
            ex_cell['value.sum'] = value_sum
            ex_cell['_count'] = count_sum
            aggregated_cells.append(ex_cell)
        return aggregated_cells


class EstimatesOfExpenditure(BabbageFiscalDataset):
    """
    This tries to provide a more semantic interface to Fiscal Data in
    the OpenSpending API than OpenSpending types.

    It makes assumptions about the OS Types we give Estimates of Expenditure
    columns, and the level of which hierarchy they end up in.
    """

    def get_programme_name_ref(self):
        return self.get_ref(self.get_programme_dimension(), 'label')

    def get_programme_number_ref(self):
        return self.get_ref(self.get_programme_dimension(), 'key')

    def get_programme_dimension(self):
        return self.get_dimension('activity')

    def get_subprogramme_name_ref(self):
        return self.get_ref(self.get_subprogramme_dimension(), 'label')

    def get_subprogramme_dimension(self):
        return self.get_dimension('activity', 1)

    def get_department_name_ref(self):
        return self.get_ref(self.get_department_dimension(), 'label')

    def get_vote_number_ref(self):
        return self.get_ref(self.get_department_dimension(), 'key')

    def get_department_dimension(self):
        return self.get_dimension('administrative_classification')

    def get_geo_ref(self):
        return self.get_ref(self.get_geo_dimension(), 'label')

    def get_geo_dimension(self):
        return self.get_dimension('geo_source')

    def get_financial_year_ref(self):
        return self.get_ref(self.get_financial_year_dimension(), 'label')

    def get_financial_year_dimension(self):
        return self.get_dimension('date')

    def get_function_ref(self):
        return self.get_ref(self.get_function_dimension(), 'label')

    def get_function_dimension(self):
        return self.get_dimension('functional_classification')

    def get_phase_ref(self):
        return self.get_ref(self.get_phase_dimension(), 'label')

    def get_phase_dimension(self):
        return self.get_dimension('phase')

    def get_econ_class_1_ref(self):
        return self.get_ref(self.get_econ_class_1_dimension(), 'key')

    def get_econ_class_1_dimension(self):
        return self.get_dimension('economic_classification')

    def get_econ_class_2_ref(self):
        return self.get_ref(self.get_econ_class_2_dimension(), 'key')

    def get_econ_class_2_dimension(self):
        return self.get_dimension('economic_classification', level=1)

    def get_econ_class_3_ref(self):
        return self.get_ref(self.get_econ_class_3_dimension(), 'key')

    def get_econ_class_3_dimension(self):
        return self.get_dimension('economic_classification', level=2)


class AdjustedEstimatesOfExpenditure(EstimatesOfExpenditure):

    def get_adjustment_kind_dimension(self):
        return self.get_dimension('value_kind')

    def get_adjustment_kind_ref(self):
        return self.get_ref(self.get_adjustment_kind_dimension(), 'label')


class ExpenditureTimeSeries(AdjustedEstimatesOfExpenditure):
    pass


def cube_url(model_url):
    return re.sub('model/?$', '', model_url)


def cache_key(url):
    return sha1(url).hexdigest()
