

from django.db import models

class SchemeDetails(models.Model):
    scheme_code = models.CharField(max_length=20, unique=True)
    scheme_name = models.CharField(max_length=255)

    class Meta:
        ordering = ['scheme_name']
        verbose_name = 'Scheme Detail'
        verbose_name_plural = 'Scheme Details'

    def __str__(self):
        return self.scheme_name
class MutualFundNAV(models.Model):
    scheme = models.ForeignKey(SchemeDetails, on_delete=models.CASCADE, related_name='navs')
    nav_date = models.DateField()
    nav = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        ordering = ['nav_date']
        unique_together = ('scheme', 'nav_date')

    def __str__(self):
        return f"{self.scheme.scheme_name} - {self.nav_date}: {self.nav}"
