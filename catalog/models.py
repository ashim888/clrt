from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'service categories'

    def __str__(self):
        return self.name


class Service(models.Model):
    UNIT_CHOICES = [
        ('unit', 'Unit'),
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('month', 'Month'),
        ('project', 'Project'),
        ('page', 'Page'),
        ('word', 'Word'),
    ]
    name = models.CharField(max_length=200)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='unit')
    default_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category__order', 'name']

    def __str__(self):
        return self.name
