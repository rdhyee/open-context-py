import json
import requests
from django.db import models
from django.conf import settings
from opencontext_py.apps.searcher.solrsearcher.solrdirect import SolrDirect
from opencontext_py.apps.indexer.crawler import Crawler
from opencontext_py.apps.ocitems.manifest.models import Manifest
from opencontext_py.apps.ocitems.assertions.models import Assertion
from opencontext_py.apps.ldata.linkannotations.models import LinkAnnotation


class SolrReIndex():
    """ This class contains methods to make updates to
        the solr index especially after edits
    """

    def __init__(self):
        self.uuids = []
        self.iteration = 0
        self.recursive = True
        # maximum number of times to iterate and make requests
        self.max_iterations = 100
        # if not false, get uuids by directly requsting JSON from solr
        self.solr_direct_url = False
        # if not false, use a request to Open Context to generate a
        # solr request to get UUIDs
        self.oc_url = False
        # if not false, use a dictionary of paramaters with Open Context
        # to generate a solr request to get UUIDs
        self.oc_params = False
        # if not false, use a Postgres SQL query to get a list of
        # UUIDs of items annotated after a certain date
        self.annotated_after = False
        # if not false, then limit to items that have been indexed before
        # this time
        self.skip_indexed_after = False
        # if not True also get uuids for items that have an assertion
        # linking them to annotated items
        self.related_annotations = False
        # if not false, use a Postgres SQL query to get a list of
        # UUIDs from a list of projects
        self.project_uuids = False
        # if not false, use a Postgres SQL query to get a list of
        # UUIDs
        self.sql = False

    def reindex(self):
        """ Reindexes items in Solr,
            with item UUIDs coming from a given source
        """
        self.iteration += 1
        print('Iteration: ' + str(self.iteration))
        if self.iteration <= self.max_iterations:
            uuids = []
            if self.solr_direct_url is not False:
                print('Get uuids from solr: ' + str(self.solr_direct_url))
                uuids = self.get_uuids_solr_direct(self.solr_direct_url)
            elif self.oc_url is not False:
                # now validate to make sure we're asking for uuids
                if 'response=uuid' in self.oc_url \
                   and '.json' in self.oc_url:
                    print('Get uuids from OC-API: ' + str(self.oc_url))
                    uuids = self.get_uuids_oc_url(self.oc_url)
            elif isinstance(self.project_uuids, list) \
                and self.annotated_after is False \
                and self.skip_indexed_after is False:
                # now validate to make sure we're asking for uuids
                uuids = []
                raw_uuids = Manifest.objects\
                                    .filter(project_uuid__in=self.project_uuids)\
                                    .values_list('uuid', flat=True)
                for raw_uuid in raw_uuids:
                    uuids.append(str(raw_uuid))
            elif isinstance(self.project_uuids, list)\
                 and self.annotated_after is False\
                 and self.skip_indexed_after is not False:
                # index items from projects, but not items indexed after a certain
                # datetime
                uuids = []
                raw_uuids = Manifest.objects\
                                    .filter(project_uuid__in=self.project_uuids)\
                                    .exclude(indexed__gte=self.skip_indexed_after)\
                                    .values_list('uuid', flat=True)
                for raw_uuid in raw_uuids:
                    uuids.append(str(raw_uuid))
            elif self.annotated_after is not False:
                self.max_iterations = 1
                uuids = []
                anno_list = []
                if self.project_uuids is not False:
                    if not isinstance(self.project_uuids, list):
                        project_uuids = [self.project_uuids]
                    else:
                        project_uuids = self.project_uuids
                    anno_list = LinkAnnotation.objects\
                                              .filter(project_uuid__in=project_uuids,
                                                      updated__gte=self.annotated_after)
                else:
                    anno_list = LinkAnnotation.objects\
                                              .filter(updated__gte=self.annotated_after)
                for anno in anno_list:
                    print('Index annotation: ' + anno.subject + ' :: ' + anno.predicate_uri + ' :: ' + anno.object_uri)
                    if(anno.subject_type in (item[0] for item in settings.ITEM_TYPES)):
                        # make sure it's an Open Context item that can get indexed
                        if anno.subject not in uuids:
                            uuids.append(anno.subject)
                    if anno.subject_type == 'types' and self.related_annotations:
                        # get the
                        # subjects item used with this type, we need to do a lookup
                        # on the assertions table
                        assertions = Assertion.objects\
                                              .filter(object_uuid=geo_anno.subject)
                        for ass in assertions:
                            if ass.uuid not in uuids:
                                uuids.append(ass.uuid)
            if isinstance(uuids, list):
                print('Ready to index ' + str(len(uuids)) + ' items')
                crawler = Crawler()
                crawler.index_document_list(uuids)
                self.reindex()
            else:
                print('Problem with: ' + str(uuids))

    def get_uuids_solr_direct(self, solr_request_url):
        """ gets uuids from solr by direct request
        """
        solr_d = SolrDirect()
        uuids = solr_d.get_result_uuids(solr_request_url)
        return uuids

    def get_uuids_oc_url(self, oc_url):
        """ gets uuids from the Open Context API
        """
        try:
            r = requests.get(oc_url,
                             timeout=60)
            r.raise_for_status()
            uuids = r.json()
        except:
            uuids = []
        return uuids
