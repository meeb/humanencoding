#!/usr/bin/env python3


WORD_LIST = 'american-english-words.txt'
BRAND_NAMES = 'brand-names.txt'
ABUSE_TERMS = 'abuse-terms.txt'


def read_file(filename):
    r = []
    with open(filename, 'rt') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            r.append(line)
    return r


def number_of_syllables(word):
    return 1


if __name__ == '__main__':
    print(number_of_syllables('test'))
