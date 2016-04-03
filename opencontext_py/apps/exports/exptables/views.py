import json
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse, Http404
from opencontext_py.libs.rootpath import RootPath
from opencontext_py.libs.requestnegotiation import RequestNegotiation
from opencontext_py.apps.exports.exptables.models import ExpTable
from opencontext_py.apps.exports.exptables.templating import ExpTableTemplating
from django.template import RequestContext, loader
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache


# An table item caches a list of uuids, along with record values (as string literals)
# of attributes for download as a CSV file. It does some violence to the more
# elaborately structured aspects of Open Context's data model, but is convenient
# for most researchers.
@cache_control(no_cache=True)
@never_cache
def index_view(request, table_id=None):
    """ Get the search context JSON-LD """
    rp = RootPath()
    base_url = rp.get_baseurl()
    req_neg = RequestNegotiation('text/html')
    if 'HTTP_ACCEPT' in request.META:
        req_neg.check_request_support(request.META['HTTP_ACCEPT'])
    if req_neg.supported:
        # requester wanted a mimetype we DO support
        template = loader.get_template('tables/index.html')
        context = RequestContext(request,
                                 {'base_url': base_url,
                                  'page_title': 'Open Context: Tables',
                                  'act_nav': 'tables',
                                  'nav_items': settings.NAV_ITEMS})
        return HttpResponse(template.render(context))
    else:
        # client wanted a mimetype we don't support
        return HttpResponse(req_neg.error_message,
                            status=415)


@cache_control(no_cache=True)
@never_cache
def html_view(request, table_id):
    exp_tt = ExpTableTemplating(table_id)
    rp = RootPath()
    base_url = rp.get_baseurl()
    if exp_tt.exp_tab is not False:
        exp_tt.prep_html()
        template = loader.get_template('tables/temp.html')
        if exp_tt.view_permitted:
            req_neg = RequestNegotiation('text/html')
            req_neg.supported_types = ['application/json',
                                       'application/ld+json',
                                       'text/csv']
            if 'HTTP_ACCEPT' in request.META:
                req_neg.check_request_support(request.META['HTTP_ACCEPT'])
            if req_neg.supported:
                if 'json' in req_neg.use_response_type:
                    # content negotiation requested JSON or JSON-LD
                    return HttpResponse(json.dumps(ocitem.json_ld,
                                        ensure_ascii=False, indent=4),
                                        content_type=req_neg.use_response_type + "; charset=utf8")
                elif 'csv' in req_neg.use_response_type:
                    return redirect(exp_tt.csv_url, permanent=False)
                else:
                    context = RequestContext(request,
                                             {'item': exp_tt,
                                              'base_url': base_url})
                    return HttpResponse(template.render(context))
            else:
                # client wanted a mimetype we don't support
                return HttpResponse(req_neg.error_message,
                                    content_type=req_neg.use_response_type + "; charset=utf8",
                                    status=415)
        else:
            template = loader.get_template('items/view401.html')
            context = RequestContext(request,
                                     {'item': temp_item,
                                      'base_url': base_url})
            return HttpResponse(template.render(context), status=401)
    else:
        # raise Http404
        template = loader.get_template('tables/index.html')
        context = RequestContext(request,
                                 {'base_url': base_url,
                                  'page_title': 'Open Context: Tables',
                                  'act_nav': 'tables',
                                  'nav_items': settings.NAV_ITEMS})
        return HttpResponse(template.render(context))


def json_view(request, table_id):
    exp_tt = ExpTableTemplating(table_id)
    if exp_tt.exp_tab is not False:
        json_ld = exp_tt.make_json_ld()
        req_neg = RequestNegotiation('application/json')
        req_neg.supported_types = ['application/ld+json']
        if 'HTTP_ACCEPT' in request.META:
            req_neg.check_request_support(request.META['HTTP_ACCEPT'])
        if req_neg.supported:
            json_output = json.dumps(json_ld,
                                     indent=4,
                                     ensure_ascii=False)
            return HttpResponse(json_output,
                                content_type=req_neg.use_response_type + "; charset=utf8")
        else:
            # client wanted a mimetype we don't support
            return HttpResponse(req_neg.error_message,
                                content_type=req_neg.use_response_type + "; charset=utf8",
                                status=415)
    else:
        raise Http404


def csv_view(request, table_id):
    exp_tt = ExpTableTemplating(table_id)
    if exp_tt.exp_tab is not False:
        exp_tt.prep_csv()
        req_neg = RequestNegotiation('text/csv')
        if 'HTTP_ACCEPT' in request.META:
            req_neg.check_request_support(request.META['HTTP_ACCEPT'])
        if req_neg.supported:
            return redirect(exp_tt.csv_url, permanent=False)
        else:
            # client wanted a mimetype we don't support
            return HttpResponse(req_neg.error_message,
                                content_type=req_neg.use_response_type + "; charset=utf8",
                                status=415)
    else:
        raise Http404
