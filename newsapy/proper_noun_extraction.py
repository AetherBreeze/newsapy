import nltk

from newsapy.const import FAKE_PROPER_NOUNS, JOINERS, PUNCTUATION_REPLACEMENT, NODE_DISTINGUISHERS, PUNCTUATION, SENTENCE_INTERRUPTORS, SINGLE_QUOTES, UPPERCASE_ASCII_VALUES_UPPER_BOUND, UPPERCASE_WORD_GARBAGE_THRESHHOLD, PROBLEM_WORDS, PROBLEM_PHRASES, ELLIPSES, WORD_SEPERATORS



def text_preprocess(text):
    for seperator in WORD_SEPERATORS:
        text = text.replace(seperator, ' ')

    words = text.split(' ')
    words = punctuation_parse(words)
    return remove_zero_length_strings(words)


def remove_zero_length_strings(list_of_strings):
    return [item for item in list_of_strings if item != ""]


def punctuation_parse(words):
    ret = []
    for word in words:
        parsed_word = word
        split_at_beginning = False
        split_at_end = False

        if len(word) < 2 or word in NODE_DISTINGUISHERS: # one-length words not only are definitely not proper nouns, they also break [-2] checks:
            ret.append(word)
            continue # so just add it and skip to the next word

        for interruptor in SENTENCE_INTERRUPTORS:
            try:
                if parsed_word[0] == interruptor:
                    parsed_word = parsed_word[1:]
                    split_at_beginning = True
                if parsed_word[-2] == interruptor:
                    parsed_word = parsed_word [:-2] # catches things like Here's how he's "like Biden":
                    split_at_end = True
                elif parsed_word[-1] == interruptor:
                    parsed_word = parsed_word[:-1]
                    split_at_end = True
            except IndexError:
                pass

        for ellipse in ELLIPSES:
            try:
                if parsed_word[-len(ellipse):] == ellipse:
                    parsed_word = parsed_word[-len(ellipse):]
                    split_at_end = True
            except IndexError: # if the word isnt long enough to fit an ellipse
                pass # its not the end of the world

        for punctuation_mark in PUNCTUATION: # only have to check the end of the word for punctuation
            try:
                if parsed_word[-1] == punctuation_mark and len(word) > 2: # a single letter followed by punctuation is usually an initial, not a sentence split
                    parsed_word = parsed_word[:-1]
                    split_at_end = True
                elif parsed_word[-2] == punctuation_mark: # catches things like 'Dreamers,' = > ["Dreamers"] and not ["Dreamers,"]
                    parsed_word = parsed_word[:-2]
                    split_at_end = True
            except IndexError: # if the word is under two characters long
                pass # were done here

        for single_quote in SINGLE_QUOTES: # we have to parse these seperately because of possessives
            try:
                if parsed_word[0] == single_quote:  # if it begins in a single quote, its probably the start of quoted text
                    parsed_word = parsed_word[1:]
                    split_at_beginning = True
                if parsed_word[-2:] == (single_quote + "s"):  # if the word ends in 's, it's probably a possessive
                    parsed_word = parsed_word[:-2] # add it back to that list with the possessive removed
                    split_at_end = True # so that "Trump's Ford" gets parsed as ["Trump, Ford"] and not ["Trump Ford"]
                elif parsed_word[-1] == single_quote:  # if it just ends in a single quote, it might be a possessive or the end of quoted text
                    parsed_word = parsed_word[:-1]  # so just remove the quote and see how it parses without it
                    split_at_end = True # either of those would end a thought chunk, though
            except IndexError: # if the word isnt long enough to fit some single quotes
                pass # its not the end of the world

        if split_at_beginning:
            ret.append(PUNCTUATION_REPLACEMENT)
        ret.append(parsed_word)
        if split_at_end:
            ret.append(PUNCTUATION_REPLACEMENT)

    return ret


def too_many_capitalized_words(words):
    total_actual_words = 0  # count all the words that arent PUNCTUATION_REPLACEMENT
    uppercase_words = 0  # |
    for word in words:  # for all the v real words
        if word != PUNCTUATION_REPLACEMENT:
            if ord(word[0]) < UPPERCASE_ASCII_VALUES_UPPER_BOUND:  # if the first letters' ascii value is in the capital range
                uppercase_words += 1
            total_actual_words += 1
    return (uppercase_words / total_actual_words) >= UPPERCASE_WORD_GARBAGE_THRESHHOLD


