from bookStoreInfo import BookStoreInfo, dprint, dprint_json
from datetime import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastApi


sched = BackgroundScheduler(timezone='Asia/Shanghai')
app = FastApi()
bi = BookStoreInfo("config.toml")


def cur_time_str():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def print_appointment():
    import pandas as pd
    ap = bi.getAppointmentRecords()
    ap = ap[ap['sign'] == False]
    ap['begintime'] = pd.to_datetime(ap['currentday'] + ' ' + ap['stime'])
    ap = ap[['id', 'begintime', 'etime', 'rname',
             'status', 'flag', 'cstatus', 'bstatus']]
    ap.sort_values(by='begintime', inplace=True, ascending=False)
    now_pd = pd.to_datetime(datetime.now())
    ap = ap[ap['begintime'] > now_pd - pd.Timedelta(minutes=20)]
    return dprint_json(ap)


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

@app.get('/help')
def help():
    return """
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
            """.format(cur_time_str())

@app.get('/la')
def la():
    return dprint_json(bi.full_data)
@app.get('/ls')
def ls():
    return dprint_json(bi.avai_data)
@app.get('/ap')
def ap():
    return print_appointment()
@app.get('/jb')
def get_jobs():
    return str(sched.get_jobs())
@app.get('s')
def sched_next():
    sc = sched.get_job('nxt_day_app')
    if sc:
        return "Job already exists"
    else:
        app_time = datetime.now()
        app_time = app_time.replace(
            day=app_time.day + 1, hour=0, minute=0, second=2, microsecond=0)
        # app_time = app_time.replace(second=app_time.second + 1)
        
        sched.add_job(scheduled_appointment, 'date',
                        run_date=app_time, id='nxt_day_app')
        return "Job Will Start At {}.".format(app_time)
@app.get('lock')
def lock_up():
    sc = sched.get_job('auto_reappoint')
    if sc:
        return "Auto ReAppoint Job already exists"
    else:
        sched.add_job(auto_reappoint, 'interval',
                        seconds=5, id='auto_reappoint')
        return "Lock Success"
@app.get('unlk')
def lock_down():
    sched.remove_job("auto_reappoint")
    return "Lock State End"
        elif command[0] == "sn":
            scheduled_appointment()
        elif command[0] == "cs":
            sched.remove_job("nxt_day_app")
        elif command[0] == "clear":
            os.system('clear')
        else:
            print('Unknown command\nPrint "help" for more information')
        print("> ", end='')
