
def text2int(textnum, numwords={}):
    if not numwords:
        units = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
                 "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
                 "sixteen", "seventeen", "eighteen", "nineteen"]

        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

        scales = ["hundred", "thousand", "million", "billion", "trillion"]

        numwords["and"] = (1, 0)
        for idx, word in enumerate(units):
            numwords[word] = (1, idx)
        for idx, word in enumerate(tens):
            numwords[word] = (1, idx * 10)
        for idx, word in enumerate(scales):
            numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
            raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current


def join_with_and(collection):
    if not collection:
        raise ValueError
    if len(collection) == 1:
        return collection[0]
    else:
        return ", ".join(collection[:-1]) + " and " + collection[-1]


def debug(doc):
    for token in doc:
        print('text: ' + token.text, 'lemma: ' + token.lemma_, 'tag: ' + token.tag_,
              'pos: ' + token.pos_, 'head.lemma: ' + token.head.lemma_, 'dep_:' + token.dep_, sep=' ' * 4)
        print('\n')
