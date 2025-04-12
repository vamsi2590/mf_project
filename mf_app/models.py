from django.db import models

# Model for SchemeDetails table
class SchemeDetails(models.Model):
    scheme_name = models.CharField(max_length=255)
    scheme_code = models.IntegerField(unique=True)

    def __str__(self):
        return self.scheme_name

    class Meta:
        db_table = 'Scheme_Details'  # Ensures that the table name matches the SQL table name

class MutualFundNAV(models.Model):
    scheme = models.ForeignKey(SchemeDetails, on_delete=models.CASCADE, related_name='navs')  # ForeignKey to SchemeDetails
    nav_date = models.DateField()
    nav = models.FloatField()

    class Meta:
        db_table = 'MutualFund_NAV'  # Ensures that the table name matches the SQL table name
        unique_together = ['scheme', 'nav_date']  # Ensure this constraint is defined

    def __str__(self):
        return f"{self.scheme.scheme_name} - {self.nav_date}"