def proper_noun_final_pass(list_of_proper_nouns):
    for noun in list_of_proper_nouns:
        noun_is_safe = False # if the noun is replaced by a Problem Phrase replacement, we know it wont end with a joiner; this tracks that
        for problem_phrase in [*PROBLEM_PHRASES]: # PROBLEM_WORDS is a dictionary of (what nltk usually picks up, what the proper noun actually is) pairs
            if noun  == problem_phrase:  # if we find one of those alone in the list of proper nouns,
                list_of_proper_nouns.remove(problem_phrase) # it was probably supposed to be the problem word
                list_of_proper_nouns.append(PROBLEM_PHRASES[noun])
                noun_is_safe = True # avoid KeyError below when the word is both a problem word and has a joiner

        for joiner in JOINERS:
            if noun_is_safe:
                break

            words = noun.split(' ')
            if words[-1] == joiner:
                list_of_proper_nouns.remove(noun)
                list_of_proper_nouns.append(' '.join(words[:-1]))

    return list_of_proper_nouns


def extract_proper_nouns_from_text(text):
    ret = []
    consecutive_proper_nouns = [] # holds consecutive proper nouns, since theyre usually actually one big proper noun
    last_word_was_proper_noun = False

    words = text_preprocess(text)

    if too_many_capitalized_words(words): # if too many of the words in the text are capitalized
        return [] # the proper noun extractor wont get anything useful out of it

    for word, tag in nltk.pos_tag(words): # split the text using NLTK classification, then iterate over each word
        this_word_is_proper_noun = (tag == "NNP" and word != PUNCTUATION_REPLACEMENT and word not in FAKE_PROPER_NOUNS)

        if last_word_was_proper_noun and not this_word_is_proper_noun: # if this word ends a sentence or a chunk of proper nouns
            if word in JOINERS: # but could be used to connect two of them (i.e. Ministry 'of' State)
                consecutive_proper_nouns.append(word)
            else: # otherwise, we just ended a chunk of proper nouns
                if consecutive_proper_nouns[-1] in JOINERS: # 'informed Theresa May of his intentions" => "Theresa May" and not "Theresa May of"
                    consecutive_proper_nouns = consecutive_proper_nouns[:-1]

                if len(consecutive_proper_nouns) > 6: # no reasonable proper nouns are this long
                    continue

                proper_noun = ' '.join(consecutive_proper_nouns)
                lower_proper_noun = proper_noun.lower() # compare lowercases, so New York and New york arent taken as separates

                proper_noun_is_new = True
                for older_proper_noun in ret:
                    lower_older_proper_noun = older_proper_noun.lower()
                    if lower_proper_noun in lower_older_proper_noun: # if this proper noun is, or is an abbreviation of, a previously identified proper noun
                        proper_noun_is_new = False # don't add this one too
                        break # no point seeing if we can add it, now that we know we wont
                    elif lower_older_proper_noun in lower_proper_noun: # if an *older proper noun* is an abbreviation of this one,
                        ret.remove(older_proper_noun) # we dont need that old one anymore
                if proper_noun_is_new:
                    ret.append(proper_noun)

                consecutive_proper_nouns = [] # dont concatenate all the nouns in the article please
                last_word_was_proper_noun = False
        elif this_word_is_proper_noun:
            if word.isupper() and len(word) > 2: # temporary fix (hahaa) to avoid fucking up too many acronyms
                word = word.lower().capitalize() # EUROPE -> Europe

            if word in PUNCTUATION:
                continue # punctuation is not nouns, but nltk seems to disagree

            if word in PROBLEM_WORDS: # fixes formatting errors on some common words i.e. U.N. => U.n
                word = PROBLEM_WORDS[word]

            consecutive_proper_nouns.append(word)
            last_word_was_proper_noun = True

    if consecutive_proper_nouns: # if we ended on a proper noun
        ret.append(' '.join(consecutive_proper_nouns)) # make sure to add that too

    return proper_noun_final_pass(ret) # do a final filter, then return the list