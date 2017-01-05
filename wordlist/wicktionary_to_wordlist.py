#!/usr/bin/env python3


'''
    This script parses an export from the English Wictionary XML export and
    extracts all the title words. The words are then naively processed to
    extract the easiest to pronounce words which do not contain punctuation.
    Abusive words and names are skipped. The resulting wordlist is written to
    stdout. This tool is designed to be readable, not fast.

    Example:
        $ python3 wicktionary_to_wordlist.py \
            -x enwiktionary-latest-pages-articles.xml \
            -b blacklist.txt > wordlist.txt

    You can get an up to date copy of enwiktionary-latest-pages-articles.xml
    in a bzip2 compressed archive from the Wikipedia foundation from here:
        https://dumps.wikimedia.org/enwiktionary/latest/

    Warning: the uncompressed XML file is 4-5 gigabytes in size!

    Warning: this script will take a long time!
'''


import os
import sys
import lxml.etree
import string
import re
import argparse


MIN_WORD_LEN = 3
MAX_WORD_LEN = 12
MIN_BADWORD_FRAGMENT_LEN = 4
VOWELS = ('a', 'e', 'i', 'o', 'u', 'y')


_wiki_markdown_regex = re.compile('{{([^}]+)}}')
_blacklist = []
_pending_word = None
_badwords = set()
_buffer = set()
_bad_wictionary_tags = set(['initialism of', 'acronym of', 'vulgar',
                            'alternative spelling of', 'alternative form of',
                            'offensive', 'ethnic slur', 'abbreviation of'])


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


def clean_word(word):
    global _blacklist
    word = str(word).strip()
    if not word:
        return
    elif not is_lowercase_word(word):
        return
    elif len(word) < MIN_WORD_LEN or len(word) > MAX_WORD_LEN:
        return
    elif word in _blacklist:
        return
    return word


def fast_iter_tree(context, func, *args, **kwargs):
    for event, elem in context:
        func(elem, *args, **kwargs)
        elem.clear()
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context


def buffer_badword(word):
    global _badwords
    word = clean_word(word)
    if not word:
        return
    _badwords.add(word)


def buffer_word(word):
    global _buffer
    word = clean_word(word)
    if not word:
        return
    _buffer.add(word)


def process_element(elem):
    global _pending_word, _badwords
    elem.tag = elem.tag.split('}', 1)[1]
    if elem.tag == 'title':
        _pending_word = elem.text.strip()
    elif elem.tag == 'text' and elem.text is not None:
        for part in elem.text.split('----'):
            if '==English==' not in part:
                continue
            descriptions = []
            for split_on in ('===Noun===', '===Adjective===', '===Verb===',
                             '===Pronoun===', '===Adverb==='):
                subpart = part.split(split_on)
                if len(subpart) > 1:
                    if '==' in subpart[1]:
                        subpart[1] = subpart[1][:subpart[1].find('==')]
                    descriptions.append(subpart[1])
            if not descriptions:
                continue
            tags = set()
            for description in descriptions:
                for tagstr in _wiki_markdown_regex.findall(description):
                    for t in tagstr.split('|'):
                        tags.add(t)
            if _bad_wictionary_tags & tags:
                buffer_badword(_pending_word)
            else:
                buffer_word(_pending_word)


def iter_goodwords():
    global _buffer, _badwords
    for word in _buffer:
        ok = True
        for badword in _badwords:
            if word is badword:
                ok = False
            elif len(badword) >= MIN_BADWORD_FRAGMENT_LEN and badword in word:
                ok = False
        if ok:
            yield word


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--blacklist', type=str,
                        default='blacklist.txt',
                        help='Blacklist of words to ignore')
    parser.add_argument('-x', '--wicktionaryxml', type=str,
                        default='wicktionary.txt',
                        help='Input Wictionary XML file')
    args = parser.parse_args()
    wicktionaryxml_file = args.wicktionaryxml
    blacklist_file = args.blacklist
    if not os.path.isfile(wicktionaryxml_file):
        err = 'Wictionary XML file path is not a file: {}'
        raise Exception(err.format(wicktionaryxml_file))
    if not os.path.isfile(blacklist_file):
        err = 'Blacklist file path is not a file: {}'
        raise Exception(err.format(blacklist_file))
    _blacklist = set(read_file(blacklist_file))
    context = lxml.etree.iterparse(wicktionaryxml_file, events=('end',))
    fast_iter_tree(context, process_element)
    for word in iter_goodwords():
        sys.stdout.write(word + '\n')
