import os
from apscheduler.schedulers.background import BackgroundScheduler
from bookStoreInfo import BookStoreInfo, dprint

scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

bi = BookStoreInfo("config.toml")


def now_time_pd():
    from pandas import to_datetime
    from datetime import datetime
    return to_datetime(datetime.now())


def cur_time_str():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def get_ruled_appointment():
    import pandas as pd
    ap = bi.getAppointmentRecords()
    ap = ap[ap['sign'] == False]
    ap['begintime'] = pd.to_datetime(ap['currentday'] + ' ' + ap['stime'])
    ap = ap[['id', 'begintime', 'etime', 'rname', 'status', 'flag', 'cstatus', 'bstatus']]
    ap.sort_values(by='begintime', inplace=True, ascending=False)
    now_pd = now_time_pd()
    ap = ap[ap['begintime'] > now_pd]
    return ap


def try_make_auto_reappoint_job():
    from time import sleep
    sched_appoint_job = scheduler.get_job('auto_reappoint')
    if sched_appoint_job:
        print("Auto ReAppoint Job already exists")
    else:
        now_pd = now_time_pd()
        now_delay = float(now_pd.strftime('%S.%f')) % 5
        if now_delay < 2.5:
            sleep(2.5 - now_delay)
        else:
            sleep(7.5 - now_delay)
        now_pd.replace(second=0, microsecond=0)
        scheduler.add_job(auto_reappoint, 'interval',
                          seconds=5, id='auto_reappoint')


def auto_reappoint():
    # Version 2

    now_pd = now_time_pd()
    ap = get_ruled_appointment()
    dprint(ap)
    print(now_pd, end=' ')
    cur_ap = ap.iloc[-1, :]
    if cur_ap['begintime'] > now_pd:
        delta = cur_ap['begintime'] - now_pd
        print(delta.total_seconds())
        if delta.total_seconds() < 5:
            from time import sleep
            print('Auto ReAppoint Begin!')
            print(bi.cancelAppointment(cur_ap['id']).json())
            print('CanCel Success!')
            sleep(delta.total_seconds() + 0.5)
            res = bi.makeOneSeatEveryAppointment()
            if len(res) > 0:
                print("Warning! Perhaps Unsigned.\n[LOCKED RESULT]")
                for time_period in res.keys():
                    print("[{}]{} {} {}".format(cur_time_str(), time_period, res[time_period]['status'],
                                                res[time_period]['content']))
            print('ReAppoint Success!')


@scheduler.scheduled_job('interval', seconds=5, id="refresh", max_instances=100)
def refresh():
    bi.__init__("config.toml")


def scheduled_appointment():
    res = bi.makeOneSeatEveryAppointment(force=True)
    print("[SCHEDULED RESULT]")
    for time_period in res.keys():
        print("[{}]{} {} {}".format(cur_time_str(), time_period,
                                    res[time_period]['status'], res[time_period]['content']))
    try_make_auto_reappoint_job()


scheduler.start()

if __name__ == "__main__":
    print('WelCome to SchoolLibrary REPL v0.3!\nPrint "help" for more information\n> ', end='')
    while True:
        command = input().strip().split()
        if not command:
            pass
        elif command[0] == "help":
            print("""
[{}]
help: print this help message
exit: exit the program
la  : print school library full list
ls  : print school library avai list
ap  : print appointments list
jb  : print background jobs(debug)
r   : force refresh info(debug)
cs  : cancel sched
st  : set current seat
sn  : sched now(force)
s   : sched next_day
lock: lock chosen seat
unlk: unlock chosen seat
            """.format(cur_time_str()))
        elif command[0] == "exit":
            scheduler.shutdown(wait=False)
            print("Bye!")
            break
        elif command[0] == "la":
            dprint(bi.full_data)
        elif command[0] == "ls":
            dprint(bi.avai_data)
        elif command[0] == "ap":
            dprint(get_ruled_appointment())
        elif command[0] == "jb":
            print(scheduler.get_jobs())
        elif command[0] == "s":
            sc = scheduler.get_job('nxt_day_app')
            if sc:
                print("Job already exists")
            else:
                from datetime import datetime

                app_time = datetime.now()
                app_time = app_time.replace(
                    day=app_time.day + 1, hour=0, minute=0, second=2, microsecond=0)
                # app_time = app_time.replace(second=app_time.second + 1)
                print("Job Will Start At {}.".format(app_time))
                scheduler.add_job(scheduled_appointment, 'date',
                                  run_date=app_time, id='nxt_day_app')
        elif command[0] == "lock":
            try_make_auto_reappoint_job()
        elif command[0] == "unlk":
            try:
                scheduler.remove_job("auto_reappoint")
            except Exception as e:
                print("Already Removed")
        elif command[0] == "sn":
            scheduled_appointment()
        elif command[0] == "cs":
            scheduler.remove_job("nxt_day_app")
        elif command[0] == "clear":
            os.system('clear')
        else:
            print('Unknown command\nPrint "help" for more information')
        print("> ", end='')
