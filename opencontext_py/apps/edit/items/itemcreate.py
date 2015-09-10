import time
import uuid as GenUUID
from lxml import etree
import lxml.html
from django.db import models
from django.db.models import Q
from django.core.cache import cache
from opencontext_py.apps.entities.entity.models import Entity
from opencontext_py.apps.ocitems.manifest.models import Manifest
from opencontext_py.apps.ocitems.projects.permissions import ProjectPermissions
from opencontext_py.apps.ocitems.projects.models import Project
from opencontext_py.apps.ocitems.documents.models import OCdocument
from opencontext_py.apps.ocitems.persons.models import Person
from opencontext_py.apps.ocitems.subjects.models import Subject
from opencontext_py.apps.ocitems.predicates.models import Predicate
from opencontext_py.apps.ocitems.octypes.models import OCtype
from opencontext_py.apps.ocitems.strings.models import OCstring
from opencontext_py.apps.ocitems.strings.manage import StringManagement
from opencontext_py.apps.ocitems.octypes.manage import TypeManagement
from opencontext_py.apps.edit.items.itemassertion import ItemAssertion


class ItemCreate():
    """ This class contains methods
        for mannually creating items into a project
    """

    def __init__(self,
                 project_uuid,
                 request=False):
        self.project_uuid = project_uuid
        self.oc_root_project = False
        self.request = request
        self.errors = {'params': False}
        self.response = {}
        try:
            self.project = Project.objects.get(uuid=project_uuid)
        except Project.DoesNotExist:
            self.project = False
        try:
            self.proj_manifest_obj = Manifest.objects.get(uuid=project_uuid)
        except Manifest.DoesNotExist:
            self.proj_manifest_obj = False
        if request is not False and self.project is not False:
            # check to make sure edit permissions OK
            pp = ProjectPermissions(project_uuid)
            self.edit_permitted = pp.edit_allowed(request)
        else:
            # default to no editting permissions
            self.edit_permitted = False
        if project_uuid == '0' \
           or project_uuid == ''  \
           or project_uuid == 'oc':
            self.oc_root_project = True
        else:
            self.oc_root_project = False

    def check_uuid_exists(self, uuid, check_strings=True):
        """ checks to see if a uuid is already in use """
        exists = True
        obj_check = Manifest.objects\
                            .filter(uuid=uuid)[:1]
        uses = len(obj_check)
        obj_check = Subject.objects\
                           .filter(uuid=uuid)[:1]
        uses += len(obj_check)
        obj_check = Project.objects\
                           .filter(uuid=uuid)[:1]
        uses += len(obj_check)
        obj_check = OCdocument.objects\
                              .filter(uuid=uuid)[:1]
        uses += len(obj_check)
        obj_check = Predicate.objects\
                             .filter(uuid=uuid)[:1]
        uses += len(obj_check)
        obj_check = OCtype.objects\
                          .filter(uuid=uuid)[:1]
        uses += len(obj_check)
        if check_strings:
            # we can skip this check
            obj_check = OCstring.objects\
                                .filter(uuid=uuid)[:1]
            uses += len(obj_check)
        if uses == 0:
            exists = False
        return exists

    def create_or_validate_uuid(self, post_data):
        """ mints a new uuuid or validates an existing
            one is OK to use
        """
        uuid = GenUUID.uuid4()
        uuid = str(uuid)
        if 'uuid' in post_data:
            if self.check_uuid_format(post_data['uuid']):
                uuid = post_data['uuid'].strip()
                uuid_exists = self.check_uuid_exists(uuid)
                if uuid_exists:
                    self.errors['uuid'] = 'Cannot create an item with UUID: ' + uuid
                    self.errors['uuid'] += ', because it is already used.'
                    uuid = False
        return uuid

    def check_uuid_format(self, uuid_string):
        """ checks to see if a string has
            a valid uuid format
        """
        uuid_format_ok = False
        if len(uuid_string) > 30 \
           and uuid_string.count('-') == 4:
            uuid_format_ok = True
        return uuid_format_ok

    def create_project(self, post_data):
        """ creates a project item into a project
        """
        ok = True
        required_params = ['source_id',
                           'label',
                           'short_des']
        for r_param in required_params:
            if r_param not in post_data:
                # we're missing some required data
                # don't create the item
                ok = False
                message = 'Missing paramater: ' + r_param + ''
                if self.errors['params'] is False:
                    self.errors['params'] = message
                else:
                    self.errors['params'] += '; ' + message
        uuid = self.create_or_validate_uuid(post_data)
        if uuid is False:
            ok = False
            note = self.errors['uuid']
        if ok:
            label = post_data['label']
            if self.oc_root_project:
                project_uuid = uuid
            else:
                project_uuid = self.project_uuid
            new_proj = Project()
            new_proj.uuid = uuid
            new_proj.project_uuid = project_uuid
            new_proj.source_id = post_data['source_id']
            new_proj.edit_status = 0
            new_proj.label = label
            new_proj.short_des = post_data['short_des']
            new_proj.save()
            new_man = Manifest()
            new_man.uuid = uuid
            new_man.project_uuid = project_uuid
            new_man.source_id = post_data['source_id']
            new_man.item_type = 'projects'
            new_man.repo = ''
            new_man.class_uri = ''
            new_man.label = label
            new_man.des_predicate_uuid = ''
            new_man.views = 0
            new_man.save()
        else:
            label = '[Item not created]'
            uuid = False
        if ok:
            # now clear the cache a change was made
            cache.clear()
        self.response = {'action': 'create-item-into',
                         'ok': ok,
                         'change': {'uuid': uuid,
                                    'label': label,
                                    'note': self.add_creation_note(ok)}}
        return self.response

    def create_person(self, post_data):
        """ creates a person item into a project
        """
        ok = True
        required_params = ['source_id',
                           'item_type',
                           'foaf_type',
                           'combined_name',
                           'given_name',
                           'surname',
                           'mid_init',
                           'initials']
        for r_param in required_params:
            if r_param not in post_data:
                # we're missing some required data
                # don't create the item
                ok = False
                message = 'Missing paramater: ' + r_param + ''
                if self.errors['params'] is False:
                    self.errors['params'] = message
                else:
                    self.errors['params'] += '; ' + message
        uuid = self.create_or_validate_uuid(post_data)
        if uuid is False:
            ok = False
            note = self.errors['uuid']
        if ok:
            label = post_data['combined_name']
            new_pers = Person()
            new_pers.uuid = uuid
            new_pers.project_uuid = self.project_uuid
            new_pers.source_id = post_data['source_id']
            new_pers.foaf_type = post_data['foaf_type']
            new_pers.combined_name = post_data['combined_name']
            new_pers.given_name = post_data['given_name']
            new_pers.surname = post_data['surname']
            new_pers.mid_init = post_data['mid_init']
            new_pers.initials = post_data['initials']
            new_pers.save()
            new_man = Manifest()
            new_man.uuid = uuid
            new_man.project_uuid = self.project_uuid
            new_man.source_id = post_data['source_id']
            new_man.item_type = 'persons'
            new_man.repo = ''
            new_man.class_uri = post_data['foaf_type']
            new_man.label = post_data['combined_name']
            new_man.des_predicate_uuid = ''
            new_man.views = 0
            new_man.save()
        else:
            label = '[Item not created]'
            uuid = False
        if ok:
            # now clear the cache a change was made
            cache.clear()
        self.response = {'action': 'create-item-into',
                         'ok': ok,
                         'change': {'uuid': uuid,
                                    'label': label,
                                    'note': self.add_creation_note(ok)}}
        return self.response

    def validate_content_uuid(self, tm, post_data):
        """ Checks to see if the content_uuid
            is OK,
            returns False if not valid
        """
        ok = True
        label = post_data['label'].strip()
        predicate_uuid = post_data['predicate_uuid'].strip()
        content_uuid = post_data['content_uuid'].strip()
        if self.check_uuid_format(content_uuid):
            str_manage = StringManagement()
            str_manage.project_uuid = self.project_uuid
            # get an existing or create a new string object
            string_uuid = str_manage.check_string_exists(label,
                                                         True)
            # now check to make sure the content_uuid is not
            # already used, skipping strings
            uuid_exists = self.check_uuid_exists(content_uuid,
                                                 False)
            if uuid_exists:
                # the uuid is used for something that is not a string
                # this messes stuff up, so note the error
                ok = False
                self.errors['content_uuid'] = 'Cannot use the UUID: ' + content_uuid
                self.errors['content_uuid'] += ', because it is already used.'
            elif string_uuid is not False and string_uuid != content_uuid:
                # conflict beteween the user submitted content_uuid
                # and the string_uuid for the same label
                ok = False
                self.errors['content_uuid'] = 'Cannot create a category called "' + label + '" '
                self.errors['content_uuid'] += ', becuase the submitted content UUID: ' + content_uuid
                self.errors['content_uuid'] += ' conflicts with the existing UUID: ' + string_uuid
            else:
                # now, one last check is to make sure the
                # current combinaiton of predicate_uuid and content_uuid does not exist
                type_exists = tm.check_exists_pred_uuid_content(predicate_uuid,
                                                                content_uuid)
                if type_exists:
                    ok = False
                    self.errors['content_uuid'] = 'Cannot create a category called "' + label + '" '
                    self.errors['content_uuid'] += ', becuase the submitted content UUID: ' + content_uuid
                    self.errors['content_uuid'] += ' is already used with the Predicate UUID: ' + predicate_uuid
        else:
            ok = False
            self.errors['content_uuid'] = 'Cannot create a category called "' + label + '"'
            self.errors['content_uuid'] += ', becuase the submitted content UUID: ' + content_uuid
            self.errors['content_uuid'] += ' is badly formed.'
        if ok:
            return content_uuid
        else:
            return False

    def check_non_blank_param(self, post_data, param):
        """ checks to see if a paramater exists,
            and is not blank or false
        """
        output = False
        if param in post_data:
            val = post_data[param]
            if len(val) > 0:
                if val != 'false':
                    output = True
        return output

    def create_type(self, post_data):
        """ creates a type item into a project
        """
        ok = True
        required_params = ['source_id',
                           'item_type',
                           'predicate_uuid',
                           'label',
                           'note']
        for r_param in required_params:
            if r_param not in post_data:
                # we're missing some required data
                # don't create the item
                ok = False
                message = 'Missing paramater: ' + r_param + ''
                if self.errors['params'] is False:
                    self.errors['params'] = message
                else:
                    self.errors['params'] += '; ' + message
        # now prep the type management !
        tm = TypeManagement()
        tm.project_uuid = self.project_uuid
        uuid = False
        content_uuid = False
        if ok:
            # now check to see if this already exists
            label = post_data['label'].strip()
            type_note = post_data['note'].strip()
            tm.source_id = post_data['source_id'].strip()
            predicate_uuid = post_data['predicate_uuid'].strip()
            if self.check_non_blank_param(post_data, 'uuid')\
               and self.check_non_blank_param(post_data, 'content_uuid'):
                uuid = post_data['uuid'].strip()
                if self.check_uuid_format(uuid):
                    uuid_exists = self.check_uuid_exists(uuid)
                    if uuid_exists:
                        ok = False
                        self.errors['uuid'] = 'Cannot create a category called "' + label + '"'
                        self.errors['uuid'] += ', becuase the submitted UUID: ' + uuid
                        self.errors['uuid'] += ' already exists.'
                        note = self.errors['uuid']
                    else:
                        # ok! use this as the suggested UUID for making a new type
                        tm.suggested_uuid = uuid
                        content_uuid = self.validate_content_uuid(tm,
                                                                  post_data)
                        if content_uuid is False:
                            ok = False
                            note = self.errors['content_uuid']
                        else:
                            # ok! the content uuid is also OK to use
                            tm.suggested_content_uuid = content_uuid
                else:
                    ok = False
                    self.errors['uuid'] = 'Cannot create a category called "' + label + '"'
                    self.errors['uuid'] += ', becuase the submitted UUID: ' + uuid
                    self.errors['uuid'] += ' is badly formed.'
                    note = self.errors['uuid']
            elif self.check_non_blank_param(post_data, 'uuid') \
                and not self.check_non_blank_param(post_data,
                                                   'content_uuid'):
                # we have a uuid for the type, but not the content. We can't
                # create the type however, since we're missing a content uuid
                uuid = post_data['uuid'].strip()
                ok = False
                self.errors['uuid'] = 'Cannot create a category called "' + label + '"'
                self.errors['uuid'] += ', becuase the submitted UUID: ' + str(uuid)
                self.errors['uuid'] += ' needs to have a valid Content UUID.'
                note = self.errors['uuid']
            elif not self.check_non_blank_param(post_data, 'uuid') \
                and self.check_non_blank_param(post_data,
                                               'content_uuid'):
                # we have a uuid for the content only. a weird case, but possible
                content_uuid = self.validate_content_uuid(tm,
                                                          post_data)
                if content_uuid is False:
                    ok = False
                    note = self.errors['content_uuid']
                else:
                    # ok! the content uuid is also OK to use
                    tm.suggested_content_uuid = content_uuid
        else:
            label = '[Item not created]'
            uuid = False
        if ok:
            type_uuid = tm.check_exists_pred_uuid_content(predicate_uuid,
                                                          label,
                                                          True)
            if type_uuid is not False:
                # we already have this type!
                ok = False
                uuid = type_uuid
                self.errors['uuid'] = 'Cannot create a category called "' + label + '"'
                self.errors['uuid'] += ', becuase it already exists with UUID: ' + uuid
                note = self.errors['uuid']
        if ok:
            tm.source_id = post_data['source_id'].strip()
            if content_uuid is False:
                newtype = tm.get_make_type_within_pred_uuid(predicate_uuid,
                                                            label)
                content_uuid = newtype.content_uuid
                uuid = newtype.uuid
            else:
                tm.content = label
                newtype = tm.get_make_type_pred_uuid_content_uuid(predicate_uuid,
                                                                  content_uuid)
                content_uuid = newtype.content_uuid
                uuid = newtype.uuid
            # now add the note if not empty
            self.add_description_note(newtype.uuid,
                                      'types',
                                      newtype.source_id,
                                      type_note)
        if ok:
            # now clear the cache a change was made
            cache.clear()
        self.response = {'action': 'create-item-into',
                         'ok': ok,
                         'change': {'uuid': uuid,
                                    'content_uuid': content_uuid,
                                    'label': label,
                                    'note': self.add_creation_note(ok)}}
        return self.response

    def create_predicate(self, post_data):
        """ creates a type item into a project
        """
        ok = True
        required_params = ['source_id',
                           'item_type',
                           'label',
                           'note',
                           'class_uri',
                           'data_type']
        for r_param in required_params:
            if r_param not in post_data:
                # we're missing some required data
                # don't create the item
                ok = False
                message = 'Missing paramater: ' + r_param + ''
                if self.errors['params'] is False:
                    self.errors['params'] = message
                else:
                    self.errors['params'] += '; ' + message
        uuid = self.create_or_validate_uuid(post_data)
        if uuid is False:
            ok = False
            note = self.errors['uuid']
        if ok:
            # now check to see if this already exists
            note = ''
            item_type = 'predicates'
            source_id = post_data['source_id'].strip()
            label = post_data['label'].strip()
            if len(label) < 1:
                ok = False
                self.errors['label'] = 'The label cannot be blank.'
                note += self.errors['label'] + ' '
            else:
                exist_uuid = self.get_uuid_manifest_label(label,
                                                          item_type)
                if exist_uuid is not False:
                    ok = False
                    self.errors['uuid'] = 'Cannot create a category called "' + label + '"'
                    self.errors['uuid'] += ', becuase it already exists with UUID: ' + uuid
                    note += self.errors['uuid'] + ' '
            pred_note = post_data['note'].strip()
            class_uri = post_data['class_uri'].strip()
            if class_uri not in Predicate.CLASS_TYPES:
                ok = False
                self.errors['class_uri'] = class_uri + ' is not a valid Predicate class.'
                note += self.errors['class_uri'] + ' '
            data_type = post_data['data_type'].strip()
            if data_type not in Predicate.DATA_TYPES_HUMAN:
                ok = False
                self.errors['data_type'] = data_type + ' is not a valid Predicate data-type.'
                note += self.errors['data_type'] + ' '
        if ok:
            note = 'Predicate "' + label + '" created with UUID:' + uuid
            # everything checked out OK, so make the predicate
            new_pred = Predicate()
            new_pred.uuid = uuid
            new_pred.project_uuid = self.project_uuid
            new_pred.source_id = source_id
            new_pred.data_type = data_type
            new_pred.sort = 1
            new_pred.save()
            # now save to the manifest
            new_man = Manifest()
            new_man.uuid = uuid
            new_man.project_uuid = self.project_uuid
            new_man.source_id = source_id
            new_man.item_type = 'predicates'
            new_man.repo = ''
            new_man.class_uri = class_uri
            new_man.label = label
            new_man.des_predicate_uuid = ''
            new_man.views = 0
            new_man.save()
            # now add the note if not empty
            self.add_description_note(uuid,
                                      'predicates',
                                      source_id,
                                      pred_note)
        if ok:
            # now clear the cache a change was made
            cache.clear()
        self.response = {'action': 'create-item-into',
                         'ok': ok,
                         'change': {'uuid': uuid,
                                    'label': label,
                                    'note': self.add_creation_note(ok)}}
        return self.response

    def add_description_note(self,
                             uuid,
                             item_type,
                             source_id,
                             note):
        """ adds a descriptive note to a created item """
        item_assert = ItemAssertion()
        item_assert.project_uuid = self.project_uuid
        item_assert.source_id = source_id
        item_assert.uuid = uuid
        item_assert.item_type = item_type
        item_assert.add_description_note(note)

    def get_uuid_manifest_label(self, label, item_type):
        """ Gets the UUID for a label of a certain item_type
            from the manifest.
            Returns false if the label is not matched
        """
        uuid = False
        man_labs = Manifest.objects\
                           .filter(label=label,
                                   item_type=item_type,
                                   project_uuid=self.project_uuid)[:1]
        if len(man_labs) > 0:
            uuid = man_labs[0].uuid
        return uuid

    def add_creation_note(self, ok):
        """ adds a note about the creation of a new item """
        if self.proj_manifest_obj is not False:
            proj_label = self.proj_manifest_obj.label
        else:
            proj_label = 'Open Context [General]'
        if ok:
            note = 'Item added into: ' + proj_label
        else:
            note = 'Failed to create item into: ' + proj_label
        return note
