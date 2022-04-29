import asyncio
import time
import nest_asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bookStoreInfo import BookStoreInfo
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

VERSION = "0.8.3"

nest_asyncio.apply()
session: PromptSession = PromptSession(
    message="> ",
    history=InMemoryHistory(),
    auto_suggest=AutoSuggestFromHistory(),
)
job_defaults = {
    'coalesce': True,
    'misfire_grace_time': None
}
scheduler = AsyncIOScheduler(timezone='Asia/Shanghai', job_defaults=job_defaults)
bi = BookStoreInfo("config.toml")
helper_text = """
    [{}]

    [[program control]]
    help: print this help message
       ?: print this help message
    exit: exit the program

    [[data control]]
    la  : seat available
    ls  : seat raw
    lr  : seat full
    ap  : unsigned appointments
    ar  : appointments raw
    ra  : remove specific appointment

    [[scheduler control]]
    jb  : print background jobs(debug)
    r   : force refresh info(debug)
    cs  : cancel schedule
    sg  : sign(force)
    st  : set current seat
    sn  : schedule now(force)
    s   : schedule next_day
"""


def cur_time_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


async def sign_all():
    print(cur_time_str(), 'person1', bi.sign('person1'))
    print(cur_time_str(), 'person2', bi.sign('person2'))


@scheduler.scheduled_job('cron', minute='5, 30', hour='7-22', id="refresh")
async def refresh_and_sign_all():
    await bi.refresh()
    await sign_all()


@scheduler.scheduled_job('cron', hour='0', minute='0', second='0', id='nxt_day_app')
async def scheduled_appointment(seat=None, force='10-23'):
    # bi.refresh()
    res = await bi.makeOneSeatEveryAppointment(room_id=seat, force=force)
    print("[SCHEDULED RESULT]")
    for time_period in res.keys():
        print("[{}]{} {} {}".format(cur_time_str(), time_period,
                                    res[time_period]['status'], res[time_period]['content']))


async def main():
    print_formatted_text(FormattedText([
        ('#ffdd00', 'WelCome to '),
        ('#ff0000 bold', 'SCL REPL '),
        ('#44ff00 bold italic', f'v{VERSION}!\n'),
        ('', 'Print '),
        ('#ff00dd bold', 'help '),
        ('', 'for more information\n'),
    ]))
    await bi.refresh()
    while True:
        try:
            command: list[str] = session.prompt().strip().split()
            if not command:
                pass
            elif command[0] in ["help", "h", "?"]:
                print(helper_text.format(cur_time_str()))
            elif command[0] == "exit":
                scheduler.shutdown(wait=False)
                print("Bye!")
                break
            elif command[0] == "la":
                bi.showFullData()
            elif command[0] == "ls":
                bi.showAvailableData()
            elif command[0] == "lr":
                bi.showRawData()
            elif command[0] == "ap":
                bi.showUnsignedAppointment()
            elif command[0] == "ar":
                bi.showRawAppointment()
            elif command[0] == "ra":
                print(bi.cancelAppointment(command[1]).text)
            elif command[0] == "r":
                await refresh_and_sign_all()
                print('\b\b', end='')
            elif command[0] == "jb":
                scheduler.print_jobs()
            elif command[0] == "sg":
                if len(command) > 1 and command[1] == 'all':
                    await sign_all()
                elif len(command) > 1:
                    print(f'{command[1]} sign result: {bi.sign(command[1])}')
                else:
                    print(bi.sign())
            elif command[0] == "s":
                app_time = datetime.now()
                app_time = app_time.replace(
                    day=app_time.day + 1, hour=0, minute=0, second=0, microsecond=0)
                # app_time = app_time.replace(second=app_time.second + 1)
                print("Job Will Start At {}.".format(app_time))
                scheduler.add_job(scheduled_appointment, 'date',
                                  run_date=app_time, id='nxt_day_app')
            elif command[0] == "sn":
                if len(command) > 2:
                    await scheduled_appointment(command[1], command[2])
                elif len(command) > 1:
                    if len(command[1]) < 10:
                        await scheduled_appointment(force=command[1])
                    else:
                        await scheduled_appointment(seat=command[1])
                else:
                    await scheduled_appointment()
            elif command[0] == "cs":
                scheduler.remove_job("nxt_day_app")
            elif command[0] == "ca":
                print(bi.cancelAppointment(command[1]).json())
            elif command[0] == "clear":
                clear()
            else:
                print('Unknown command\nPrint "help" for more information')
        except Exception as e:
            print(e)

if __name__ == '__main__':
    scheduler.start()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
