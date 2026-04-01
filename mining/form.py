"""
Forms for the Silver Mining Database.

Every form handles validation of incoming data.
Views call form.is_valid() then read form.cleaned_data.
"""

from django import forms
from .models import Company, Finmetrics, Stockprice, Productiondata, Usertab


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
#validates email and password on login
class LoginForm(forms.Form):
    email = forms.EmailField(max_length=100)
    password = forms.CharField()

#validates new investor registration checks passwords match and email is unique
class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length = 50)
    last_name = forms.CharField(max_length = 50)
    email = forms.EmailField(max_length = 100)
    password = forms.CharField(min_length = 8)
    confirm_password = forms.CharField()

    def clean_email(self):
        email = self.cleaned_data['email']
        if Usertab.objects.filter(user_email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# COMPANY
# ─────────────────────────────────────────────────────────────────────────────
#validates adding a new company (checks ticker does not already exist)
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['ticker', 'company_name']

    def clean_ticker(self):
        ticker = self.cleaned_data['ticker'].upper().strip()
        if Company.objects.filter(ticker=ticker).exists():
            raise forms.ValidationError(f"A company with ticker '{ticker}' already exists.")
        return ticker

#validates updating a company name
class CompanyUpdateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['company_name']


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL METRICS
# ─────────────────────────────────────────────────────────────────────────────
#Validates inserting new financial metrics
class FinmetricsForm(forms.ModelForm):
    class Meta:
        model = Finmetrics
        fields = ['ticker', 'aisc', 'peg', 'total_debt', 'debt_to_equity', 'revenue', 'ebitda']

    def clean(self):
        cleaned = super().clean()
        ticker = cleaned.get('ticker')
        if ticker and Finmetrics.objects.filter(ticker = ticker).exists():
            raise forms.ValidationError(f"Financial metrics for {ticker} already exist. Use the edit form instead.")
        return cleaned

#validates updating existing metrics (checks values are positive)
class FinmetricsUpdateForm(forms.ModelForm):
    class Meta:
        model = Finmetrics
        fields = ['aisc', 'peg', 'total_debt', 'debt_to_equity', 'revenue', 'ebitda']

    def clean_aisc(self):
        val = self.cleaned_data['aisc']
        if val <= 0:
            raise forms.ValidationError("AISC must be a positive value.")
        return val

    def clean_peg(self):
        val = self.cleaned_data['peg']
        if val <= 0:
            raise forms.ValidationError("PEG ratio must be positive.")
        return val

    def clean_debt_to_equity(self):
        val = self.cleaned_data['debt_to_equity']
        if val < 0:
            raise forms.ValidationError("Debt-to-equity cannot be negative.")
        return val


# ─────────────────────────────────────────────────────────────────────────────
# STOCK PRICE
# ─────────────────────────────────────────────────────────────────────────────
#Validates stock price records (checks high is not below low)
class StockpriceForm(forms.ModelForm):
    class Meta:
        model = Stockprice
        fields = ['ticker', 'date_updated','previous_open', 'previous_close','fifty_two_week_high', 'fifty_two_week_low',]

    def clean(self):
        cleaned = super().clean()
        ticker = cleaned.get('ticker')
        date = cleaned.get('date_updated')
        if ticker and date:
            exists = Stockprice.objects.filter(ticker = ticker, date_updated = date)
            if self.instance and self.instance.pk:
                exists = exists.exclude(pk = self.instance.pk)
            if exists.exists():
                raise forms.ValidationError("A stock price record for this ticker and date already exists.")
        high = cleaned.get('fifty_two_week_high')
        low = cleaned.get('fifty_two_week_low')
        if high and low and high < low:
            raise forms.ValidationError("52-week high cannot be less than 52-week low.")
        return cleaned
    
#validates updating existing stock price (checks values are positive)
class StockpriceUpdateForm(forms.ModelForm):
    class Meta:
        model = Stockprice
        fields = ['previous_open', 'previous_close','fifty_two_week_high', 'fifty_two_week_low']

    def clean_previous_open(self):
        val = self.cleaned_data['previous_open']
        if val <= 0:
            raise forms.ValidationError("Previous open must be a positive value.")
        return val

    def clean_previous_close(self):
        val = self.cleaned_data['previous_close']
        if val <= 0:
            raise forms.ValidationError("Previous close must be a positive value.")
        return val

    def clean_fifty_two_week_high(self):
        val = self.cleaned_data['fifty_two_week_high']
        if val <= 0:
            raise forms.ValidationError("52 week high must be a positive value.")
        return val

    def clean_fifty_two_week_low(self):
        val = self.cleaned_data['fifty_two_week_low']
        if val <= 0:
            raise forms.ValidationError("52 week low must be a positive value.")
        return val


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTION DATA
# ─────────────────────────────────────────────────────────────────────────────
#validates inserting new production records
class ProductiondataForm(forms.ModelForm):
    class Meta:
        model = Productiondata
        fields = ['ticker', 'period', 'silver_ounces_produced', 'notes']

    def clean(self):
        cleaned = super().clean()
        ticker = cleaned.get('ticker')
        period = cleaned.get('period')
        if ticker and period and Productiondata.objects.filter(ticker = ticker, period = period).exists():
            raise forms.ValidationError(f"A production record for {ticker} / {period} already exists. Use the edit form.")
        return cleaned

#validates updating production record (checks ounces not negative)
class ProductiondataUpdateForm(forms.ModelForm):
    class Meta:
        model = Productiondata
        fields = ['silver_ounces_produced', 'notes']

    def clean_silver_ounces_produced(self):
        val = self.cleaned_data.get('silver_ounces_produced')
        if val is not None and val < 0:
            raise forms.ValidationError("Ounces produced cannot be negative.")
        return val


# ─────────────────────────────────────────────────────────────────────────────
# INVESTOR FILTER / SEARCH
# ─────────────────────────────────────────────────────────────────────────────
#validates the optional search and filter parameters investors use
class CompanyFilterForm(forms.Form):
    search = forms.CharField(required=False, max_length=100)
    max_aisc = forms.DecimalField(required=False, min_value=0)
    max_debt_equity = forms.DecimalField(required=False, min_value=0)
    max_peg = forms.DecimalField(required=False, min_value=0)

