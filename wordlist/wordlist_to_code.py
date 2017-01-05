#!/usr/bin/env python3

'''
    This script iterates over the words in the Carnegie Mellon pronounciation
    corpus from the NLTK toolkit. Words are tested on their own and with a
    range of common suffixes appended against the input word list. The aim
    is to generate over 65536 unique words that are common and pronouncable.

    Once generated, each word is then given a score based on its character
    length and a rough estimation of the number of syllables. The words are
    sorted by their score, truncted to 65536 words in length, re-ordered
    alphabetically and then written to stdout in the selected language
    construct. By default this is a Python tuple.
    This script parses a wordlist in a file (one word per line split by
    newlines) into a code structure. By default this is a Python tuple. The
    generated data structure is written to stdout.

    This script requires the cmudict corpus to be downloaded for nltk.

    Example:
        $ python3 wordlist_to_code.py -w wordlist_v1 -l python > words.py
'''


import os
import sys
import argparse
import re
from textwrap import wrap
try:
    from nltk.corpus import cmudict
except ImportError:
    sys.stderr.write('Use nltk.download() to download the cmudict corpus\n')
    sys.exit(1)


LANGUAGES = {
    # generates a Python tuple
    'python': {
        'name': 'words',
        'equals': '=',
        'start_structure': '(',
        'end_structure': ')',
        'wrap_item': '\'',
        'separate_item': ',',
        'line_length': 79,
    },
    # generates an importable lua table
    'lua': {
        'name': 'return',
        'equals': '',
        'start_structure': '{',
        'end_structure': '}',
        'wrap_item': '\'',
        'separate_item': ',',
        'line_length': 80,
    }
}


PENALTY_PREFIXES = ('q', 'x', 'z', 'rh', 'ae', 'wr')
PREFIX_PENALTY_AMOUNT = 1.2
VOWELS = ('a', 'e', 'i', 'o', 'u', 'y')
SUFFIXES = ('', 'acy', 'al', 'ance', 'dom', 'er', 'ism', 'ist', 'ity', 'ment',
            'ness', 'ship', 'sion', 'ate', 'en', 'ify', 'fy', 'ize', 'ise',
            'able', 'ible', 'al', 'esque', 'ful', 'ic', 'ical', 'ious', 'ish',
            'ive', 'less', 'y', 'ly', 'ed', 'ing', 'est')
IGNORE_WORDS = ('aak', 'aal', 'aam', 'acs', 'adv', 'aes', 'aff', 'ajr', 'aks',
                'aqa', 'aua', 'bge', 'ccy', 'cee', 'dba', 'dyb', 'dyd', 'dzo',
                'eef', 'eqp', 'eqq', 'exx', 'eyr', 'ezh', 'faa', 'ibn', 'idd',
                'igg', 'iid', 'itt', 'iwi', 'kyr', 'nyc', 'oxo', 'pde', 'pfu',
                'qty', 'tyg', 'vse', 'ygo')
BAD_WORDS = ('anal', 'anus', 'arse', 'ass', 'balls', 'bastard', 'bitch',
             'bloody', 'bollock', 'boner', 'boob', 'bugger', 'bum', 'butt',
             'clitoris', 'cock', 'coon', 'crap', 'cunt', 'damn', 'dick',
             'dildo', 'dyke', 'fag', 'feck', 'fellate', 'fellatio', 'felching',
             'fuck', 'flange', 'goddamn', 'hell', 'homo', 'jerk', 'jizz',
             'knob', 'labia', 'muff', 'nigger', 'nigga', 'penis', 'piss',
             'poop', 'prick', 'pube', 'pussy', 'queer', 'scrotum', 'sex',
             'shit', 'slut', 'smeg', 'spunk', 'tit', 'tosser', 'turd', 'twat',
             'vagina', 'wank', 'whore', 'wtf')
EXTRA_SUFFIX = 's'
NUM_WORDS = 65536
MAX_FRAGMENT_REPITITIONS = 3


_cmudict = cmudict.dict()
_repititions = re.compile(r'(.+?)\1+')


def number_of_syllables(word):
    count = 0
    if len(word) == 0:
        return 0
    if word[0] in VOWELS:
        count += 1
    for i in range(1, len(word)):
        if word[i] in VOWELS and word[i - 1] not in VOWELS:
            count += 1
    if word.endswith('e'):
        count -= 1
    if word.endswith('le'):
        count += 1
    if count == 0:
        count += 1
    return count


