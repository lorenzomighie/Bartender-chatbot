import random
from bar import Drink
from utils import text2int, join_with_and, debug
import datetime
import numpy as np
from enum import Enum


class Bartender:

    class States(Enum):
        NEW_CLIENT = 1
        WAITING_ORDER = 2
        PAYMENT = 3
        ACCEPT_SUGGESTION = 4
        NUMBER_SUGGESTED = 5
        DELETE_NUMBER = 6

    def __init__(self, bar):
        self.bar = bar
        self.state = self.States.NEW_CLIENT
        self.orders = {}
        self.suggested_drink = None
        self.known_drinks = {}

        for category in Drink.CATEGORY:
            with open("../res/" + category + "_list.txt", "r") as file:
                a = file.readlines()
                self.known_drinks[category] = [line.strip().lower() for line in a]

    def get_drink_list(self, category):
        return self.known_drinks[category]

    def suggest(self, ordered_items=None, category=None):
        # suggest with a probability as high as the price

        # do not suggest something alredy ordered
        if ordered_items:
            drinks = list(set(self.bar.get_drinks(category)) - ordered_items.keys())
        else:
            drinks = self.bar.get_drinks(category)

        prices = np.array([drink.price for drink in drinks])
        probability = 1. / np.sum(prices)*prices
        return np.random.choice(drinks, p=probability)

    def respond(self, doc):
        debug(doc)
        intents = []  # [self.check_sentence]
        if self.state is self.States.NEW_CLIENT:
            intents.extend([self.greetings, self.specific_order, self.generic_order, self.suggestion])
        elif self.state is self.States.WAITING_ORDER:
            intents.extend([self.specific_order, self.generic_order, self.suggestion, self.delete_item, self.end_order])
        elif self.state is self.States.PAYMENT:
            intents.append(self.confirmation_payment)  # , self.delete_item])
        elif self.state is self.States.ACCEPT_SUGGESTION:
            intents.append(self.confirmation_suggestion)
        elif self.state is self.States.NUMBER_SUGGESTED:
            intents.append(self.get_the_number)

        intents.append(self.leave)
        intents.append(self.not_understood)

        for intent in intents:
            answer = intent(doc)
            if answer:
                return answer

    def greetings(self, doc):
        greeting_queries = ["hello", "hi", "greetings", "good evening", "what's up", "good morning",
                            "good afternoon", "hey", "yo"]

        now = datetime.datetime.now()
        if 6 <= now.hour < 12:
            a = "Good morning! "
        elif 12 <= now.hour < 17:
            a = "Good afternoon! "
        else:
            a = "Good evening! "
        greeting_1 = ["Hello!", "Hi!", "Greetings!", a]
        greeting_2 = ["We offer some of the best Earth beers and wines, what do you want to take?",
                      "I'm Bender the bartender, what do you want to order?",
                      "Welcome to the Life On Mars pub, what can I do for you?"]

        for token in doc:
            if token.pos_ == 'VERB':
                return None

        for greeting in greeting_queries:
            if greeting in doc.text:
                self.state = self.States.WAITING_ORDER
                return random.choice(greeting_1) + random.choice(greeting_2)

    def specific_order(self, doc):
        # spacy returns verbs at infinity form with .lemma_
        ordering_verbs = ["order", "like", "have", "take", "make", "give", "want", "get", "buy", "add"]
        ans_pos = ["Ok I will add [noun1] to the list!",
                   "Ok I have added [noun1] to the order.",
                   "Good choice with [noun1]."]
        ans_donthave = ["Unfortunately we don't have [noun1].",
                        "Unfortunately we ran out of [noun1].",
                        "Sorry but we don't have any [noun1]."]
        ans_not_understood = ["I am not programmed to understand the rest of what you just said.",
                              "My circuits do not provide any info for the other items."]
        ans_suggest = ["I can suggest you a fresh [noun1]. Would you like it?"]
        ans_ending = ["Would you like something else?",
                      "Do you wish to order something else?",
                      "Would you like to add some other drinks?"]

        bad_items = {}  # set()
        ordered_items = {}
        not_understood = False

        print(list(doc.noun_chunks))
        # noun_chunks:  spacy command which divides 'noun plus the words' describing the noun
        for span in doc.noun_chunks:
            root = span.root
            if root.dep_ == 'nsubj':  # ex I or Mary , this noun_chunk is not relevant
                continue

            # nome puntato dal verbo di odinazione o nome puntato da un altro nome (puntato da verbo di ordinazione)
            if (((root.pos_ == 'NOUN' or root.pos_ == "PROPN") and root.dep_ == 'dobj' and
               root.head.lemma_ in ordering_verbs) or
               (root.dep_ == 'conj' and (root.head.pos_ == 'NOUN' or root.head.pos_ == "PROPN")) or
               (root.dep_ == 'appos' and (root.head.pos_ == 'NOUN' or root.head.pos_ == "PROPN"))):

                long_name = []
                num = 1
                for child in root.children:
                    if child.dep_ == 'compound':
                        long_name.append(child.text)
                    if child.pos_ == 'NUM' and child.dep_ == 'nummod':
                        try:
                            num = int(child.lemma_)
                        except ValueError:
                            num = text2int(child.lemma_)

                long_name.append(root.lemma_)
                composed_name = ''
                for n, i in enumerate(long_name):
                    if n == len(long_name) - 1:
                        composed_name = composed_name + i
                    else:
                        composed_name = composed_name + i + ' '

                composed_name = composed_name.lower()

                flag = True
                if composed_name in [drink.name for drink in self.bar.get_drinks()]:
                    ordered_items.setdefault(composed_name, 0)
                    ordered_items[composed_name] += num  # works also with unspecified number = 1
                else:
                    for category in Drink.CATEGORY:
                        if composed_name in self.get_drink_list(category):
                            flag = False
                            bad_items[composed_name] = category  # add(composed_name)  # items not in the list
                    if flag:
                        not_understood = True

        answer = []
        # Processing positive part:
        if ordered_items:
            self.state = self.States.WAITING_ORDER
            for item in ordered_items:
                self.orders.setdefault(self.bar.get_drink(item), 0)
                self.orders[self.bar.get_drink(item)] += ordered_items[item]

            if not not_understood and not bad_items:
                noun1 = 'that'
            else:
                noun1 = join_with_and([str(num) + ' ' + item for item, num in ordered_items.items()])

            part_pos = random.choice(ans_pos)
            part_pos = part_pos.replace('[noun1]', noun1)
            answer.append(part_pos)

        # Processing bad items part:
        if bad_items:
            part_donthave = random.choice(ans_donthave)
            noun1 = join_with_and(list(bad_items.keys()))
            part_donthave = part_donthave.replace('[noun1]', noun1)
            answer.append(part_donthave)

            # Giving a suggestion:
            if len(bad_items) > 1 and not ordered_items:
                ordered_categories = list(bad_items.values())
                part_suggest = ''
                for cat in ordered_categories:
                    intro = 'Our list of  ' + cat + 's is the following: '
                    part_suggest = part_suggest + intro + join_with_and([drink.name for
                                                                         drink in self.bar.get_drinks(cat)])
                answer.append(part_suggest)
            elif len(bad_items) == 1:
                self.state = self.States.ACCEPT_SUGGESTION
                bad_item = list(bad_items.keys())[0]
                a = self.suggest(ordered_items, category=bad_items[bad_item])
                self.suggested_drink = a
                part_suggest = random.choice(ans_suggest)
                part_suggest = part_suggest.replace('[noun1]', a.name)
                answer.append(part_suggest)

        # Processing not understood part:
        if ordered_items and not bad_items and not_understood:
            answer.append(random.choice(ans_not_understood))

        if len(answer) == 0:
            return None

        # Adding final question:
        if not len(bad_items) == 1:
            answer.append(random.choice(ans_ending))
        return ' '.join(answer)

    def generic_order(self, doc):
        ordering_verbs = ["order", "can", "like", "have", "take", "make", "give", "want", "get", "buy", "add"]
        answers_list = ["We have the following [noun]s: ", "Our selection of [noun]s is the following: "]
        answers_suggest = ["I can suggest you a nice [noun]. Would you like it?"]
        probability = 0.8

        enter = False
        for token in doc:
            if token.lemma_ in ordering_verbs:
                enter = True
            if enter and token.lemma_ in Drink.CATEGORY:

                if random.random() < probability:
                    self.state = self.States.WAITING_ORDER
                    answer = random.choice(answers_list)
                    answer = answer.replace("[noun]", token.lemma_)
                    answer = answer + join_with_and([drink.name for drink in self.bar.get_drinks(token.lemma_)])
                    return answer
                else:
                    a = self.suggest(category=token.lemma_)
                    self.state = self.States.ACCEPT_SUGGESTION
                    answer = random.choice(answers_suggest)
                    answer = answer.replace("[noun]", a.name)
                    self.suggested_drink = a
                    return answer

    def end_order(self, doc):
        positive_simple = ['yes', 'positive', 'okay', 'ok', 'alright', 'right', 'good', 'yeah', 'cool', 'course',
                           'yep', 'certainly', 'sure', 'fine']
        positive_expression = ['of course', 'why not?', 'good idea', 'all right']
        negative_simple = ['no', "nope", "enough", 'finished', 'nope', 'negative', "money"]
        negative_expression = ["that's it", "it's enough", "that's all", "nothing else", "no more", "i'm done",
                               "how much", "how much is it", "how does it cost"]

        continue_answers = ["What can I do for you?", "What would you like?"]
        recap_answers = ["So, you have ordered [noun1], ", "A quick recap of what you've ordered: [noun1], "]
        payment_answers = ["which amounts to [noun1] euros. Proceed with the payment?",
                           "That makes a total of [noun1] euros. Shall we proceed?"]
        nothing_ordered = ["Well that's not gonna cost anything since your order is empty..." +
                           "Do you intend to actually order something?",
                           "Your order is empty, do you intend to actually order something?",
                           "Are you gonna order for real?"]
        for token in doc:
            if token.lemma_ in positive_simple:
                self.state = self.States.WAITING_ORDER
                return random.choice(continue_answers)
            # User wants to proceed with the payment
            if (token.pos_ == "NOUN" and token.lemma_ == 'payment') or (token.pos_ == "VERB" and token.lemma_ == 'pay')\
                    or (token.lemma_ in negative_simple):
                self.state = self.States.PAYMENT
                recap_answer = random.choice(recap_answers)
                noun1 = join_with_and([str(num) + ' ' + drink.name for drink, num in self.orders.items()])
                recap_answer = recap_answer.replace("[noun1]", noun1)
                payment_answer = random.choice(payment_answers)
                pay = sum([n*drink.price for drink, n in self.orders.items()])
                if pay % 1 == 0:
                    pay = int(pay)
                if pay == 0:
                    self.state = self.States.WAITING_ORDER
                    return random.choice(nothing_ordered)
                payment_answer = payment_answer.replace('[noun1]', str(pay))
                return recap_answer + payment_answer

        # Controllo su espressioni (parole multiple)
        for phrase in negative_expression:
            if phrase in doc.text:
                self.state = self.States.PAYMENT
                recap_answer = random.choice(recap_answers)
                noun1 = join_with_and([str(num) + ' ' + drink.name for drink, num in self.orders.items()])
                recap_answer = recap_answer.replace("[noun1]", noun1)
                payment_answer = random.choice(payment_answers)
                pay = sum([n*drink.price for drink, n in self.orders.items()])
                if pay % 1 == 0:
                    pay = int(pay)
                if pay == 0:
                    self.state = self.States.WAITING_ORDER
                    return random.choice(nothing_ordered)
                payment_answer = payment_answer.replace('[noun1]', str(pay))
                return recap_answer + payment_answer

        for phrase in positive_expression:
            if phrase in doc.text:
                self.state = self.States.WAITING_ORDER
                return random.choice(continue_answers)

    def confirmation_payment(self, doc):
        positive_simple = ['yes', 'positive', 'okay', 'ok', 'alright', 'right', 'good', 'yeah', 'cool', 'course',
                           'yep', 'certainly', 'sure', 'fine']
        positive_expression = ['of course', 'why not?', 'good idea', 'all right']
        negative_simple = ['no', "nope", "enough", 'finished', 'nope', 'negative', 'modify']

        finish_answers = ["Thanks for your patience, your order will be ready in a second!",
                          "Enjoy your drink and your visit on our planet!"]
        negative_answers = ["Ok, you can modify your order as you wish.",
                            "You can add or delete any drink from your order.",
                            "Tell me if you wish to remove or add something."]

        for phrase in positive_expression:
            if phrase in doc.text:
                self.state = self.States.NEW_CLIENT
                return random.choice(finish_answers)
        for token in doc:
            if token.lemma_ in negative_simple:
                self.state = self.States.WAITING_ORDER
                return random.choice(negative_answers)
            if token.lemma_ in positive_simple:
                self.state = self.States.NEW_CLIENT
                return random.choice(finish_answers)

    def suggestion(self, doc):
        suggestion_verbs = ["advice", "recommend", "suggest", "think"]
        support_verbs = ["give", "be"]
        support_nouns = ["advice", "idea", "suggestion", "choice", "recommendation"]
        answer_suggest_cat = ["I recommend you a [noun1] which is an excellent [noun2]. Would you try it?",
                              "You should try the [noun1] it's a very typical Earth [noun2]. Will you get a taste?"]
        answers_suggest = ["In my opinion [noun1] is a really good [noun2]. Do you want it?",
                           "You can't say you have tried the Earth taste until you drink the [noun1]. " +
                           "Would you try it?",
                           "The [noun1] is renowned among terrestrial beings to be a terrific [noun2]. " +
                           "Shall I add it?"]
        enter = False
        for token in doc:  # look for a suggestion of a certain category
            if token.lemma_ in suggestion_verbs:
                enter = True
            if token.lemma_ in support_verbs:
                for child in token.children:
                    if (child.dep_ == 'dobj' or child.dep_ == 'attr') and child.lemma_ in support_nouns:
                        enter = True
        if enter:
            for token in doc:
                if token.lemma_ in Drink.CATEGORY:
                    a = self.suggest(category=token.lemma_)
                    self.state = self.States.ACCEPT_SUGGESTION
                    self.suggested_drink = a
                    answer = random.choice(answer_suggest_cat)
                    answer = answer.replace('[noun1]', a.name)
                    answer = answer.replace('[noun2]', token.lemma_)
                    return answer

            # entra quando non e' stata trovata una categoria (consiglio generico)
            a = self.suggest()
            self.state = self.States.ACCEPT_SUGGESTION
            self.suggested_drink = a
            answer = random.choice(answers_suggest)
            answer = answer.replace('[noun1]', a.name)
            answer = answer.replace('[noun2]', a.category)
            return answer

    def confirmation_suggestion(self, doc):
        positive_simple = ['yes', 'positive', 'okay', 'ok', 'alright', 'right', 'good', 'yeah', 'cool', 'course',
                           'yep', 'certainly', 'sure', 'fine']
        positive_expression = ['of course', 'why not?', 'good idea', 'all right']
        negative_simple = ['no', "nope", "enough", 'finished', 'nope', 'negative', 'modify']

        answers_pos = ["Okay, I've just added it. Would you like to add something else?",
                       "Perfect, anything else?",
                       "You'll see, it's magnificent! Do you wish to add something else?"]
        answer_num = ["Excellent, how many [noun1] do you want?",
                      "Perfect, how many [noun1] should I prepare?"]

        for token in doc:
            if token.text in positive_simple:
                num = 0
                for j in doc:
                    if j.text == 'a':
                        num = 1
                    if j.pos_ == 'NUM':
                        try:
                            num = int(j.lemma_)
                        except ValueError:
                            num = text2int(j.lemma_)
                        break
                if num != 0:
                    self.orders[self.bar.get_drink(self.suggested_drink.name)] = num
                    self.suggested_drink = None
                    self.state = self.States.WAITING_ORDER
                    return random.choice(answers_pos)
                else:
                    self.state = self.States.NUMBER_SUGGESTED
                    # print(self.suggested_drink.name)
                    answer = random.choice(answer_num)
                    answer = answer.replace('[noun1]', self.suggested_drink.name)
                    return answer
            if token.text in negative_simple:
                self.suggested_drink = None
                self.state = self.States.WAITING_ORDER
                return "No problem, so what else would you like?"

        for phrase in positive_expression:
            if phrase in doc.text:
                num = 0
                for j in doc:
                    if j.text == 'a':
                        num = 1
                    if j.pos_ == 'NUM':
                        try:
                            num = int(j.lemma_)
                        except ValueError:
                            num = text2int(j.lemma_)
                        break
                if num != 0:
                    self.orders[self.bar.get_drink(self.suggested_drink.name)] = num
                    self.suggested_drink = None
                    self.state = self.States.WAITING_ORDER
                    return random.choice(answers_pos)
                else:
                    self.state = self.States.NUMBER_SUGGESTED
                    # print(self.suggested_drink.name)
                    answer = random.choice(answer_num)
                    answer = answer.replace('[noun1]', self.suggested_drink.name)
                    return answer

    def get_the_number(self, doc):
        answers = ["Nice, would you like to add something?",
                   "Perfect, anything else?",
                   "Well done, do you wish to add something else?"]
        num = 0
        for j in doc:
            if j.text == 'a':
                num = 1
            if j.pos_ == 'NUM' or (j.tag_ == 'LS' and j.pos_ == 'PUNCT'):
                try:
                    num = int(j.lemma_)
                except ValueError:
                    num = text2int(j.lemma_)
                break
        if num == 0:
            return "Please, specify a number!"
        else:
            self.orders[self.bar.get_drink(self.suggested_drink.name)] = num
            self.suggested_drink = None
            self.state = self.States.WAITING_ORDER
            return random.choice(answers)

    def delete_item(self, doc):
        # spacy returns verbs at infinity form with .lemma_
        delete_verbs = ["remove", "delete", "drop"]
        ans_remove = ["I have removed [noun1].",
                      "As you wish, so I've deleted [noun1].",
                      "No problem [noun1] successfully removed!"]
        ans_ending = ["Do you wish to add or remove something?",
                      "Do you wish to order or remove something else?",
                      "Would you like to add or remove some other drinks?"]
        ans_donthave = ["You didn't order any [noun1].",
                        "Sorry but you didn't take any [noun1]."]
        ans_not_understood = ["I am not programmed to understand the rest of what you just said.",
                              "My circuits do not provide any info for the other items."]
        ans_recap = ["So far you have ordered [noun1].",
                     "A quick recap of what you've ordered: [noun1],"]

        ans_invalid = ["I couldn't delete [noun1] because you went below zero.",
                       "If I remove [noun1] you would end up with a negative order, so I cannot do it."]

        bad_items = {}  # set()
        deleted_items = {}
        not_understood = False

        print(list(doc.noun_chunks))
        # noun_chunks:  spacy command which divides 'noun plus the words' describing the noun
        for span in doc.noun_chunks:
            root = span.root
            if root.dep_ == 'nsubj':  # ex I or Mary , this noun_chunk is not relevant
                continue

            if (((root.pos_ == 'NOUN' or root.pos_ == "PROPN") and root.dep_ == 'dobj' and
                 root.head.lemma_ in delete_verbs) or
                    (root.dep_ == 'conj' and (root.head.pos_ == 'NOUN' or root.head.pos_ == "PROPN")) or
                    (root.dep_ == 'appos' and (root.head.pos_ == 'NOUN' or root.head.pos_ == "PROPN"))):

                long_name = []
                num = 1
                for child in root.children:
                    if child.dep_ == 'compound':
                        long_name.append(child.text)
                    if child.pos_ == 'NUM' and child.dep_ == 'nummod':
                        try:
                            num = int(child.lemma_)
                        except ValueError:
                            num = text2int(child.lemma_)

                long_name.append(root.lemma_)
                composed_name = ''
                for n, i in enumerate(long_name):
                    if n == len(long_name) - 1:
                        composed_name = composed_name + i
                    else:
                        composed_name = composed_name + i + ' '

                composed_name = composed_name.lower()

                flag = True
                if composed_name in [drink.name for drink in self.orders.keys()]:
                    deleted_items.setdefault(composed_name, 0)
                    deleted_items[composed_name] += num  # works also with unspecified number = 1
                else:
                    for category in Drink.CATEGORY:
                        if composed_name in self.get_drink_list(category):
                            flag = False
                            bad_items[composed_name] = category  # add(composed_name)  # items not in the list
                    if flag:
                        not_understood = True

        answer = []
        # Processing positive part:
        deleted_real = {}
        invalid_delete = {}
        if deleted_items:
            # self.state = self.States.WAITING_ORDER
            for item in deleted_items:

                # self.orders.setdefault(self.bar.get_drink(item), 0)
                old_n = self.orders[self.bar.get_drink(item)]
                if old_n > deleted_items[item]:
                    self.orders[self.bar.get_drink(item)] -= deleted_items[item]
                    deleted_real[item] = deleted_items[item]
                elif old_n == deleted_items[item]:
                    del self.orders[self.bar.get_drink(item)]
                    deleted_real[item] = deleted_items[item]
                else:
                    invalid_delete[item] = deleted_items[item]

            if deleted_real:
                noun1 = join_with_and([str(num) + ' ' + item for item, num in deleted_real.items()])
                part_neg = random.choice(ans_remove)
                part_neg = part_neg.replace('[noun1]', noun1)
                answer.append(part_neg)
            if invalid_delete:
                noun1 = join_with_and([str(num) + ' ' + item for item, num in invalid_delete.items()])
                part_invalid = random.choice(ans_invalid)
                part_invalid = part_invalid.replace('[noun1]', noun1)
                answer.append(part_invalid)

        # Processing bad items part:
        if bad_items:
            part_donthave = random.choice(ans_donthave)
            noun1 = join_with_and(list(bad_items.keys()))
            part_donthave = part_donthave.replace('[noun1]', noun1)
            answer.append(part_donthave)

            # Recap
            part_recap = random.choice(ans_recap)
            noun1 = join_with_and([str(num) + ' ' + drink.name for drink, num in self.orders.items()])
            part_recap = part_recap.replace("[noun1]", noun1)
            answer.append(part_recap)

        # Processing not understood part:
        if deleted_items and not bad_items and not_understood:
            answer.append(random.choice(ans_not_understood))

        if len(answer) == 0:
            return None

        # Adding final question:
        answer.append(random.choice(ans_ending))
        return ' '.join(answer)

    def not_understood(self, doc):
        answers = ["sorry I didn't understood, please rephrase.",
                   "I didn't get what you said, try to say that again.",
                   "What did you mean with that?"]
        return random.choice(answers)

    def leave(self, doc):
        queries_simple = ["nevermind", "leave", "go", "away", "outside"]
        queries_expression = ["don't want to order", "forget it", "changed my mind", "have to go"]
        answers = ["This was faster than expected! ", "Well, goodbye!", "Okay, beware of the red sandstorm outside!"]

        for phrase in queries_expression:
            if phrase in doc.text:
                self.state = self.States.NEW_CLIENT
                return random.choice(answers)
        for token in doc:
            if token.lemma_ in queries_simple:
                self.state = self.States.NEW_CLIENT
                return random.choice(answers)
