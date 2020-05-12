#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This script uses sinoparserd to generate transcriptions for several sentences
read from standard input and outputs them in the same format as Tatoeba's
exported transcription files, in order to make it easy to compare them.
"""

from __future__ import print_function

import re
import xml.etree.ElementTree as ET

try:
    from urllib.request import quote, urlopen
except ImportError:  # Python 2
    from urllib2 import quote, urlopen


def utf8(text):
    if type(text) != str:
        return text.encode('utf-8')
    return text


def basic_pinyin_cleanup(text):
    # See tatoeba2/src/Lib/Autotranscription.php: _basic_pinyin_cleanup
    text = re.sub(r'\s+([!?:;.,])', r'\1', text)
    text = re.sub(r'"\s*([^"]+)\s*"', r'"\1"', text)
    text = text[0].upper() + text[1:]
    return text


def transcribe(text):
    response = urlopen('http://localhost:8080/all?str='+quote(text))
    xml = ET.fromstring(response.read())
    data = {child.tag: utf8(child.text) for child in xml}
    script = {
        'simplified_script': 'Hans',
        'traditional_script': 'Hant'
    }[data['script']]
    alternate_script = {'Hans': 'Hant', 'Hant': 'Hans'}[script]
    alternate_script_text = data['alternateScript']
    romanization = data['romanization']
    transcriptions = {
        alternate_script: alternate_script_text,
        'Latn': basic_pinyin_cleanup(romanization),
    }
    return transcriptions


def main(argv):
    from sys import stdin
    user = '' # automatic transcriptions are marked by an empty username
    for line in stdin.readlines():
        n, lang, text = line.rstrip('\n').split('\t', 2)
        transcriptions = transcribe(text)
        for script, transcription in sorted(transcriptions.items()):
            print(n, lang, script, user, transcription, sep='\t')


if __name__ == '__main__':
    import sys
    main(sys.argv)
