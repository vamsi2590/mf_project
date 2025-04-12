from django.db import models
from django.core.validators import MinValueValidator
import pandas as pd
from datetime import timedelta

class SchemeDetails(models.Model):
    scheme_code = models.CharField(max_length=20, unique=True)
    scheme_name = models.CharField(max_length=255)

    class Meta:
        ordering = ['scheme_name']
        verbose_name = 'Scheme Detail'
        verbose_name_plural = 'Scheme Details'

    def __str__(self):
        return self.scheme_name

    @classmethod
    def get_all_schemes_df(cls):
        """Get all schemes as a pandas DataFrame"""
        queryset = cls.objects.all().order_by('scheme_name')
        return pd.DataFrame(list(queryset.values('scheme_code', 'scheme_name')))

class MutualFundNAV(models.Model):
    scheme = models.ForeignKey(SchemeDetails, on_delete=models.CASCADE, related_name='navs')
    nav_date = models.DateField()
    nav = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        ordering = ['nav_date']
        unique_together = ('scheme', 'nav_date')
        indexes = [
            models.Index(fields=['scheme', 'nav_date']),
        ]

    def __str__(self):
        return f"{self.scheme.scheme_name} - {self.nav_date}: {self.nav}"

    @classmethod
    def get_nav_data_df(cls, scheme_code):
        """Get NAV data for a specific scheme as DataFrame"""
        navs = cls.objects.filter(
            scheme__scheme_code=scheme_code
        ).order_by('nav_date')

        if not navs.exists():
            return pd.DataFrame(columns=["nav_date", "nav"])

        df = pd.DataFrame(list(navs.values('nav_date', 'nav')))
        df['nav_date'] = pd.to_datetime(df['nav_date'])
        return df

    @classmethod
    def calculate_performance(cls, df, start_date, end_date):
        """Calculate performance metrics between dates"""
        if df.empty or start_date is None or end_date is None:
            return None, None, None

        period_df = df[(df['nav_date'] >= start_date) & (df['nav_date'] <= end_date)]
        if period_df.empty:
            return None, None, None

        start_nav = period_df['nav'].iloc[0]
        end_nav = period_df['nav'].iloc[-1]
        change = end_nav - start_nav
        percent_change = (change / start_nav) * 100
        color = "positive" if percent_change >= 0 else "negative"
        return f"{percent_change:.2f}%", f"{change:.2f}", color
