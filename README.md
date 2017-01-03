# humanencoding

`humanencoding` is a reference implementation in Python of the human encoding
format for binary data to human readable dictionary words. The full
specification is available here: [SPEC.md](SPEC.md). `humanencoding` allows
the conversion of arbitrary data into words easily read, pronounced and
memorised by people. It also supports checksums for data validation which is
useful if information is being transmitted out of bounds (such as spoken
words).

# Installation

Install from pip:

```bash
$ pip install humanencoding
```

That's it. The library has no dependancies. `humanencoding` supports both
Python2 and Python3. It also comes with a relatively extensive test suite. You
can invoke the tests by cloning this repository and running:

```bash
$ python setup.py test
```

# Usage

Basic usage:

```python
from humanencoding import encode, decode
test_data = b'test'
encoded_data = encode(test_data)
# prints: 'handset interview'
print(encoded_data)
decoded_data = decode(encoded_data)
# prints: b'test'
print(decoded_data)
```

Using CRC32 checksums:

```python
from humanencoding import encode, decode, ChecksumError
test_data = b'test'
encoded_data = encode(test_data, checksum=True, return_string=False)
# prints: ['handset', 'interview', 'check', 'laughingly', 'sterility']
print(encoded_data)
decoded_data = decode(encoded_data)
# prints: b'test'
print(decoded_data)

# modify the last word in the encoded_data (sterility) to something invalid
# to break the checksum, attempt to decode it again and catch the error
encoded_data[-1] = 'broken'
# prints: ['handset', 'interview', 'check', 'laughingly', 'broken']
print(encoded_data)
try:
    decode(encoded_data)
except ChecksumError as e:
    # prints 'Invalid CRC32 checksum'
    print(e)
```

# API

There are only two main methods to use in this library. All errors will raise
one of `humanencoding.HumanEncodingError` or `humanencoding.ChecksumError`
exceptions. The main methods are listed below with their defaults:

`humanencoding.encode(binary_data, version=1, checksum=False, return_string=True, max_bytes=10240)`

**Arguments:**

 * `binary_data` the binary input data to encode
 * `version` the bundled wordlist version to use
 * `checksum` append a CRC32 checksum
 * `return_string` if set to `True` return a string, if set to `False` return
    a list
 * `max_bytes` maximum allowed number of bytes to encode

**Returns:**

 * A string of space separated dictionary words if `return_string` is `True`,
   otherwise a list of dictionary words

`humanencoding.decode(words, version=1, max_words=1024)`

**Arguments:**

 * `words` a string of space separated dictionary words or a list of dictionary
   words
 * `version` the bundled wordlist version to use
 * `max_words` maximum allowed number of words to decode

**Returns:**

 * Binary data

# Licensing

The `humanencoding` specification itself is open for anyone to implement. The
supplied v1 wordlist and this Python reference implementation are licensed
under the LGPLv3.

# Contributing

All properly formatted and sensible pull requests, issues and comments are
welcome.
