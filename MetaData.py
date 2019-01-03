from datetime import datetime, time

"""
"Nehmen und weitergeben."
Speichert den Zustand des Bots.
"""

class MetaData(object):
    """ Hält Metadaten eines Bots """
    def __init__(self, token, user, source, bugreport):
        self._token = token
        self._user = user
        self._source = source
        self._bugreport = bugreport
        self._sleeps = False
        self._msg_id_last_InlineKeyboard = None
        self._question_frequency_min = 0.25

    def token(self):
        return self._token

    def user(self):
        return self._user

    def source(self):
        return self._source

    def bugreport(self):
        return self._bugreport

    def msg_id_last_InlineKeyboard(self):
        return self._msg_id_last_InlineKeyboard

    def set_msg_id_last_InlineKeyboard(self, msg_id):
        self._msg_id_last_InlineKeyboard = msg_id

    def question_frequency_sec(self):
        return self._question_frequency_min * 60

    def set_question_frequency(self, minutes):
        self._question_frequency_min = minutes

    def sleeps(self):
        """ :return: True if, at sleep, else False(awake) """
        return self._sleeps

    def is_night(self):
        if time(23, 00) > datetime.now().time() > time(6, 30):
            return False
        return True

    def fall_asleep(self):
        self._sleeps = True

    def wakeup(self):
        self._sleeps = False

