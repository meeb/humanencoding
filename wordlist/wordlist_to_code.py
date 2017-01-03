#!/usr/bin/env python3

'''
    This script parses a wordlist in a file (one word per line split by
    newlines) into a code structure. By default this is a Python tuple. The
    generated data structure is written to stdout. This tool is designed to be
    readable, not fast.

    Example:
        $ python3 wordlist_to_code.py -w wordlist_v1 -l python > words.py
'''


import os
import sys
import argparse
from textwrap import wrap


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
    words = []
    with open(wordlist_file, 'rt') as wordlist:
        for word in wordlist:
            word = word.strip()
            if word and not word.startswith('#'):
                words.append(params['wrap_item'] + word + params['wrap_item'])
    data_start = params['name'] + ' ' + params['equals']
    if params['equals']:
        data_start += ' '
    data_start += params['start_structure']
    spaces = ' ' * len(data_start)
    data_line_len = params['line_length'] - len(data_start)
    sep = params['separate_item'] + ' '
    data_body = sep.join([w for w in words])
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
