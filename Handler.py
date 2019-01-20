import re
import json
from telepot import message_identifier
from telepot.namedtuple import ReplyKeyboardMarkup
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime


"""
Hier wird sich um das Abarbeiten der eingehenden Nachrichten gekümmert.
"""


class Handler(object):
    def __init__(self, bot, question_manager, meta_data):
        """
        :type bot: telepot.Bot
        :type question_manager: QuestionManager
        :param meta_data: MetaDaten-Obj des Bots
        """
        self._bot = bot
        self._q_man = question_manager
        self._meta = meta_data
        self._user = self._meta.user()
        self._handlerDict = {'start': StartHandler(self._bot, self._user),
                             'next': NextHandler(self._bot, self._user, self._q_man),
                             'again': AgainHandler(self._bot, self._user, self._q_man),
                             'help': HelpHandler(self._bot, self._user, self._q_man),
                             'sleep': SleepHandler(self._bot, self._user, self._meta),
                             'wakeup': WakeUpHandler(self._bot, self._user),
                             'stats': StatsHandler(self._bot, self._user, self._q_man),
                             'keyboard': KeyboardHandler(self._bot, self._user),
                             'bugreport': BugreportHandler(self._bot, self._user, self._meta),
                             'create': CreateHandler(self._bot, self._user, self._q_man),
                             'cycle': CycleHandler(self._bot, self._user, self._meta),
                             'sof': SofHandler(self._bot, self._user)}

    def handle(self, msg):
        """
        :type msg: reiner Nachrichten-String(z.B. '/cmd foo1 foo2')
        :return True, wenn frage mit msg richtig beantwortet wurde, sonst False
        """

        # when I SLEEP...(zzz)
        if self._meta.sleeps():
            if msg.startswith("/wakeup"):
                self._meta.wakeup()
            else:
                self._bot.sendMessage(self._user, "😴\n You can activate me up with: /wakeup")
            return

        # I'm AWAKE!
        if msg.startswith("/"):

            """ COMMANDS """
            try:
                cmd = re.search("\w+", msg).group()
                self._handlerDict[cmd].handle(msg)
            except KeyError:
                self._bot.sendMessage(self._user, "Sorry, unsupported command🧐")

        else:

            """ USER beantwortet Frage """
            if self._q_man.state_STILL_OPEN():
                try:
                    correct, output = self._q_man.evalQ(msg)
                except BaseException as e:
                    print("evaluation failed"); print(e)
                    self._bot.sendMessage(self._user, "Kann Antwort nicht evaluieren. Ist aber mein Fehler ;)"
                                          "\n Also weiter gehts:...(/next)")
                    return
                # richtige Antwort
                if correct:
                    self._bot.sendMessage(self._user, output)
                    return True
                else:
                    # fasche Antwort
                    self._bot.sendMessage(self._user, output)
                    if self._q_man.get_fail_counter() >= 3:
                        # -> Hilfe
                        markup = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="Ja", callback_data="spicker_1")],
                            [InlineKeyboardButton(text="Nein", callback_data="spicker_0")],
                        ])

                        sent = self._bot.sendMessage(self._user, text="Willst du spicken?", reply_markup=markup)
                        self._meta.set_msg_id_last_InlineKeyboard(msg_id=message_identifier(sent))
                        self._q_man.reset_fail_counter()
            else:
                print("ignore input({})".format(msg))
        return False



class CommandHandler(object):
    """ kind of interface """
    def __init__(self, bot=None, user=None, q_man=None):
        self._bot = bot
        self._user = user
        self._q_man = q_man

    def handle(self, msg):
        """ :type msg: reiner Nachrichten-String(z.B. '/cmd foo1 foo2') """
        raise NotImplementedError


class StartHandler(CommandHandler):
    def __init__(self, bot, user):
        super().__init__(bot, user)
        self._start_msg = """Ich stelle Fragen, Du beantwortest
Sonst gibts noch fogende Befehle:

/next - Frage überspringen
/again - aktuelle Frage nochmal stellen
/help - Hilfe zum Lösen
/sleep - Ich geh schlafen und nerv dich nicht
/wakeup - Ich wache wieder auf
/stats - ein paar Statistiken
/bugreport - einen Fehler melden
/create - eine Frage hinzufuegen
/cycle - wie oft(Minuten) soll gefragt werden
/sof - sucht in StackOverlFlow
"""

    def handle(self, msg):
        self._bot.sendMessage(self._user, self._start_msg)


class NextHandler(CommandHandler):
    def __init__(self, bot, user, q_man):
        super().__init__(bot, user, q_man)

    def handle(self, msg):
        self._bot.sendMessage(self._user, self._q_man.next_question())


