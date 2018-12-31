import sys
import telepot
from telepot.exception import TelegramError
from question_manager import Question_Manager
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
@version: 0.95
@author: Jonathan Geiger    
"""

_verbose = True
_version = 0.95

#args
TOKEN = sys.argv[1]
USER = sys.argv[2]
SOURCE_JSON = sys.argv[3]
BUGREPORT_JSON = "bugreport.json"

# global variables
q_man = Question_Manager(jsonfile=SOURCE_JSON)
meta = MetaData(TOKEN, USER, SOURCE_JSON, BUGREPORT_JSON)
bot = None
myHandler = None
event = None


def on_question_alarm(dict):
    """ function get called regularly by scheduler """
    print("on_question_alarm(event):", dict)
    print("type(event)", type(dict))
    print("queue:", bot.scheduler._eventq)
    print("len(queue)", len(bot.scheduler._eventq))
    try:
        bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
    except TelegramError:
        pass
    if not meta.sleeps():
        if not q_man.state_STILL_OPEN():
            ask_randomQuestion()
        print("#", bot.scheduler)


def on_chat_message(msg):
    """ callbackFunction: wird bei eingehender Nachricht aufgerufen """
    global event
    try:
        content = msg['text']
    except BaseException:
        return
    if _verbose: print("input: " + content); print("msg:", msg)

    # try to delete the last InlineKeyboard
    try:
        bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
    except TelegramError:
        pass

    # freq merken
    tmp = meta.question_frequency_sec()

    myHandler.handle(content)

    # freq auf Änderung prüfen
    if tmp != meta.question_frequency_sec():
        # cur timer löschen und neuen mit neuer freq stellen
        try:
            if event: bot.scheduler.cancel(event)
        except:
            pass
        delay = meta.question_frequency_sec()
        any_data = None  # beliebige Daten im Event speichern, kann in Callback_fkt(event) abgerufen werden
        event = bot.scheduler.event_later(delay, {'_question_alarm': any_data})

    # neuern Timer stellen, wenn Frage richtig beantwortet
    if not q_man.state_STILL_OPEN():
        delay = meta.question_frequency_sec()
        any_data = None  # beliebige Daten in dict speichern, kann in Callback_fkt(dict) abgerufen werden
        event = bot.scheduler.event_later(delay, {'_question_alarm': any_data})
    if len(bot.scheduler._eventq) > 2:
        raise TelegramError("To many(>2) Events in Queue?!", None, None)


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



def ask_randomQuestion():
    """ Fragt eine zufaellig ausgewählte Frage """
    bot.sendMessage(USER, q_man.next_question())


def cleanUp():
    """ sichert Persistenz """
    print("\ncleanUp!")
    try:
        bot.deleteMessage(msg_identifier=meta.msg_id_last_InlineKeyboard())
    except TelegramError:
        pass
    q_man.saveValues()


def always_use_new(req, **user_kw):
    return None


if __name__ == "__main__":

    bot = telepot.Bot(TOKEN)

    # create Handler
    myHandler = Handler(bot, q_man, meta)

    t = bot.router.routing_table['_question_alarm'] = on_question_alarm

    #hack
    telepot.api._pools = {
        'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=6, timeout=30),
    }
    telepot.api._which_pool = always_use_new

    # first Question
    ask_randomQuestion()

    try:
        bot.message_loop({'chat': on_chat_message,
                          'callback_query': on_callback_query,
                          '_question_alarm': on_question_alarm},  # necessary for scheduler-callback
                         run_forever="{} runs!".format(bot.getMe()['username']))
    except KeyboardInterrupt:
        pass
    finally:
        cleanUp()


    # DEPRECATED
    # lifecycle: regelmaßig fragen...
    """while True:
        try:
            # regelmäßiges Fragen zwischen 22:45 und 7:30 Uhr.
            if True:# or time(22, 45) > datetime.now().time() > time(7, 30):
                if not q_man.state_STILL_OPEN() and not bot_sleeps:
                    ask_randomQuestion()
                sleep(60 * 0.5)
        except KeyboardInterrupt as keyint:
            print("KeyboardInterrupt:", keyint)
            pass
        except BaseException as e:
            print("#exception:\n", e)
        finally:
            cleanUp()
            break"""
