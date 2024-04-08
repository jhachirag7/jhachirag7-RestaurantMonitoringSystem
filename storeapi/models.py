from django.db import models




class Store(models.Model):
    storeid = models.CharField(max_length=50, primary_key=True)
    timezonestr = models.CharField(max_length=50,null=True,blank=True)

    def __str__(self):
        return self.storeid


class BusinessHour(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="business_hour")
    day = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.store.storeid}"



class Status(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="status")
    status = models.IntegerField()
    timestamp = models.DateTimeField(verbose_name="UTC",null=True,blank=True)

    def get_local_timestamp(self):
        return self.timestamp.astimezone(self.store.timezone_str)
    
    def __str__(self):
        return f"{self.store.storeid} - {self.status} - {self.timestamp}"



class Report(models.Model):
    reportid = models.CharField(max_length=50, primary_key=True)
    status = models.IntegerField()
    report_url = models.FileField(upload_to="reports",null=True,blank=True)