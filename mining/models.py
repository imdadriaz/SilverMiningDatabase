"""
Models for the Silver Mining Database.

All models use managed=False, this is so that django will not create or modify the tables

"""

from django.db import models


# ─────────────────────────────────────────────────────────────────────────────
# USERTAB
# ─────────────────────────────────────────────────────────────────────────────

class Usertab(models.Model):

    class PermissionLevel(models.TextChoices):
        INVESTOR = 'Investor', 'Investor'
        ADMIN    = 'Admin',    'Admin'

    user_id = models.AutoField(primary_key = True, db_column = 'User_ID')
    user_fname       = models.CharField(max_length = 50,  db_column = 'User_FName')
    user_lname       = models.CharField(max_length = 50,  db_column = 'User_LName')
    user_email       = models.CharField(max_length = 100, db_column = 'User_Email', unique=True)
    user_password    = models.CharField(max_length = 200, db_column = 'User_Password')
    permission_level = models.CharField(
        max_length=10,
        choices=PermissionLevel.choices,
        db_column='Permission_Level',
    )
    is_active = models.BooleanField(default=False, db_column = 'Is_Active')

    class Meta:
        db_table = 'USERTAB'
        managed  = False

    def __str__(self):
        return f"{self.user_fname} {self.user_lname} ({self.permission_level})"

    @property
    def is_admin(self):
        return self.permission_level == self.PermissionLevel.ADMIN

    @property
    def is_investor(self):
        return self.permission_level == self.PermissionLevel.INVESTOR

    def set_password(self, raw_password: str):
        import bcrypt
        hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt())
        self.user_password = hashed.decode()

    def check_password(self, raw_password: str) -> bool:
        import bcrypt
        try:
            return bcrypt.checkpw(raw_password.encode(), self.user_password.encode())
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# COMPANY
# ─────────────────────────────────────────────────────────────────────────────

class Company(models.Model):
    ticker = models.CharField(max_length = 10, primary_key=True, db_column = 'Ticker')
    company_name = models.CharField(max_length = 50, db_column = 'Company_Name')

    class Meta:
        db_table = 'COMPANY'
        managed = False

    def __str__(self):
        return f"{self.company_name} ({self.ticker})"


# ─────────────────────────────────────────────────────────────────────────────
# FAVOURITE
# ─────────────────────────────────────────────────────────────────────────────

class Favourite(models.Model):
    investor = models.ForeignKey(Usertab, on_delete = models.CASCADE, db_column = 'Investor_ID', related_name = 'favourites')
    ticker = models.ForeignKey(Company, on_delete = models.CASCADE, db_column = 'Ticker', related_name = 'favourited_by')
    date_favourited = models.DateField(db_column ='DateFavourited')

    class Meta:
        db_table = 'FAVOURITE'
        managed = False
        unique_together = (('investor', 'ticker'),)

    def __str__(self):
        return f"{self.investor} - {self.ticker_id}"


# ─────────────────────────────────────────────────────────────────────────────
# RANKINGREPORT
# ─────────────────────────────────────────────────────────────────────────────

class Rankingreport(models.Model):
    ticker = models.OneToOneField(Company, on_delete = models.CASCADE, primary_key=True, db_column = 'Ticker')
    score = models.DecimalField(max_digits = 5,  decimal_places = 2, db_column = 'Score')
    rank_position = models.IntegerField(db_column = 'RankPosition')

    class Meta:
        db_table = 'RANKINGREPORT'
        managed  = False

    def __str__(self):
        return f"#{self.rank_position} {self.ticker_id} - {self.score}"


# ─────────────────────────────────────────────────────────────────────────────
# FINMETRICS
# ─────────────────────────────────────────────────────────────────────────────

class Finmetrics(models.Model):
    ticker = models.OneToOneField(Company, on_delete = models.CASCADE, primary_key=True, db_column = 'Ticker', related_name = 'finmetrics')
    aisc            = models.DecimalField(max_digits = 12, decimal_places = 2, db_column = 'AISC')
    peg             = models.DecimalField(max_digits = 6,  decimal_places = 2, db_column = 'PEG')
    total_debt      = models.DecimalField(max_digits = 15, decimal_places = 2, db_column = 'TotalDebt')
    debt_to_equity  = models.DecimalField(max_digits = 6,  decimal_places = 2, db_column = 'DebtToEquity')
    revenue         = models.DecimalField(max_digits = 15, decimal_places = 2, db_column = 'Revenue')
    ebitda          = models.DecimalField(max_digits = 15, decimal_places = 2, db_column = 'EBITDA')
    last_updated_by = models.ForeignKey(Usertab, on_delete=models.SET_NULL, null=True, blank=True, db_column='LastUpdatedBy', related_name='finmetrics_updated')

    class Meta:
        db_table = 'FINMETRICS'
        managed  = False

    def __str__(self):
        return f"FinMetrics - {self.ticker_id}"


