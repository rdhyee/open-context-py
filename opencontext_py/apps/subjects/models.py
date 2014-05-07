from django.db import models
from opencontext_py.apps.ocitems.ocitem.models import OCitem as OCitem


# A subject is a generic item that is the subbject of observations
# A subject is the main type of record in open context for analytic data
# The main dependency for this app is for OCitems, which are used to generate
# Every type of item in Open Context, including subjects
class Subject(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True)

    class Meta:
        db_table = 'oc_manifest'

    def get_item(self):
        actItem = OCitem()
        self.ocitem = actItem.get_item(self.uuid)
        self.label = self.ocitem.label
        self.item_type = self.ocitem.item_type
        return self.ocitem
