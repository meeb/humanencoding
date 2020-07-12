'''

    humanencoding, binary data to dictionary words encoder and decoder
    Copyright (C) 2020 meeb@meeb.org

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''


import importlib
from binascii import crc32, hexlify
from struct import pack, unpack


DEFAULT_WORDLIST_VERSION = 1
CHECKSUM_WORD = 'check'
PADDING_WORD = 'null'
WORDLIST_SIZE = 65536
DEFAULT_MAX_ENCODING_BYTES = 10240
DEFAULT_MAX_DECODING_WORDS = 1024


try:
    text_type = unicode
except NameError:
    text_type = str


class HumanEncodingError(Exception):

    pass


class ChecksumError(HumanEncodingError):

    pass


wordlist = []


def lazily_load_wordlist(version=DEFAULT_WORDLIST_VERSION):
    global wordlist
    if wordlist:
        return
    version = int(version)
    wordlist_module_name = '.wordlist_v{}'.format(version)
    try:
        wordlist_module = importlib.import_module(wordlist_module_name,
                                                  package='humanencoding')
    except Exception as e:
        err = 'Invalid word list module: {} ({})'
        raise HumanEncodingError(err.format(wordlist_module_name, e))
    wordlist = getattr(wordlist_module, 'words', None)
    if not wordlist:
        raise HumanEncodingError('Word list module has no words attribute')
    elif len(wordlist) != WORDLIST_SIZE:
        err = 'Word list is in invalid size, found {} and expected {} words'
        raise HumanEncodingError(err.format(len(words), WORDLIST_SIZE))


def _bytes_to_int(b):
    return unpack('<H', b)[0]


def _chunk_to_word(chunk):
    global wordlist
    try:
        return wordlist[_bytes_to_int(chunk)]
    except IndexError:
        err = 'Invalid chunk, is the wordlist the correct size?'
        raise HumanEncodingError(err.format(word))


def _int_to_bytes(i):
    return pack('<H', i)


def _word_to_chunk(word):
    global wordlist
    try:
        return _int_to_bytes(wordlist.index(word))
    except ValueError:
        err = 'Invalid word: {} (word not in wordlist)'
        raise HumanEncodingError(err.format(word))


def _crc32(data):
    return crc32(data) & 0xffffffff


def encode(binary_data, version=DEFAULT_WORDLIST_VERSION, checksum=False,
           return_string=True, max_bytes=DEFAULT_MAX_ENCODING_BYTES):
    global wordlist
    if not isinstance(binary_data, (bytes, bytearray)):
        err = 'Data must be in bytes, convert it first. Got: {}'
        raise HumanEncodingError(err.format(type(binary_data)))
    if len(binary_data) > max_bytes:
        err = 'Data is too big, allowed byte size: {} bytes, got: {} bytes'
        raise HumanEncodingError(err.format(len(binary_data), max_bytes))
    lazily_load_wordlist(version=version)
    data_len = len(binary_data)
    padded = data_len % 2 == 1
    if padded:
        binary_data += b'\0'
        data_len += 1
    encoded_output = []
    for i in range(0, data_len, 2):
        chunk = binary_data[i: i + 2]
        encoded_output.append(_chunk_to_word(chunk))
    if padded:
        encoded_output.append(PADDING_WORD)
    if checksum:
        encoded_output.append(CHECKSUM_WORD)
        checksum_int = _crc32(binary_data[:-1] if padded else binary_data)
        checksum_bytes = pack('<I', checksum_int)
        encoded_output.append(_chunk_to_word(checksum_bytes[0:2]))
        encoded_output.append(_chunk_to_word(checksum_bytes[2:4]))
    return ' '.join(encoded_output) if return_string else encoded_output


def decode(words, version=DEFAULT_WORDLIST_VERSION,
           max_words=DEFAULT_MAX_DECODING_WORDS):
    global wordlist
    lazily_load_wordlist(version=version)
    if isinstance(words, (str, text_type)):
        words = words.split()
    if not isinstance(words, (list, tuple)):
        err = 'Words must be a string, list or tuple. Got: {}'
        raise HumanEncodingError(err.format(type(words)))
    if len(words) > max_words:
        err = 'Words are too big, allowed number of words: {}, got: {}'
        raise HumanEncodingError(err.format(len(words), max_words))
    words = [str(w).lower() for w in words]
    checksum_words = []
    if len(words) > 3 and words[-3] == CHECKSUM_WORD:
        checksum_words = words[-2:]
        words = words[:-3]
    if words[-1] == PADDING_WORD:
        is_padded = True
        words = words[:-1]
    else:
        is_padded = False
    output = b''
    for word in words:
        output += _word_to_chunk(word)
    if is_padded:
        output = output[:-1]
    if checksum_words:
        checksum_packed = _word_to_chunk(checksum_words[0])
        checksum_packed += _word_to_chunk(checksum_words[1])
        checksum_unpacked = unpack('<I', checksum_packed)[0]
        if checksum_unpacked != _crc32(output):
            raise HumanEncodingError('Invalid CRC32 checksum')
    return output
