from bookStoreInfo import BookStoreInfo, dprint
from datetime import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler
sched = BackgroundScheduler(timezone='Asia/Shanghai')

bi = BookStoreInfo("config.toml")

def cur_time_str():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def print_appointment():
    import pandas as pd
    ap = bi.getAppointmentRecords()
    ap = ap[ap['sign'] == False]
    ap['begintime'] = pd.to_datetime(ap['currentday'] + ' ' + ap['stime'])
    ap = ap[['id', 'begintime', 'etime', 'rname', 'status', 'flag', 'cstatus', 'bstatus']]
    ap.sort_values(by='begintime', inplace=True, ascending=False)
    now_pd = pd.to_datetime(datetime.now())
    ap = ap[ap['begintime'] > now_pd - pd.Timedelta(minutes=20)]
    dprint(ap)

def auto_reappoint():
    # # Version 2
    # import pandas as pd
    # ap = bi.getAppointmentRecords()
    # ap = ap[ap['sign'] == False]
    # ap['begintime'] = pd.to_datetime(ap['currentday'] + ' ' + ap['stime'])
    # ap = ap[['id', 'begintime', 'etime', 'rname', 'status', 'flag', 'cstatus', 'bstatus']]
    # ap.sort_values(by='begintime', inplace=True, ascending=False)
    # now_pd = pd.to_datetime(datetime.now())
    # ap = ap[ap['begintime'] > now_pd - pd.Timedelta(minutes=20)]
    # dprint(ap)
    # cur_ap = ap.iloc[-1, :]
    # if cur_ap['begintime'] < now_pd:
    #     delta = now_pd - cur_ap['begintime']
    #     if delta.total_seconds() > 8 * 60:
    #         print('Auto ReAppoint Begin!')
    #         print(bi.cancelAppointment(cur_ap['id']).json())
    #         print('CanCel Success!')
    #         res = bi.makeOneSeatEveryAppointment()
    #         if len(res) > 0:
    #             print("Warning! Perhaps Unsigned.\n[LOCKED RESULT]")
    #             for time_period in res.keys():
    #                 print("[{}]{} {} {}".format(cur_time_str(), time_period, res[time_period]['status'], res[time_period]['content']))
    #         print('ReAppoint Success!')

    # Version 1
    try:
        res = bi.makeOneSeatEveryAppointment()
    except Exception as e:
        print('Somewhere Error')
    else:
        if len(res) > 0:
            print("Warning! Perhaps Unsigned.\n[LOCKED RESULT]")
            for time_period in res.keys():
                print("[{}]{} {} {}".format(cur_time_str(), time_period,
                      res[time_period]['status'], res[time_period]['content']))


@sched.scheduled_job('interval', seconds=5, id="refresh", max_instances=100)
def refresh():
    bi.__init__("config.toml")


def scheduled_appointment():
    res = bi.makeOneSeatEveryAppointment(force=True)
    print("[SCHEDULED RESULT]")
    for time_period in res.keys():
        print("[{}]{} {} {}".format(cur_time_str(), time_period,
              res[time_period]['status'], res[time_period]['content']))
    sc = sched.get_job('auto_reappoint')
    if sc:
        print("Auto ReAppoint Job already exists")
    else:
        sched.add_job(auto_reappoint, 'interval',
                      seconds=5, id='auto_reappoint')


sched.start()

if __name__ == "__main__":
    print('WelCome to SchoolLibrary REPL v0.2!\nPrint "help" for more information\n> ', end='')
    while True:
        command = input().strip().split()
        if command == []:
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
            sched.shutdown(wait=False)
            print("Bye!")
            break
        elif command[0] == "la":
            dprint(bi.full_data)
        elif command[0] == "ls":
            dprint(bi.avai_data)
        elif command[0] == "ap":
            print_appointment()
        elif command[0] == "jb":
            print(sched.get_jobs())
        elif command[0] == "s":
            sc = sched.get_job('nxt_day_app')
            if sc:
                print("Job already exists")
            else:
                app_time = datetime.now()
                app_time = app_time.replace(
                    day=app_time.day + 1, hour=0, minute=0, second=2, microsecond=0)
                # app_time = app_time.replace(second=app_time.second + 1)
                print("Job Will Start At {}.".format(app_time))
                sched.add_job(scheduled_appointment, 'date',
                              run_date=app_time, id='nxt_day_app')
        elif command[0] == "lock":
            sc = sched.get_job('auto_reappoint')
            if sc:
                print("Auto ReAppoint Job already exists")
            else:
                sched.add_job(auto_reappoint, 'interval',
                              seconds=5, id='auto_reappoint')
        elif command[0] == "unlk":
            sched.remove_job("auto_reappoint")
        elif command[0] == "sn":
            scheduled_appointment()
        elif command[0] == "cs":
            sched.remove_job("nxt_day_app")
        elif command[0] == "clear":
            os.system('clear')
        else:
            print('Unknown command\nPrint "help" for more information')
        print("> ", end='')
