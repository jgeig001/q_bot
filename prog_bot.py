import sys
import telepot
from telepot.exception import TelegramError, EventNotFound
from questionmanager import QuestionManager
from Handler import Handler
from MetaData import MetaData
# hack
import telepot.api, urllib3

"""
Hallo,
ich bin der prog_bot und stelle dir regelmäßig ein paar Fragen.
Das Skript ist aktuell nur für einen Anwender ausgelegt.

Skript starten:
    pyhon3 prog_bot.py _TOKEN_ _USER_ _SOURCE_JSON_

@startdate: 10.12.2018
@version: 1.0
@author: Jonathan Geiger
@date: 20.01.2019
"""

__version__ = '1.0'
__author__ = 'Jonathan Geiger'
__date__ = '2019/01/20'
__description__ = """Hallo,
ich bin der prog_bot und stelle dir regelmäßig ein paar Fragen.
Das Skript ist aktuell nur für einen Anwender ausgelegt."""

_verbose = True

#args
TOKEN = sys.argv[1]
USER = sys.argv[2]
SOURCE_JSON = sys.argv[3]
BUGREPORT_JSON = "bugreport.json"

# global variables
q_man = QuestionManager(jsonfile=SOURCE_JSON)
meta = MetaData(TOKEN, USER, SOURCE_JSON, BUGREPORT_JSON)
bot = None
myHandler = None
event = None


def on_question_alarm(dict):
    """ function get called regularly by scheduler """
    global event
    if meta.is_night():
        try:
            if event: bot.scheduler.cancel(event)
        except EventNotFound:
            pass
        delay = meta.question_frequency_sec()
        event = bot.scheduler.event_later(delay, {'_question_alarm': None})
    else:
        try:
            bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
        except TelegramError:
            pass
        if not meta.sleeps():
            if not q_man.state_STILL_OPEN():
                bot.sendMessage(USER, q_man.next_question())
            print("#", bot.scheduler)


def on_chat_message(msg):
    """ callbackFunction: wird bei eingehender Nachricht aufgerufen """
    global event
    try:
        content = msg['text']
    except BaseException:
        return
    if _verbose: print("input: " + content)
    # try to delete the last InlineKeyboard
    try:
        bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
    except TelegramError:
        pass

    # freq merken
    tmp = meta.question_frequency_sec()

    set_timer = myHandler.handle(content)

    # freq auf Änderung prüfen
    if tmp != meta.question_frequency_sec():
        # cur timer löschen und neuen mit neuer freq stellen
        try:
            if event: bot.scheduler.cancel(event)
        except EventNotFound:
            pass
        delay = meta.question_frequency_sec()
        any_data = None  # beliebige Daten im Event speichern, kann in Callback_fkt(event) abgerufen werden
        event = bot.scheduler.event_later(delay, {'_question_alarm': any_data})

    # neuern Timer stellen, wenn Frage richtig beantwortet
    if set_timer:
        delay = meta.question_frequency_sec()
        any_data = None  # beliebige Daten in dict speichern, kann in Callback_fkt(dict) abgerufen werden
        event = bot.scheduler.event_later(delay, {'_question_alarm': any_data})
        if _verbose: print("set_timer({})".format(delay))
    if len(bot.scheduler._eventq) > 3:
        print("To many(>3) Events in Queue?!")
        raise RuntimeWarning("To many(>3) Events in Queue?!")


def on_callback_query(msg):
    """ verarbeitet callback_query """
    if _verbose: print(msg)
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

    if query_data == 'spicker_1':

        # Helfen
        bot.answerCallbackQuery(query_id, text=q_man.cur_answer())  # dropdown on top
        # InlineKeyboard löschen
        try:
            bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
        except TelegramError:
            pass

    elif query_data == "spicker_0":

        # NICHT helfen
        bot.answerCallbackQuery(query_id, text="ok")  # dropdown on top
        # InlineKeyboard löschen
        try:
            bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
        except TelegramError:
            pass



def cleanUp():
    """ sichert Persistenz """
    print("\ncleanUp!")
    try:
        bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
    except TelegramError:
        pass
    q_man.saveValues()


# needed to fix urllib3 issue
def always_use_new(req, **user_kw):
    return None


if __name__ == "__main__":

    bot = telepot.Bot(TOKEN)

    # create Handler
    myHandler = Handler(bot, q_man, meta)

    t = bot.router.routing_table['_question_alarm'] = on_question_alarm

    # urllib3-fix
    telepot.api._pools = {
        'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=6, timeout=30),
    }
    telepot.api._which_pool = always_use_new

    # first Question
    bot.sendMessage(USER, q_man.next_question())

    try:
        bot.message_loop({'chat': on_chat_message,
                          'callback_query': on_callback_query,
                          '_question_alarm': on_question_alarm},  # necessary for scheduler-callback
                         run_forever="{} runs!".format(bot.getMe()['username']))
    except KeyboardInterrupt:
        pass
    finally:
        cleanUp()

