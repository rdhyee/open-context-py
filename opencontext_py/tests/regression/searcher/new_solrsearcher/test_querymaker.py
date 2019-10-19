import pytest
import logging
import random

from opencontext_py.apps.indexer.solrdocumentnew import SolrDocumentNew as SolrDocument

from opencontext_py.apps.searcher.new_solrsearcher import querymaker

logger = logging.getLogger("tests-regression-logger")


TESTS_SPATIAL_CONTEXTS = [
    # Tuples of test cases, with input spatial context path
    # and expected output dicts:
    #
    # (spatial_context, expected_query_dict),
    #
    (
        None,
        {
           'fq':[],
           'facet.field':[SolrDocument.ROOT_CONTEXT_SOLR],
        },
    ),
    (
        'United+States',
        {
           'fq':['root___context_id_fq:united-states'],
           'facet.field':['united_states___context_id'],
        },
    ),
    (
        'United States',
        {
           'fq':['root___context_id_fq:united-states'],
           'facet.field':['united_states___context_id'],
        },
    ),
    (
        'United States/',
        {
           'fq':['root___context_id_fq:united-states'],
           'facet.field':['united_states___context_id'],
        },
    ),
    (
        '/United States',
        {
           'fq':['root___context_id_fq:united-states'],
           'facet.field':['united_states___context_id'],
        },
    ),
    (
        '/United States||',
        {
           'fq':['root___context_id_fq:united-states'],
           'facet.field':['united_states___context_id'],
        },
    ),
    (
        'United States/California',
        {
           'fq':['united_states___context_id_fq:california'],
           'facet.field':['california___context_id'],
        },
    ),
    
    # Test case where Foo Bar are parts of context paths that do
    # not exist
    (
        'United States/California||Foo Bar',
        {
           'fq':['united_states___context_id_fq:california'],
           'facet.field':['california___context_id'],
        },
    ),
    
    # Test case where Foo and Bar are parts of context paths that do
    # not exist
    (
        'United States||Foo-Bar/California||Foo Bar',
        {
           'fq':['united_states___context_id_fq:california'],
           'facet.field':['california___context_id'],
        },
    ),
    (
        'United States/California||Florida',
        {
           'fq':['((united_states___context_id_fq:california) OR (united_states___context_id_fq:florida))'],
           'facet.field':['california___context_id', 'florida___context_id',],
        },
    ),
    
    # The following test case highlights how the solr query uses slugs
    # like "24-poggio-civitate" and "24-civitate-a" as identifiers.
    # Translanding a context path string into a solr query requires
    # use of the database to look up the corresponding slugs assigned
    # to the spatial context (subjects) entities being queried. 
    (
        'Italy/Poggio+Civitate/Civitate+A',
        {
           'fq':['24_poggio_civitate___context_id_fq:24-civitate-a'],
           'facet.field':['24_civitate_a___context_id',],
        },
    ),
]


TESTS_PROJECTS = [
    
    (
        None,
        None,
    ),
    (
        '',
        None,
    ),
    (
        'Foo',
        None,
    ),
    (
        'Murlo||Foo',
        None,
    ),
    (
        '24-murlo',
        {
            'fq': ['((root___project_id_fq:24-murlo) AND (obj_all___project_id_fq:24-murlo))',],
            'facet.field':['24_murlo___project_id',],
        }
    ),
    (
        '24-murlo||foo',
        {
            'fq': ['((root___project_id_fq:24-murlo) AND (obj_all___project_id_fq:24-murlo))',],
            'facet.field':['24_murlo___project_id',],
        }
    ),
    (
        '24-murlo---foo',
        None,
    ),
    (
        'foo---24-murlo',
        None,
    ),
    (
        '52-digital-index-of-north-american-archaeology-dinaa',
        {
            'fq': ['((root___project_id_fq:52-digital-index-of-north-american-archaeology-dinaa) AND (obj_all___project_id_fq:52-digital-index-of-north-american-archaeology-dinaa))',],
            'facet.field':['52_digital_index_of_north_american_archaeology_dinaa___project_id',],
        }
    ),
    # Example of a sub-project
    (
        '52-digital-index-of-north-american-archaeology-linking-si',
        {
            'fq': ['((52_digital_index_of_north_american_archaeology_dinaa___project_id_fq:52-digital-index-of-north-american-archaeology-linking-si) AND (obj_all___project_id_fq:52-digital-index-of-north-american-archaeology-linking-si))',],
            'facet.field':['52_digital_index_of_north_american_archaeology_linking_si___project_id',],
        }
    ),
    (
        '52-digital-index-of-north-american-archaeology-dinaa---52-digital-index-of-north-american-archaeology-linking-si',
        {
            'fq': ['((root___project_id_fq:52-digital-index-of-north-american-archaeology-dinaa) AND (obj_all___project_id_fq:52-digital-index-of-north-american-archaeology-dinaa) AND (52_digital_index_of_north_american_archaeology_dinaa___project_id_fq:52-digital-index-of-north-american-archaeology-linking-si) AND (obj_all___project_id_fq:52-digital-index-of-north-american-archaeology-linking-si))'],
            'facet.field':['52_digital_index_of_north_american_archaeology_linking_si___project_id',],
        }
    ),
]


@pytest.mark.django_db
def test_get_spatial_context_query_dict():
    """Tests get_spatial_context_query_dict on a variety of inputs."""
    for spatial_context, exp_dict in TESTS_SPATIAL_CONTEXTS:
        query_dict = querymaker.get_spatial_context_query_dict(
            spatial_context
        )
        assert query_dict['fq'] == exp_dict['fq']
        assert query_dict['facet.field'] == exp_dict['facet.field']


@pytest.mark.django_db
def test_get_projects_query_dict():
    """Tests get_spatial_context_query_dict on a variety of inputs."""
    for raw_projects_path, exp_dict in TESTS_PROJECTS:
        query_dict = querymaker.get_projects_query_dict(
            raw_projects_path
        )
        if query_dict is None:
            # Case where we don't have a dict response.
            assert query_dict == exp_dict
            continue
        assert query_dict['fq'] == exp_dict['fq']
        assert query_dict['facet.field'] == exp_dict['facet.field']