# ─────────────────────────────────────────────────────────────────────────────
# STOCKPRICE
# ─────────────────────────────────────────────────────────────────────────────

class Stockprice(models.Model):
    ticker              = models.ForeignKey(Company, on_delete=models.CASCADE, primary_key=True, db_column = 'Ticker', related_name = 'stock_prices')
    date_updated = models.DateField(primary_key=True, db_column='Date_Updated')
    previous_open = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, blank=True, db_column = 'PreviousOpen')
    previous_close = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, blank=True, db_column = 'PreviousClose')
    fifty_two_week_high = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, blank=True, db_column = 'FiftyTwoWeekHigh')
    fifty_two_week_low  = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, blank=True, db_column = 'FiftyTwoWeekLow')

    class Meta:
        db_table = 'STOCKPRICE'
        managed = False
        unique_together = (('ticker', 'date_updated'),)

    def __str__(self):
        return f"{self.ticker_id} @ {self.date_updated}"


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTIONDATA
# ─────────────────────────────────────────────────────────────────────────────

class Productiondata(models.Model):
    ticker = models.ForeignKey(Company, on_delete = models.CASCADE, primary_key=True, db_column = 'Ticker', related_name = 'production_records')
    period = models.CharField(max_length = 20, primary_key=True, db_column = 'Period')
    silver_ounces_produced = models.DecimalField(max_digits = 15, decimal_places = 2, null=True, blank=True, db_column = 'SilverOuncesProduced')
    notes = models.TextField(null=True, blank=True, db_column = 'Notes')
    last_updated_by = models.ForeignKey(Usertab, on_delete = models.SET_NULL, null=True, blank=True, db_column = 'LastUpdatedBy', related_name = 'production_updated')

    class Meta:
        db_table = 'PRODUCTIONDATA'
        managed = False
        unique_together = (('ticker', 'period'),)

    def __str__(self):
        return f"{self.ticker_id} - {self.period}"


# ─────────────────────────────────────────────────────────────────────────────
# VIEWSDETAILS
# ─────────────────────────────────────────────────────────────────────────────

class Viewsdetails(models.Model):
    investor = models.ForeignKey(Usertab, on_delete = models.CASCADE, db_column = 'InvestorID', related_name = 'viewed_companies')
    ticker = models.ForeignKey(Company, on_delete = models.CASCADE, db_column = 'Ticker', related_name = 'viewed_by')

    class Meta:
        db_table = 'VIEWSDETAILS'
        managed = False
        unique_together = (('investor', 'ticker'),)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATESCOMPANY
# ─────────────────────────────────────────────────────────────────────────────

class Updatescompany(models.Model):
    admin  = models.ForeignKey(Usertab, on_delete = models.CASCADE, db_column ='AdminID', related_name = 'updated_companies')
    ticker = models.ForeignKey(Company, on_delete = models.CASCADE, db_column ='Ticker')

    class Meta:
        db_table = 'UPDATESCOMPANY'
        managed = False
        unique_together = (('admin', 'ticker'),)
        

# ─────────────────────────────────────────────────────────────────────────────
# UPDATESFINMETRICS
# ─────────────────────────────────────────────────────────────────────────────

class Updatesfinmetrics(models.Model):
    admin  = models.ForeignKey(Usertab, on_delete = models.CASCADE, db_column ='AdminID', related_name = 'updated_fin_metrics')
    ticker = models.ForeignKey(Company, on_delete = models.CASCADE, db_column ='Ticker')

    class Meta:
        db_table = 'UPDATESFINMETRICS'
        managed = False
        unique_together = (('admin', 'ticker'),)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATESSTOCKPRICE
# ─────────────────────────────────────────────────────────────────────────────

class Updatesstockprice(models.Model):
    admin = models.ForeignKey(Usertab, on_delete = models.CASCADE, db_column = 'AdminID', related_name = 'updated_stock_prices')
    ticker = models.ForeignKey(Company, on_delete = models.CASCADE, db_column = 'Ticker')
    date_updated = models.DateField(db_column = 'Date_Updated')

    class Meta:
        db_table = 'UPDATESSTOCKPRICE'
        managed = False
        unique_together = (('admin', 'ticker', 'date_updated'),)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATESPRODUCTIONDATA
# ─────────────────────────────────────────────────────────────────────────────

class Updatesproductiondata(models.Model):
    admin  = models.ForeignKey(Usertab, on_delete = models.CASCADE, db_column = 'AdminID', related_name = 'updated_production_data')
    ticker = models.ForeignKey(Company, on_delete = models.CASCADE, db_column = 'Ticker')
    period = models.CharField(max_length=20, db_column='Period')

    class Meta:
        db_table = 'UPDATESPRODUCTIONDATA'
        managed = False
        unique_together = (('admin', 'ticker', 'period'),)
