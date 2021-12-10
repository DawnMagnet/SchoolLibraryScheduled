import os
from bookStoreInfo import BookStoreInfo, dprint
from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

bi = BookStoreInfo("config.toml")


def now_time_pd():
    from pandas import to_datetime
    from datetime import datetime
    return to_datetime(datetime.now())


def cur_time_str():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def make_new_line():
    print("\b\b\b\b\b\b\b\b\b\b> ", end='')

@scheduler.scheduled_job('interval', seconds=60*20, id="refresh", max_instances=100)
def refresh():
    bi.__init__("config.toml")
    # dprint(bi.ruled_appointment)
    print(cur_time_str(), "user A", bi.sign(sign_config='SIGN_PARAM'))
    print(cur_time_str(), "user B", bi.sign(sign_config='SIGN_PARAM_2'))
    make_new_line()
    


def scheduled_appointment():
    res = bi.makeOneSeatEveryAppointment(force=True)
    print("[SCHEDULED RESULT]")
    for time_period in res.keys():
        print("[{}]{} {} {}".format(cur_time_str(), time_period,
                                    res[time_period]['status'], res[time_period]['content']))


scheduler.start()

if __name__ == "__main__":
    print('WelCome to SCL REPL v0.4!\nPrint "help" for more information\n> ', end='')
    while True:
        try:
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
    sg  : sign(force)
    st  : set current seat
    sn  : sched now(force)
    s   : sched next_day
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
                dprint(bi.ruled_appointment)
            elif command[0] == "jb":
                print(scheduler.get_jobs())
            elif command[0] == "sg":
                if len(command) > 1:
                    print(bi.sign(command[1]))
                else:
                    print(bi.sign())
            elif command[0] == "s":
                from datetime import datetime
                app_time = datetime.now()
                app_time = app_time.replace(
                    day=app_time.day + 1, hour=0, minute=0, second=2, microsecond=0)
                # app_time = app_time.replace(second=app_time.second + 1)
                print("Job Will Start At {}.".format(app_time))
                scheduler.add_job(scheduled_appointment, 'date',
                                    run_date=app_time, id='nxt_day_app')
            elif command[0] == "r":
                refresh()
            elif command[0] == "sn":
                scheduled_appointment()
            elif command[0] == "cs":
                scheduler.remove_job("nxt_day_app")
            elif command[0] == "clear":
                os.system('clear')
            else:
                print('Unknown command\nPrint "help" for more information')
            make_new_line()
        except Exception as e:
            print(e)
            make_new_line()
            pass
