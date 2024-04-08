from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
from django.conf import settings
from .models import Store,BusinessHour,Status,Report
import csv
from datetime import datetime
import threading 
import pytz
from django.utils.timezone import make_aware
from .helper import generate_report,generate_report_csv
import secrets
naive_datetime = datetime.now()
naive_datetime.tzinfo  # None

settings.TIME_ZONE  # 'UTC'
aware_datetime = make_aware(naive_datetime)
aware_datetime.tzinfo

def insertStore(source_file_path):
    store_list=[]
    with open(source_file_path, 'r') as source_file:
        reader = csv.reader(source_file)
        next(reader)  # Skip the header row
        # Iterate through the rows in the source file
        for row in reader:
            id, timezone = str(row[0]).strip(), str(row[1]).strip()
            store_=Store(storeid=id,timezonestr=timezone)
            store_list.append(store_)
        Store_=Store.objects.bulk_create(store_list)

def insertBusinessHours(source_file_path):
    business_list=[]
    with open(source_file_path, 'r') as source_file:
        reader = csv.reader(source_file)
        next(reader)  # Skip the header row
        # Iterate through the rows in the source file
        for row in reader:
            id, day, start, end = str(row[0]).strip(), int(row[1]), str(row[2]).strip(), str(row[3]).strip()
            start= datetime.strptime(start, "%H:%M:%S").time()
            end= datetime.strptime(end, "%H:%M:%S").time()
            try:
                store=Store.objects.get(storeid=id)
                bussiness_=BusinessHour(store=store,day=day,start_time=start,end_time=end)
                business_list.append(bussiness_)
            except Exception as e:
                print("Error",e)
        Business_=BusinessHour.objects.bulk_create(business_list)

def insertStatus(source_file_path):
    status_list=[]
    with open(source_file_path, 'r') as source_file:
        reader = csv.reader(source_file)
        next(reader)  # Skip the header row
        # Iterate through the rows in the source file
        for row in reader:
            id, status, timestamp_UTC = str(row[0]).strip(), str(row[1]).strip(), str(row[2]).strip()
            try:
                datetime_object = datetime.strptime(timestamp_UTC, "%Y-%m-%d %H:%M:%S.%f UTC")
            except Exception as e:
                datetime_object = datetime.strptime(timestamp_UTC, "%Y-%m-%d %H:%M:%S UTC")
            chicago_timezone = pytz.timezone('America/Chicago')
            datetime_object.astimezone(chicago_timezone)
            val=0
            if status=='active':
                val=1
            try:
                store=Store.objects.get(storeid=id)
                status_=Status(store=store,status=val,timestamp=datetime_object)
                status_list.append(status_)
            except Exception as e:
                print("Error",e)
        Status_=Status.objects.bulk_create(status_list)





@api_view(['GET'])
def getRoute(request):
    routes = [
        'GET /insert',
        'GET /trigger_report',
        'GET /get_report'
    ]
    return Response(routes)

@api_view(['GET'])
def insertData(request):
    file_path_store = os.path.join(settings.BASE_DIR, 'timezone.csv')
    file_path_business = os.path.join(settings.BASE_DIR, 'Menu_hours.csv')
    file_path_status = os.path.join(settings.BASE_DIR, 'store_status.csv')

    t1=threading.Thread(target=insertStore,args=(file_path_store,))
    t1.start()
    t1.join()
    t2=threading.Thread(target=insertBusinessHours,args=(file_path_business,))
    t3=threading.Thread(target=insertStatus,args=(file_path_status,))

    t2.start()
    t3.start()
    t2.join()
    t3.join()
    
    return Response({"successfully inserted"})

class MyThread(threading.Thread):
    def __init__(self, target=None, args=(),kwargs={}):
        threading.Thread.__init__(self,target=target, args=args,kwargs=kwargs)
        self._result = None

    def run(self):
        if self._target is not None:
            self._result = self._target(*self._args,**self._kwargs)

    def join(self):
        threading.Thread.join(self)
        return self._result


@api_view(['GET'])
def trigger_report(request):
    # try:
        stores = Store.objects.all()
        reportid=secrets.token_urlsafe(16)
        report = Report.objects.create(reportid=reportid, status=0)
        report_data=[]
        threads = []
        i=0
        for store in stores:
            thread = MyThread(target=generate_report, args=(store,))
            thread.start()
            threads.append(thread)
            i=i+1
            if i>=100:
                break
        for thread in threads:
            result=thread.join()
            report_data.append(result)
        generate_report_csv(report_data,report)
        return Response(status=200, data={"report_id": report.reportid})
    # except Exception as e:
    #     return Response(status=404, data={"Error": str(e)})


@api_view(['GET'])
def getReport(request, pk):
    try:
        report = Report.objects.get(reportid=str(pk))
        if report.status == 1:
            report_url = settings.MEDIA_ROOT + "/" + report.report_url.name
            print(report_url)
            return Response(status=200,data={"report_url": report_url,"status": "Complete"})
        else:
            return Response(status=200, data={"status": "Running"}) 
    except Exception as e:
        return Response(status=404, data={"Error": e})
