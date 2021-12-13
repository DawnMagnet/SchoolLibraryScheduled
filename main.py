import os

from apscheduler.schedulers.background import BackgroundScheduler

from bookStoreInfo import BookStoreInfo
from bookStoreInfo import dprint

scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
bi = BookStoreInfo("config.toml")

def cur_time_str():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def make_new_line():
    print("> ", end='')

@scheduler.scheduled_job('cron', minute='5, 30', id="refresh", max_instances=100)
def refresh():
    bi.__init__("config.toml")
    for user in ['SIGN_PARAM', 'SIGN_PARAM_2']:
        if res := bi.sign(sign_config=user):
            print(cur_time_str(), user, res)

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
    s   : sched next_day(always)
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
                scheduler.print_jobs()
            elif command[0] == "sg":
                if len(command) > 1:
                    print(bi.sign(command[1]))
                else:
                    print(bi.sign())
            elif command[0] == "s":
                scheduler.add_job(scheduled_appointment, 'cron', hour='0', minute='0', second='2', id='nxt_day_app')
            elif command[0] == "r":
                refresh()
            elif command[0] == "sn":
                scheduled_appointment()
            elif command[0] == "cs":
                scheduler.remove_job("nxt_day_app")
            elif command[0] == "clear":
                os.system('clear')
            elif command[0] == 'dbg':
                print("Debug Mode(\q to quit)\n###>>> ", end='')
                while dbg_command := input():
                    if dbg_command == "\q":
                        break
                    try:
                        print(eval(dbg_command))
                    except Exception as e:
                        print(e)
                        pass
                    print("###>>> ", end='')
                print("Exit Debug Mode!")
            else:
                print('Unknown command\nPrint "help" for more information')
            make_new_line()
        except Exception as e:
            print(e)
            make_new_line()
            pass
