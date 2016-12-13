import os
import codecs
import uuid as GenUUID
import re
import datetime
import json
import html
from dateutil.parser import parse
from lxml import etree
from django.db import models
from django.conf import settings
from opencontext_py.libs.general import LastUpdatedOrderedDict
from opencontext_py.apps.ocitems.manifest.models import Manifest
from opencontext_py.apps.ocitems.predicates.manage import PredicateManagement
from opencontext_py.apps.ocitems.octypes.manage import TypeManagement
from opencontext_py.apps.imports.fields.datatypeclass import DescriptionDataType
from opencontext_py.apps.imports.faims.files import FileManage


class AttributesImport():
    """ Loads attributes.xml files for import

from opencontext_py.apps.imports.faims.attributes import AttributesImport
faims_attribs = AttributesImport()
faims_attribs.gen_config('faims-survey')


    """

    def __init__(self):
        self.tree = None
        self.project_uuid = False
        self.source_id = False
        self.attributes = None
        self.oc_config_attributes = 'oc-attributes'
        self.reconcile_key = 'faims_id'
        self.fm = FileManage()

    def gen_config(self, act_dir, filename='attributes.xml'):
        """ processes the attributes XML file """
        self.tree = self.fm.load_xml_file(act_dir, filename)
        if self.tree is not False:
            ok = self.load_or_classify_attributes(act_dir)

    def load_or_classify_attributes(self, act_dir):
        """ loads or classifies attributes in a tree """
        ok = False
        key = self.oc_config_attributes
        self.attributes = self.fm.get_dict_from_file(key, act_dir)
        if self.attributes is None:
            print('Need to 1st generate an attributes file from the ArchEnts!')
            ok = False
        else:
            # we have JSON with dictionary for the attributes
            ok = True
            self.classify_xml_tree_attributes()
            self.fm.save_serialized_json(key,
                                         act_dir,
                                         self.attributes)
        return ok    

    def classify_xml_tree_attributes(self):
        """ classifies attributes in a tree """
        if self.tree is not False and self.attributes is not None:
            attribs = self.tree.xpath('/attributes/attribute')
            for attrib in attribs:
                prop_name = attrib.xpath('AttributeName')[0].text
                prop_id = attrib.xpath('AttributeID')[0].text
                if prop_id in self.attributes:
                    if 'predicate_uuid' not in self.attributes[prop_id]:
                        # only do the next part if the predicate_uuid is not assigned yet
                        self.attributes[prop_id]['predicate_uuid'] = None
                        cont_vocabs = attrib.xpath('controlledVocabs/vocabulary')
                        if len(cont_vocabs) > 0: 
                            self.attributes[prop_id]['data_type'] = 'id'
                            self.attributes[prop_id]['vocabs_count'] = len(cont_vocabs)
                            oc_types = self.classify_xml_attributes_to_types(cont_vocabs)
                            self.attributes[prop_id]['oc_types'] = oc_types
    
    def classify_xml_attributes_to_types(self, cont_vocabs, predicate_uuid=None):
        """ classifies open context types used with each attribute """
        oc_types = LastUpdatedOrderedDict()
        for vocab in cont_vocabs:
            vocab_id = vocab.xpath('VocabID')[0].text
            oc_type = LastUpdatedOrderedDict()
            oc_type['id'] = vocab_id
            if len(vocab.xpath('Arch16n')) > 0:
                oc_type['label'] = vocab.xpath('Arch16n')[0].text
            else:
                oc_type['label'] = vocab.xpath('VocabName')[0].text
            oc_type['uuid'] = None
            oc_type['predicate_uuid'] = predicate_uuid
            oc_type['faims_attrib_id'] = vocab.xpath('AttributeID')[0].text
            oc_type['faims_internal_str'] = vocab.xpath('VocabName')[0].text
            sort_str = vocab.xpath('VocabCountOrder')[0].text
            try:
                oc_type['sort'] = float(sort_str)
            except:
                oc_type['sort'] = 0
            oc_type['note'] = None
            notes = vocab.xpath('VocabDescription')
            for act_note_node in notes:
                act_note = act_note_node.text
                if '&lt;' in act_note and '&gt;' in act_note:
                    # has escaped HTML, unescape it
                    oc_type['note'] = act_note.unescape(act_note)
                else:
                    oc_type['note'] = act_note
            oc_types[vocab_id] = oc_type
        return oc_types
    
    def db_save_reconcile_predicates_types(self, act_dir):
        """ saves predicates and type items to the
            Open Context database, and / or reconciles these
            items with previously saved items from the same project
        """
        key = self.oc_config_attributes
        json_obj = self.fm.get_dict_from_file(key, act_dir)
        if json_obj is None:
            print('Need to 1st generate an attributes file from the ArchEnts!')
            ok = False
        else:
            # we have JSON with dictionary for the attributes
            ok = True
            self.attributes = json_obj
            for faims_id_pred, attrib_dict in json_obj.items():
                sup_dict = LastUpdatedOrderedDict()
                sup_dict[self.reconcile_key] = faims_id_pred
                pm = PredicateManagement()
                pm.project_uuid = self.project_uuid
                pm.source_id = self.source_id
                pm.sup_dict = sup_dict
                pm.sup_reconcile_key = self.reconcile_key
                pm.sup_reconcile_value = faims_id_pred
                pred_obj = pm.get_make_predicate(attrib_dict['label'],
                                                 attrib_dict['predicate_type'],
                                                 attrib_dict['data_type'])
                if pred_obj is not False:
                    # we reconciled the predicate!
                    self.attributes[faims_id_pred]['predicate_uuid'] = str(pred_obj.uuid)
                    if 'oc_types' in attrib_dict:
                        for faims_id_type, type_dict in attrib_dict['oc_types'].items():
                            sup_dict = LastUpdatedOrderedDict()
                            sup_dict[self.reconcile_key] = faims_id_type
                            tm = TypeManagement()
                            tm.project_uuid = self.project_uuid
                            tm.source_id = self.source_id
                            tm.sup_dict = sup_dict
                            tm.sup_reconcile_key = self.reconcile_key
                            tm.sup_reconcile_value = faims_id_type
                            type_obj = tm.get_make_type_within_pred_uuid(pred_obj.uuid,
                                                                         type_dict['label'])
                            if type_obj is not False:
                                # we have reconciled the type!
                                type_dict['uuid'] = str(type_obj.uuid)
                                type_dict['predicate_uuid'] = str(pred_obj.uuid)
                                self.attributes[faims_id_pred]['oc_types'][faims_id_type] = type_dict
            # now save the results
            self.fm.save_serialized_json(key,
                                         act_dir,
                                         self.attributes)
