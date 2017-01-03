# Human encoding of binary data specification

This specifications describes the conversion of binary data to human readable
words and the inverse conversion of human readable words into binary data. This
specification provides a method similar to base64 or hex encoding for binary
data. The resulting human readable encoded data sacrifices encoded data size
for readability and usability by humans.

Below is a comparison between various binary encoding menthods and their
resulting output size. Note the average word length used in the current word
list is 7.716 characters.

| method         | input | output               | chars per byte | increase |
|----------------|-------|----------------------|----------------|----------|
| hex            | test  | 74657374             | 2              | 150%     |
| base64         | test  | dGVzdA==             | 1.333          | 133%     |
| base32         | test  | ORSXG5A=             | 1.625          | 162.5%   |
| human encoding | test  | interstate instilled | 3.858          | 385.8%   |

# Goals

The aim is to allow reasonable sized binary data, such as cryptographic
information, to be easily stored, memorised and transferred by humans rather
than computers. There are a number of alternatives available, such as RFC 1751,
however none of these support arbitrary lengths or use more complicated text
generation. There are other per-project Implementations of similar encoding
methods using dictionary lookup tables, however they are not standardised.

# Implementation

This Implementation of human encoding uses, at its core, a 65536 word lookup
table of words from the standard American English dictionary. One word is used
for each two bytes of input data. When inverting words to bytes the position
of the word in the dictionary is used as a two byte integer and the output is
concatenated. There are a few additional features which are detailed in the
technical specification below.

American English is used as it is the most widely used version of English
globally.

# Wordlist

This is the obvious drawback with human encoded binary data. To generate human
readable and memorisable output a large dictionary must be used. A reasonable
amount of time has gone into processing the supplied version 1 word list to
ensure that it:

 * contains the easiest to say and shortest words
 * contains no commonly used brand terms
 * contains no abuse terms
 * all words are between 3 and 12 characters in length

As the order and contents of the word list is critical to the operation of
human encoding (as it is effectively a public 'pad' in cryptographic terms) it
is versioned. If any changes to the blacklist or word list generation algorithm
are required a new version of the word list must be used. Libraries
implementing human encoding should ship all versions of the word list to avoid
breaking downstream projects using human encoding libraries.

Every word in the word list must be unique.

# Technical specification

The output of human encoding is dictionary words in lower case characters with
no punctuation and separated by spaces (or as a list / table / array of words
in the implementing language). There are only two reserved words:

 * `null`
 * `check`

If the third to last word in a human encoded string is the word `check` then
the second to last word and the last word, when converted into 4 bytes, are
a CRC32 checksum used to validate the rest of the message.

If the last word (or forth to last word if a checksum is being used) is `null`
then the input data was of an odd length and a null byte was appended as
padding. This should be truncated before returning the binary data.

Binary data to human encoding can be performed with the following steps:

 1. if the input binary data is an odd length, append a null byte (\0)
 2. iterate over the data two bytes at a time
 3. convert each two byte chunk into a little endian unsigned short integer
    from 0 to 65535
 4. fetch the corresponding word from the word list of 65536 words
 5. concatenate the words together
 6. if a null byte was appended in step 1, append the reserved word `null` to
    the output
 7. if checksums are being used, append the reserved word `check`, calculate
    the CRC32 checksum of the input binary data, convert it to two dictionary
    words as detailed in step 4 and append it to the output

In very verbose pseudocode, the encoding process is:

```
# test input binary data
original_input = 'some data'
input_length = length(original_input)

# the wordlist, this must be exactly 65536 words long
wordlist = ['table', 'of', 'words', '65536', 'entries', 'long', ...]

# check if padding is required
if (input_length mod 2 == 0) {
  # input length is odd
  padded_input = original_input + '\0'
  input_length = input_length + 1
  is_padded = true
}
else {
  padded_input = original_input
  is_padded = false
}

# loop through the input data two bytes at a time, pack the integers into a
# little endian unsigned short integer and get the corresponding word from the
# wordlist
words = []
while (i < input_length) {
  first_byte = input[i]
  second_byte = input[i + 1]
  first_int = ord(first_byte)
  second_int = ord(second_byte)
  wordlist_position = (first_int << 8) + second_int
  word = wordlist[wordlist_position]
  words.append(word)
  i = i + 2
}

# if padding was applied, append the reserved word 'null'
if (is_padded) {
  words.append('null')
}

# optional, generate a 32bit CRC32 checksum as two human encoded words
checksum = generate_crc32(original_input)
wordlist_position_1 = (ord(checksum[0]) << 8) + ord(checksum[1])
wordlist_position_2 = (ord(checksum[2]) << 8) + ord(checksum[3])
words.append('check')
words.append(wordlist[wordlist_position_1])
words.append(wordlist[wordlist_position_2])

# return the words separated by a space or as a list / tuple / array
return ' '.join(words)
```

Human encoded words to binary data is the above encoding process in reverse:

 1. if the number of words in the human encoded string is larger than 4 and the
    third to last word is `check`, remove the second to last word and the last
    word and store them for later, these are a CRC32 32bit checksum for the
    rest of the message - discard the third to last word
 2. if the last word is `null` then the input data was padded with a null byte,
    make note of this for data - discard the last word
 3. iterate over each word in the input data and get its position in the word
    list
 4. unpack each word position integer into two bytes
 5. concatenate all the bytes together
 6. if a null byte was appended as padding (detected in step 2), remove the
    last byte
 7. if a checksum was appended (dected in step 1), decode the two stored words
    from step 1 using the process detailed in step 3 into a 32bit CRC32
    checksum and compare it with the the CRC32 of the output data generated in
    step 5

In very verbose pseudocode, the decoding process is:

```
# encoded test data
encoded_input = ['some', 'dictionary', 'words', 'here']
input_num_words = size(encoded_input)

# the unique word list, this must be exactly 65536 words long and the same
# word list must be used to decode as was used to encode the data
wordlist = ['table', 'of', 'words', '65536', 'entries', 'long', ...]

# check for checksums
if (input_num_words > 4 && encoded_input[-3] == 'check') {
  checksum_word1 = encoded_input[-2]
  checksum_word2 = encoded_input[-1]
  # truncate the last 3 words
  encoded_input = encoded_input[:-3]
  has_checksum = true
}
else {
  has_checksum = false
}

# check for null padding
if (encoded_input[-1] == 'null') {
  # truncate the last word
  encoded_input = encoded_input[:-1]
  has_padding = true
}
else {
  has_padding = false
}

# loop over the words, get their position in the word list and convert the
# position from a short into two bytes
output_data = ''
for (word in encoded_input) {
  word_position = wordlist.index(word)
  first_byte = (word_position >> 8) mod 256
  second_byte = word_position mod 256
  output_data = output_data + first_byte + second_byte
}

# check for padding
if (has_padding) {
  # truncate the last byte
  output_data = output_data[:-1]
}

# check for checksums
if (has_checksum) {
  validate_checksum = ''
  word1_position = wordlist.index(checksum_word1)
  first_byte1 = (word1_position >> 8) mod 256
  second_byte1 = word1_position mod 256
  validate_checksum = validate_checksum + first_byte1 + second_byte1
  word2_position = wordlist.index(checksum_word2)
  first_byte2 = (word2_position >> 8) mod 256
  second_byte2 = word2_position mod 256
  validate_checksum = validate_checksum + first_byte2 + second_byte2
  if (validate_checksum != generate_crc32(output_data)) {
    error('invalid CRC32 checksum!')
  }
}

# return the binary output data
return output_data
```