class AgainHandler(CommandHandler):
    def __init__(self, bot, user, q_man):
        super().__init__(bot, user, q_man)

    def handle(self, msg):
        if self._q_man.state_ANSWERED_CORRECTLY():
            self._bot.sendMessage(self._user, "/next für nächste Frage")
        else:
            self._bot.sendMessage(self._user, self._q_man.cur_question())


class HelpHandler(CommandHandler):#
    def __init__(self, bot, user, q_man):
        super().__init__(bot, user, q_man)

    def handle(self, msg):
        if self._q_man.state_STILL_OPEN():
            self._bot.sendMessage(self._user, self._q_man.cur_answer())
        else:
            self._bot.sendMessage(self._user, "/next für nächste Frage")


class SleepHandler(CommandHandler):
    def __init__(self, bot, user, meta):
        super().__init__(bot, user)
        self._meta = meta

    def handle(self, msg):
        self._meta.fall_asleep()
        self._bot.sendMessage(self._user, "😴")


class WakeUpHandler(CommandHandler):
    def __init__(self, bot, user):
        super().__init__(bot, user)

    def handle(self, msg):
        self._bot.sendMessage(self._user, "I'm awake!😳")


class StatsHandler(CommandHandler):
    def __init__(self, bot, user, q_man):
        super().__init__(bot, user, q_man)

    def handle(self, msg):
        self._bot.sendMessage(self._user, self._q_man.stats())


class KeyboardHandler(CommandHandler):
    def __init__(self, bot, user):
        super().__init__(bot, user)

    def handle(self, msg):
        markup = ReplyKeyboardMarkup(keyboard=[
            ["/next", "/again", "/help"],
            ["/sleep", "/wakeup"],
            ["/stats", "/bugreport", "/create"]
        ])
        self._bot.sendMessage(self._user, text="Here you are.", reply_markup=markup)


class BugreportHandler(CommandHandler):
    def __init__(self, bot, user, meta):
        super().__init__(bot, user)
        self._meta = meta

    def handle(self, msg):
        if len(msg) == len("/bugreport"):
            # Hinweis: How to use
            self._bot.sendMessage(self._user, "Du hast einen Bug gefunden?\n"
                                  "Dann nutzte den command: /bugreport und deine Nachricht direkt dahinter."
                                  "z.B.: '/bugreport wenn ich x drücke, dann passiert y'")
        else:
            # Verarbeitung
            with open(self._meta.bugreport(), 'r+') as file:
                data = json.load(file)
                data["id"] += 1
                bugdict = {"id": data["id"],
                           "date": str(datetime.now()),
                           "description": msg[len("/bugreport "):]}
                data["bugs"].append(bugdict)
                file.seek(0)
                json.dump(data, file)
                file.truncate()
            self._bot.sendMessage(self._user, "Danke, ich kümmere mich drum.😊")


class CreateHandler(CommandHandler):
    def __init__(self, bot, user, q_man):
        super().__init__(bot, user, q_man)

    def handle(self, msg):
        valid = re.match(r'/create ".+" ".+" ".+"$', msg)
        if msg == "/create" or not valid:
            s = "Mit /create kannst du neue Fragen erstellen.\n" \
                "Gib das ganze folgendermaßen an:\n" \
                "/create \"frage\" \"antwort\" \"regEx\" "
            self._bot.sendMessage(self._user, s)
        if valid:
            _, question, answer, regEx = msg.split()
            self._q_man.addQuestion(question, answer, regEx)
            self._bot.sendMessage(self._user, "Ich habe deine Frage aufgenommen!👍")


class CycleHandler(CommandHandler):
    def __init__(self, bot, user, meta):
        super().__init__(bot, user)
        self._meta = meta

    def handle(self, msg):
        try:
            num = float(msg.split()[1])
            self._meta.set_question_frequency(minutes=num)
            self._bot.sendMessage(self._user, "Alles klar!\nIch frage jetzt alle {} min. ".format(num))
        except (ValueError, IndexError):
            s = "aktuell: {}min\nWillst du sie ändern gibt eine Zahl an: z.B. /cycle 3.14".format(
                self._meta.question_frequency_sec() / 60)
            self._bot.sendMessage(self._user, s)


class SofHandler(CommandHandler):
    def __init__(self, bot, user):
        super().__init__(bot, user)

    def handle(self, msg):
        try:
            # cutting cmd off && remove question mark at the and if existing
            striped = re.search(r'(?!=/sof) .*[^?]', msg).group()
            # build link
            link = "https://stackoverflow.com/search?q=" + "+".join(striped.split())
            print("link: ", link)
            self._bot.sendMessage(self._user, link)
        except BaseException as e:
            print(e)
            self._bot.sendMessage(self._user, "Something went wrong. Try again!😬")