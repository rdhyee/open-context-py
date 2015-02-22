import json
from django.conf import settings
from django.http import HttpResponse, Http404
from django.template import RequestContext, loader
from opencontext_py.libs.solrconnection import SolrConnection
from opencontext_py.libs.general import LastUpdatedOrderedDict
from opencontext_py.apps.searcher.solrsearcher.models import SolrSearch
from opencontext_py.apps.searcher.solrsearcher.makejsonld import MakeJsonLd
from opencontext_py.apps.searcher.solrsearcher.filterlinks import FilterLinks
from opencontext_py.apps.searcher.solrsearcher.templating import SearchTemplate
from opencontext_py.apps.searcher.solrsearcher.requestdict import RequestDict


def index(request, spatial_context=None):
    return HttpResponse("Hello, world. You're at the sets index.")


def html_view(request, spatial_context=None):
    rd = RequestDict()
    request_dict_json = rd.make_request_dict_json(request,
                                                  spatial_context)
    solr_s = SolrSearch()
    if solr_s.solr is not False:
        response = solr_s.search_solr(request_dict_json)
        m_json_ld = MakeJsonLd(request_dict_json)
        # share entities already looked up. Saves database queries
        m_json_ld.entities = solr_s.entities
        m_json_ld.request_full_path = request.get_full_path()
        m_json_ld.spatial_context = spatial_context
        json_ld = m_json_ld.convert_solr_json(response.raw_content)
        # now make the JSON-LD into an object suitable for HTML templating
        st = SearchTemplate(json_ld)
        st.process_json_ld()
        template = loader.get_template('sets/view.html')
        context = RequestContext(request,
                                 {'st': st})
        return HttpResponse(template.render(context))
    else:
        template = loader.get_template('500.html')
        context = RequestContext(request,
                                 {'error': 'Solr Connection Problem'})
        return HttpResponse(template.render(context), status=503)


def json_view(request, spatial_context=None):
    """ API for searching Open Context """
    rd = RequestDict()
    request_dict_json = rd.make_request_dict_json(request,
                                                  spatial_context)
    solr_s = SolrSearch()
    if solr_s.solr is not False:
        response = solr_s.search_solr(request_dict_json)
        m_json_ld = MakeJsonLd(request_dict_json)
        # share entities already looked up. Saves database queries
        m_json_ld.entities = solr_s.entities
        m_json_ld.request_full_path = request.get_full_path()
        m_json_ld.spatial_context = spatial_context
        json_ld = m_json_ld.convert_solr_json(response.raw_content)
        return HttpResponse(json.dumps(json_ld,
                            ensure_ascii=False, indent=4),
                            content_type="application/json; charset=utf8")
    else:
        template = loader.get_template('500.html')
        context = RequestContext(request,
                                 {'error': 'Solr Connection Problem'})
        return HttpResponse(template.render(context), status=503)

