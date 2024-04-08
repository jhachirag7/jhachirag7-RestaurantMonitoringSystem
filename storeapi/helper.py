from .models import Store,  Report , Status 
from django.utils import timezone 
from pytz import timezone as pytz_timezone
import datetime
import csv
import os
from django.conf import settings


# def binary_search_time(store, end_time, start_time, current_day):
#     if end_time >= start_time:
 
#         mid = start_time + (end_time - start_time)/2

#         store_business_hours = store.business_hour.filter(
#                 day=current_day,
#                 start_time__lte=mid,
#                 end_time__gte=mid
#         ).exists()
 
#         if not store_business_hours: # not considering this log in both uptime and downtime since it was not in the business hour
#             continue
 
#         # If element is smaller than mid, then it can only
#         # be present in left subarray
#         elif arr[mid] > x:
#             return binary_search(arr, low, mid - 1, x)
 
#         # Else the element can only be present in right subarray
#         else:
#             return binary_search(arr, mid + 1, high, x)
 
#     else:
#         # Element is not present in the array
#         return -1

def get_one_hour_data(store, utc_time, current_day, current_time):
    dict = {"uptime" : 0 , "downtime" : 0 }

    last_one_hour = (store.status.filter(timestamp__gte=utc_time - datetime.timedelta(hours=1)) & store.status.filter(timestamp__lte=utc_time)).order_by('timestamp')


    time=None
    last_status=None

    for log in last_one_hour:
        # checkig if store time overlap's with store business hours
        # case 1                                case 2                                   case 3
        # t=1 not business hour                 t=1 active                               t=1 not business hour
        # t=2 inactive                          t=2 inactive                             t=2 not business hour
        # t=3 active                            t=3 active                               t=3 active
        # t=4 active                            t=4 active                               t=4 active
        # t=5 not business hour                 t=5 not business hour                    t=5 inactive
        # t=6 not business hour                 t=6 not business hour                    t=6 active
        if current_day==log.timestamp.weekday():
            store_business_hours = store.business_hour.filter(
                day=log.timestamp.weekday(),
                start_time__lte=log.timestamp.time(),
                end_time__gte=log.timestamp.time()
            ).exists()
            
            if not store_business_hours: # not considering this log in both uptime and downtime since it was not in the business hour
                last_status=-1
                time=log.timestamp 
                continue
            if time==None:
                time=log.timestamp
            diff=log.timestamp-time # if it's in business hour calculating difference in previous and current log timestamp that would either be downtime or uptime
            if last_status == 1:
                dict["uptime"]+= diff.total_seconds()/60
            else:
                dict["downtime"]+= diff.total_seconds()/60
            time=log.timestamp
            last_status=log.status
    # edge case:
    # t=1 not business hour
    # t=2 not business hour
    # t=3 active
    # t=4 active
    if last_status is not None:
        diff=utc_time-time
        if last_status==1:
            dict["uptime"]+= diff.total_seconds()/60
        else:
            dict["downtime"]+= diff.total_seconds()/60
    
    return dict


def get_one_day_data(store, utc_time, current_day, current_time):
    dict = {"uptime" : 0 , "downtime" : 0}
    one_day_ago = current_day - 1

    
    last_one_day = (store.status.filter(timestamp__gte=utc_time - datetime.timedelta(days=1)) & store.status.filter(timestamp__lte=utc_time)).order_by('timestamp')
    time=None
    last_status=None
    for log in last_one_day:
        # checkig if store time overlap's with store business hours
        store_business_hours = store.business_hour.filter(
            day__gte=one_day_ago,
            day__lte=current_day,
            start_time__lte=log.timestamp.time(),
            end_time__gte=log.timestamp.time()
            ).exists()

        if not store_business_hours: # not considering this log in both uptime and downtime since it was not in the business hour
            last_status=-1
            time=log.timestamp 
            continue
        if time==None:
            time=log.timestamp
        diff=log.timestamp-time # if it's in business hour calculating difference in previous and current log timestamp that would either be downtime or uptime
        if last_status == 1:
            dict["uptime"]+= diff.total_seconds()/3600
        else:
            dict["downtime"]+= diff.total_seconds()/3600
        time=log.timestamp
        last_status=log.status

    if last_status is not None:
        diff=utc_time-time
        if last_status==1:
            dict["uptime"]+= diff.total_seconds()/3600
        else:
            dict["downtime"]+= diff.total_seconds()/3600
    return dict

def get_one_week_data(store, utc_time, current_day, current_time):
    dict = {"uptime" : 0 , "downtime" : 0}
    one_week_ago = current_day - 7

    # getting all the logs in last one week
    last_one_week_logs = (store.status.filter(timestamp__gte=utc_time - datetime.timedelta(days=7))& store.status.filter(timestamp__lte=utc_time)).order_by('timestamp')
    time=None
    last_status=None
    for log in last_one_week_logs:
       # checkig if store time overlap's with store business hours
        store_business_hours = store.business_hour.filter(
            day__gte=one_week_ago,
            day__lte=current_day,
            start_time__lte=log.timestamp.time(),
            end_time__gte=log.timestamp.time()
            ).exists()

        if not store_business_hours: # not considering this log in both uptime and downtime since it was not in the business hour
            last_status=-1
            time=log.timestamp 
            continue
        if time==None:
            time=log.timestamp
        diff=log.timestamp-time # if it's in business hour calculating difference in previous and current log timestamp that would either be downtime or uptime
        if last_status == 1:
            dict["uptime"]+= diff.total_seconds()/3600
        else:
            dict["downtime"]+= diff.total_seconds()/3600
        time=log.timestamp
        last_status=log.status

    if last_status is not None:
        diff=utc_time-time
        if last_status==1:
            dict["uptime"]+= diff.total_seconds()/3600
        else:
            dict["downtime"]+= diff.total_seconds()/3600
    
    return dict


def generate_report(store):
    tz = store.timezonestr
    timezone = pytz_timezone(tz)
    time = Status.objects.all().order_by('-timestamp').first().timestamp
    local_time = time.astimezone(timezone)
    utc_timezone = pytz_timezone('UTC')
    utc_time = time.astimezone(utc_timezone)
    current_day = local_time.weekday()
    current_time = local_time.time()

    hour_data = get_one_hour_data(store, utc_time, current_day, current_time)

    day_data = get_one_day_data(store, utc_time, current_day, current_time)


    week_data = get_one_week_data(store, utc_time, current_day, current_time)

    data = []
    data.append(store.pk)
    data.extend(list(hour_data.values()))
    data.extend(list(day_data.values()))
    data.extend(list(week_data.values()))

    return data


def generate_report_csv(report_data,report):
    file_name = f"{report.reportid}.csv"
    file_path = os.path.join(settings.BASE_DIR/'reports_csv', file_name)
    #print(report.reportid)
    with open(file_path, "w", newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["store_id", "last_one_hour uptime(in minutes)", "last_one_hour downtime(in minutes)", "last_one_day uptime(in hours)", "last_one_day downtime(in hours)", "last_one_week uptime(in hours)", "last_one_week downtime(in hours)"])
            for data in report_data:
                #print(data)
                csv_writer.writerow(data)
            
    report.report_url.save(file_name, open(file_path, "rb"))
    report.status = 1
    report.save()