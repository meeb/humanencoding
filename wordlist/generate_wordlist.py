#!/usr/bin/env python3


'''
    This script parses the standard American English dictionary and attempts to
    naively extract the easiest to pronounce words which do not contain
    punctuation. There is a simple blacklist of reserved, abusive and commonly
    used brand words applied to the dictionary. The resulting wordlist is
    written to stdout. This tool is designed to be readable, not fast.

    Example:
        $ python3 generate_wordlist.py -w american-english-words.txt \
            -b blacklist.txt > wordlist.txt
'''


import os
import sys
import string
import re
import argparse


MIN_WORD_LEN = 2
MAX_WORD_LEN = 12
MAX_FRAGMENT_REPITITIONS = 3
PENALTY_PREFIXES = ('q', 'x', 'z', 'rh', 'ae', 'wr')
PENALTY_AMOUNT = 1.2
VOWELS = ('a', 'e', 'i', 'o', 'u', 'y')
NUM_WORDS = 65536


def is_digit(char):
    return char in string.digits


def is_lowercase_word(word):
    has_vowel = False
    for char in word:
        if char not in string.ascii_lowercase:
            return False
        if char in VOWELS:
            has_vowel = True
    return has_vowel


def read_file(filename):
    r = []
    with open(filename, 'rt') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            r.append(line)
    return r


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


_repititions = re.compile(r'(.+?)\1+')


def number_of_repetitions(word):
    for match in _repititions.finditer(word):
        yield (match.group(1), len(match.group(0))/len(match.group(1)))


_blacklist = None


def clean_word(word, blacklist_file):
    global _blacklist
    word = str(word).lower().strip()
    if not word:
        return
    elif not is_lowercase_word(word):
        return
    elif len(word) < MIN_WORD_LEN or len(word) > MAX_WORD_LEN:
        return
    elif word in _blacklist:
        return
    for (fragment, repeated) in number_of_repetitions(word):
        if repeated > MAX_FRAGMENT_REPITITIONS:
            return
    return word


def word_score(word):
    syllables = number_of_syllables(word)
    if not syllables:
        return
    score = syllables * len(word)
    for prefix in PENALTY_PREFIXES:
        if word[:len(prefix)] == prefix:
            score *= PENALTY_AMOUNT
            break
    return score


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--blacklist', type=str,
                        default='blacklist.txt',
                        help='Blacklist of words to ignore')
    parser.add_argument('-w', '--wordlist', type=str, default='wordlist.txt',
                        help='Input wordlist file')
    args = parser.parse_args()
    wordlist_file = args.wordlist
    blacklist_file = args.blacklist
    if not os.path.isfile(wordlist_file):
        err = 'Wordlist path is not a file: {}'
        raise Exception(err.format(wordlist_file))
    if not os.path.isfile(blacklist_file):
        err = 'Blacklist path is not a file: {}'
        raise Exception(err.format(blacklist_file))
    # process the words into a unique set
    uniquewords = set()
    _blacklist = set(read_file(blacklist_file))
    for word in read_file(wordlist_file):
        word = clean_word(word, blacklist_file)
        if not word:
            continue
        uniquewords.add(word)
    # give each word a score
    scoredwords = []
    for word in uniquewords:
        score = word_score(word)
        if not score:
            continue
        scoredwords.append((word, score))
    # order the words by their score
    orderedwords = sorted(scoredwords, key=lambda x: x[1])
    # truncate at 65536
    orderedwords = orderedwords[:NUM_WORDS]
    # re-order alphabetically and strip the scores
    words = sorted([word[0] for word in orderedwords])
    # write the words to stdout
    for word in words:
        sys.stdout.write(word + '\n')
