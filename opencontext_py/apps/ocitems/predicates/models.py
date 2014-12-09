from datetime import datetime
from django.db import models


# Predicate stores a predicate (decriptive property or linking relation)
# that is contributed by open context data contributors
class Predicate(models.Model):
    uuid = models.CharField(max_length=50, primary_key=True)
    project_uuid = models.CharField(max_length=50, db_index=True)
    source_id = models.CharField(max_length=50, db_index=True)
    data_type = models.CharField(max_length=50)
    sort = models.DecimalField(max_digits=8, decimal_places=3)
    created = models.DateTimeField()
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        saves a manifest item with a good slug
        """
        if self.sort is None:
            self.sort = 0
        if self.created is None:
            self.created = datetime.now()
        super(Predicate, self).save(*args, **kwargs)

    class Meta:
        db_table = 'oc_predicates'
        ordering = ['sort']
