import json, re
from random import gauss, randint
from enum import Enum
from functools import reduce

# states
states = Enum("States", "NOTHING_ASKED STILL_OPEN ANSWERED_CORRECTLY")

# bot_reply
positive = ["Yeah, richtig!", "👍", "👌", "Jajaja", "Das ist richtig", "True✅", "✅"]
negative = ["Nope", "Falsch", "False❌", "Ne", "Wrong", "❌"]


class Question_Manager(object):
    """ Verwaltet Fragenkatalog und Zustand """
    def __init__(self, jsonfile):
        self.qna_lis = []
        self.cur_index = 0
        self.path = jsonfile
        self.state = states.NOTHING_ASKED
        self.fail_counter = 0
        # fill qna_lis
        with open(self.path) as file:
            data = json.load(file)
            for key, value in data.items():
                obj = QnA(key, value["answer"], value["regex"], value["answered"], value["right"], value["wrong"])
                self.qna_lis.append(obj)

    def _nextIndex(self):
        """ generiert den nächsten Index(beliebig komlexes Verfahren) """
        # μ: Erwartungswert
        # σ: Standardabweichung
        μ = (len(self.qna_lis)/2) - 1
        σ = len(self.qna_lis) * (1/6)
        i = round(gauss(μ, σ))
        if i >= len(self.qna_lis) or i < 0:
            self.cur_index = len(self.qna_lis)
        else:
            self.cur_index = i
        return self.cur_index
        #return (self.cur_index + randint(1, len(self.qna_lis) - 2)) % (len(self.qna_lis)) #nice, but DEPRECATED

    def _nextQnA(self):
        """ :return nächste Frage(QnA) """
        self.fail_counter = 0
        self.state = states.STILL_OPEN
        return self.bell_curve()[self._nextIndex()]

    def bell_curve(self):
        lis = sorted(self.qna_lis, key=lambda x: x.wrong / (x.answered + 1))
        return lis[len(lis) % 2::2] + lis[::-2]

    def _curQnA(self):
        """ :return die aktuelle Frage(QnA) """
        return self.bell_curve()[self.cur_index]

    def next_question(self):
        """ :return nächste Frage(string) """
        return self._nextQnA().question

    def cur_question(self):
        """ :return aktuelle Frage(string) """
        return self._curQnA().question

    def cur_answer(self):
        return self._curQnA().answer

    def evalQ(self, given_answer):
        """
        Prueft mithilfe des regex, ob Frage richtig beantwortet wurde.
        Aktualisiert je nach Ergebnis den status.
        :type given_answer: string
        :return Tuple of (correctness, output_string)
                correctness: True, wenn richtig sonst False
                output_string: wenn richtig, einen züfalligen string aus global positive,
                               sonst einen zufälligen string aus global negative
        """
        correct = self._curQnA().evaluate(given_answer)
        if correct:
            self.state = states.ANSWERED_CORRECTLY
            return correct, positive[randint(0, len(positive)-1)]
        else:
            self.state = states.STILL_OPEN
            self.fail_counter += 1
            return correct, negative[randint(0, len(negative)-1)]

    def get_fail_counter(self):
        return self.fail_counter

    def reset_fail_counter(self):
        self.fail_counter = 0

    def state_NOTHING_ASKED(self):
        if self.state == states.NOTHING_ASKED:
            return True
        return False

    def state_STILL_OPEN(self):
        if self.state == states.STILL_OPEN:
            return True
        return False

    def state_ANSWERED_CORRECTLY(self):
        if self.state == states.ANSWERED_CORRECTLY:
            return True
        return False

    def stats(self):
        """ kleine Statistik als String """
        answered = reduce(lambda r, cur: r + cur, [qna.answered for qna in self.qna_lis], 0)
        right = reduce(lambda r, cur: r + cur, [qna.right for qna in self.qna_lis], 0)
        wrong = reduce(lambda r, cur: r + cur, [qna.wrong for qna in self.qna_lis], 0)
        s = "{} Fragen beantwortet\n{}-mal richt gelegen({:.2f}%)\n{}-mal falsch({:.2f}%)"
        s = s.format(answered, right, (right / answered) * 100, wrong, (wrong / answered) * 100)
        return s

    def saveValues(self):
        """ vor Beendigung des Programms werden die counter im jsonFile gesichert """
        with open(self.path, 'r+') as jsonfile:
            data = json.load(jsonfile)
            for obj in self.qna_lis:
                key = obj.question
                data[key]["answered"], data[key]["right"], data[key]["wrong"] = obj.answered, obj.right, obj.wrong
                jsonfile.seek(0)
                json.dump(data, jsonfile)
                jsonfile.truncate()


class QnA(object):
    """ Frage und Antwort(inkl. regex) + counter  """
    def __init__(self, question, answer, answer_regex, answered=0, right=0, wrong=0):
        self.question = question
        self.answer = answer
        self.regex = answer_regex
        # counter
        self.answered = answered
        self.right = right
        self.wrong = wrong

    def evaluate(self, given_answer):
        """ prueft gegebene Antwort und aktualisiert counter """
        self.answered += 1
        if re.match(pattern=self.regex, string=given_answer):
            self.right += 1
            return True
        self.wrong += 1
        return False

    def __str__(self):
        return "{} : [{}, {}, {}, {}, {}]".format(self.question, self.answer, self.regex, self.answered, self.right,
                                                  self.wrong)

    def __repr__(self):
        return self.__str__()