def number_of_repetitions(word):
    for match in _repititions.finditer(word):
        yield (match.group(1), len(match.group(0)) / len(match.group(1)))


def word_score(word):
    syllables = number_of_syllables(word)
    if not syllables:
        return
    for (fragment, repeated) in number_of_repetitions(word):
        if repeated >= MAX_FRAGMENT_REPITITIONS:
            return
    score = syllables * len(word)
    for prefix in PENALTY_PREFIXES:
        if word[:len(prefix)] == prefix:
            score *= PREFIX_PENALTY_AMOUNT
            break
    return score


if __name__ == '__main__':
    language_choices = [k.lower() for k in LANGUAGES.keys()]
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--language', type=str, choices=language_choices,
                        default='python',
                        help='Select the output language')
    parser.add_argument('-w', '--wordlist', type=str, default='wordlist.txt',
                        help='Input wordlist file')
    args = parser.parse_args()
    language = args.language
    wordlist_file = args.wordlist
    params = LANGUAGES.get(language, None)
    if not params:
        raise Exception('Invalid language: {}'.format(language))
    if not os.path.isfile(wordlist_file):
        raise Exception('Not a file: {}'.format(wordlist_file))
    wordlist = set()
    with open(wordlist_file, 'rt') as wordlist_handle:
        for word in wordlist_handle:
            word = word.strip()
            if word and not word.startswith('#'):
                    wordlist.add(word)
    words = set()
    for cmuword in _cmudict:
        if cmuword in BAD_WORDS:
            continue
        if cmuword.endswith(EXTRA_SUFFIX):
            wordnosuffix = cmuword[:-len(EXTRA_SUFFIX)]
            if wordnosuffix in IGNORE_WORDS or wordnosuffix in BAD_WORDS:
                continue
        for suffix in SUFFIXES:
            wordsuffix = cmuword + suffix
            if wordsuffix in wordlist and wordsuffix not in IGNORE_WORDS:
                words.add(wordsuffix)
            wordsuffixs = wordsuffix + EXTRA_SUFFIX
            if wordsuffixs in wordlist and wordsuffixs not in IGNORE_WORDS:
                ignored = False
                if wordsuffixs.endswith(EXTRA_SUFFIX):
                    wordnosuffix = wordsuffixs[:-len(EXTRA_SUFFIX)]
                    if wordnosuffix in IGNORE_WORDS:
                        ignored = True
                if not ignored:
                    words.add(wordsuffixs)
    if len(words) < NUM_WORDS:
        err = 'Not enough words, supply a larger wordlist. Found: {}, need: {}'
        raise Exception(err.format(len(words), NUM_WORDS))
    words_with_scores = []
    for word in words:
        score = word_score(word)
        if not score:
            continue
        words_with_scores.append((word, score))
    words_with_order = sorted(words_with_scores, key=lambda x: x[1])
    words_truncated = words_with_order[:NUM_WORDS]
    words_in_alpha = []
    for (word, score) in words_truncated:
        words_in_alpha.append(word)
    words_in_alpha = sorted(words_in_alpha)
    words_format = []
    for word in words_in_alpha:
        words_format.append(params['wrap_item'] + word + params['wrap_item'])
    data_start = params['name'] + ' ' + params['equals']
    if params['equals']:
        data_start += ' '
    data_start += params['start_structure']
    spaces = ' ' * len(data_start)
    data_line_len = params['line_length'] - len(data_start)
    sep = params['separate_item'] + ' '
    data_body = sep.join([w for w in words_format])
    data_wrapped = wrap(data_body, width=data_line_len)
    first_line = data_wrapped.pop(0)
    last_line = data_wrapped.pop()
    sys.stdout.write(data_start)
    sys.stdout.write(first_line + '\n')
    for line in data_wrapped:
        sys.stdout.write(spaces + line + '\n')
    sys.stdout.write(spaces + last_line)
    if len(last_line) + len(spaces) >= params['line_length']:
        sys.stdout.write('\n' + spaces + params['end_structure'] + '\n')
    else:
        sys.stdout.write(params['end_structure'] + '\n')
