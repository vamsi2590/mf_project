from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .forms import CustomUserCreationForm
from django.http import JsonResponse

import pandas as pd
from datetime import timedelta
from django.shortcuts import render
from django.db import connection
import plotly.express as px
from plotly.offline import plot

# DB connection (PostgreSQL)
def get_connection():
    # We are using Django's database connection here, which will be configured in settings.py
    return connection.cursor()

def get_all_scheme_codes():
    # Using Django's database connection to fetch scheme details
    with connection.cursor() as cursor:
        cursor.execute("SELECT scheme_code, scheme_name FROM Scheme_Details ORDER BY scheme_name")
        rows = cursor.fetchall()  # Fetch all rows returned by the query
        # Converting the result into a DataFrame for further manipulation
        df = pd.DataFrame(rows, columns=["scheme_code", "scheme_name"])
    return df

def get_nav_data(scheme_code):
    # Fetching NAV data for a particular scheme
    with connection.cursor() as cursor:
        query = f"""
        SELECT nav.nav_date, nav.nav
        FROM Scheme_Details sd
        JOIN MutualFund_NAV nav ON sd.scheme_details_id = nav.scheme_code_id
        WHERE sd.scheme_code = {scheme_code}
        ORDER BY nav.nav_date ASC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        # Converting the result into a DataFrame
        df = pd.DataFrame(rows, columns=["nav_date", "nav"])
        df['nav_date'] = pd.to_datetime(df['nav_date'])  # Converting nav_date to datetime
    return df

def calculate_performance(df, start_date, end_date):
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

def purchase_tracker(request):
    # Fetch all scheme codes and names
    scheme_df = get_all_scheme_codes()
    schemes = scheme_df.to_dict(orient='records')  # Convert DataFrame to a dictionary
    selected_scheme = request.GET.get("scheme")

    context = {
        "schemes": schemes,
        "selected_scheme": selected_scheme,
    }

    # If a scheme is selected, fetch its NAV data
    if selected_scheme:
        scheme_code = scheme_df[scheme_df['scheme_name'] == selected_scheme]['scheme_code'].values[0]
        nav_df = get_nav_data(scheme_code)

        if not nav_df.empty:
            min_date = nav_df['nav_date'].min()
            max_date = nav_df['nav_date'].max()

            user_date = request.GET.get("purchase_date")
            if user_date:
                purchase_date = pd.to_datetime(user_date)
                user_nav_df = nav_df[(nav_df['nav_date'] >= purchase_date) & (nav_df['nav_date'] <= max_date)]

                if not user_nav_df.empty:
                    current_nav = user_nav_df['nav'].iloc[-1]
                    total_percent, total_change, total_color = calculate_performance(nav_df, purchase_date, max_date)

                    # Timeframe performance
                    timeframes = [
                        ("1M", "1 Month", timedelta(days=30)),
                        ("3M", "3 Months", timedelta(days=90)),
                        ("6M", "6 Months", timedelta(days=182)),
                        ("1Y", "1 Year", timedelta(days=365)),
                        ("2Y", "2 Years", timedelta(days=730)),
                        ("5Y", "5 Years", timedelta(days=1825))
                    ]

                    tf_data = []
                    for code, label, delta in timeframes:
                        end_date = min(purchase_date + delta, max_date)
                        percent, change, color = calculate_performance(nav_df, purchase_date, end_date)
                        tf_data.append({
                            "label": label,
                            "percent": percent or "-",
                            "change": change or "-",
                            "color": color or "neutral"
                        })

                    # Plotly chart
                    fig = px.line(user_nav_df, x='nav_date', y='nav')
                    fig.add_vline(
                        x=purchase_date.timestamp() * 1000,
                        line_dash="dash", line_color="red", annotation_text="Purchase Date"
                    )
                    fig.update_layout(
                        title=f"{selected_scheme} Performance Since Purchase",
                        height=300, margin=dict(l=20, r=20, t=40, b=20),
                        plot_bgcolor='white', showlegend=False
                    )
                    fig.update_traces(line=dict(color="#0a9e47", width=2))
                    fig.update_xaxes(showgrid=False, tickformat="%b %Y")
                    fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
                    chart_html = plot(fig, output_type='div')

                    context.update({
                        "min_date": min_date.date(),
                        "max_date": max_date.date(),
                        "purchase_date": purchase_date.date(),
                        "current_nav": f"{current_nav:.2f}",
                        "nav_date": max_date.strftime("%d %b, %Y"),
                        "purchase_date_str": purchase_date.strftime("%d %b, %Y"),
                        "total_percent": total_percent,
                        "total_change": total_change,
                        "total_color": total_color,
                        "timeframes": tf_data,
                        "chart": chart_html,
                    })
                else:
                    context["error"] = "No data available after your selected purchase date."
            else:
                context["min_date"] = min_date.date()
                context["max_date"] = max_date.date()
        else:
            context["error"] = "No NAV data found for this scheme."
    return render(request, "mf_app/purchase_tracker.html", context)



def signup_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        else:
            errors = dict(form.errors.items())
            return JsonResponse({'success': False, 'errors': errors}, status=400)

    return JsonResponse({'success': False, 'errors': {'form': 'Invalid request.'}}, status=400)

def login_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        else:
            return JsonResponse({
                'success': False,
                'errors': {'__all__': 'Invalid username or password'}
            }, status=400)

    return JsonResponse({'success': False, 'errors': {'form': 'Invalid request.'}}, status=400)

def index(request):
    return render(request, 'mf_app/index.html')

@login_required
def dashboard(request):
    return render(request, 'mf_app/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('index')

# ... keep your other views the same ...

# ... keep your other views the same ...
def about(request):
    return render(request, 'mf_app/about.html')

def blog(request):
    return render(request, 'mf_app/blog.html')

def contact(request):
    return render(request, 'mf_app/contact.html')

def faq(request):
    return render(request, 'mf_app/FAQ.html')

def feature(request):
    return render(request, 'mf_app/feature.html')

def offer(request):
    return render(request, 'mf_app/offer.html')

def service(request):
    return render(request, 'mf_app/service.html')

def team(request):
    return render(request, 'mf_app/team.html')

def testimonial(request):
    return render(request, 'mf_app/testimonial.html')

def error_404(request, exception):
    return render(request, '404.html', status=404)

def home(request):
    return render(request, 'mf_App/index.html')
