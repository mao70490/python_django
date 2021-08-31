from django.db import models

# Create your models here.
class Product(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=60)
    price = models.IntegerField()

    def __str__(self):
        s = f'{self.id} {self.name} {self.price}'
        return s
