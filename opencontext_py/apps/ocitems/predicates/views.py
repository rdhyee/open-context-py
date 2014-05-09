from django.http import HttpResponse
from opencontext_py.apps.ocitems.predicates.models import Predicate
import json


# A predicate is a descriptive variable or linking relation that originates from
# an Open Context contributor
# The main dependency for this app is for OCitems, which are used to generate
# Every type of item in Open Context, including subjects
def index(request):
    return HttpResponse("Hello, world. You're at the predicates index.")


def html_view(request, uuid):
    try:
        actItem = Predicate.objects.get(uuid=uuid)
        return HttpResponse("Hello, world. You're at the predicates htmlView of " + str(uuid))
    except Predicate.DoesNotExist:
        raise Http404


def json_view(request, uuid):
    try:
        act_item = Predicate.objects.get(uuid=uuid)
        act_item.get_item()
        json_output = json.dumps(act_item.ocitem.json_ld, indent=4)
        return HttpResponse(json_output, mimetype='application/json')
    except Predicate.DoesNotExist:
        raise Http404
