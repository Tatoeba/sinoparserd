#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This is a script for generating mandarin.xml from CC-CEDICT.

It downloads the most recent version from https://cc-cedict.org and transforms
it into the XML format expected by sinoparserd.
"""

from collections import Counter
import gzip
try:
    from urllib.request import urlopen
except ImportError:  # Python 2
    from urllib2 import urlopen

import mandarin_preference


def gunzip_urlopen(url):
    response = urlopen(url)
    try:
        import StringIO
        gzipped_data = response.read()
        return gzip.GzipFile(fileobj=StringIO.StringIO(gzipped_data))
    except ImportError:  # Python 3
        return gzip.open(response, 'rt')


def parse_entry(line):
    """Turns a dictionary entry into a triple (traditional, simplified, pinyin)

    Each entry has the form
    traditional simplified [pin1 yin1] /meaning 1/meaning 2/
    but we only care about the first three parts.
    """
    trad, rest = line.split(' ', 1)
    simp, rest = rest.split(' ', 1)
    assert rest[0] == '[', "Can't find [pinyin] in line:\n" + line
    pinyin, rest = rest[1:].split(']', 1)
    pinyin = pinyin.replace('u:', 'v')  # two different representations of ü
    return (trad, simp, pinyin)


def add_spaces_to_syllable(syllable):
    """Add space in front of capital letters and after commas."""
    if syllable[0].isupper():
        syllable = ' ' + syllable
    if syllable[-1] == ',':
        syllable += ' '
    return syllable


def join_pinyin(pinyin):
    """Joins pinyin syllables into words.

    Entries in CC-CEDICT usually represent words whose syllables should not
    be separated by spaces in pinyin. Exceptions include multi-part names,
    like 中國人民大學 [Zhong1 guo2 Ren2 min2 Da4 xue2] where capital letters
    indicate the parts. There are other exceptions, e.g. complete sentences
    like 黃鼠狼給雞拜年，沒安好心 but it's hard to handle those automatically.
    """
    syllables = pinyin.split(' ')
    pinyin = ''.join(map(add_spaces_to_syllable, syllables))
    return pinyin.strip()  # removing extraneous spaces introduced above


def remove_prefixes(entries):
    """This function removes adverbial prefixes (like negation) from words
    so the combination isn't treated as a single unit.

    Relevant standard:
    《汉语拼音正词法基本规则》(GB/T 16159-2012) 6.1.6：“副词与后面的词语，分写”
    """
    prefixes = [
        ('不', '不', 'bu4 '),
        ('很', '很', 'hen3 '),
        ('更', '更', 'geng4 '),
        ('最', '最', 'zui4 '),
        ('非常', '非常', 'fei1 chang2 '),
    ]
    return {
        entry
        for entry in entries
        if not any(
            all(e.startswith(p) for e, p in zip(entry, prefix))  # has prefix
            and tuple(e[len(p):] for e, p in zip(entry, prefix)) in entries  # remainder is also an entry
            for prefix in prefixes
        )
    }


def sorted_entries(entries, preference):
    """Apply an ordering where ambiguous entries are disambiguated according to
    the given preference ordering"""
    trad_count = Counter(trad for trad, simp, pinyin in entries)
    simp_count = Counter(simp for trad, simp, pinyin in entries)
    ambiguous = []
    unambiguous = []
    for entry in entries:
        trad, simp, pinyin = entry
        if trad_count[trad] > 1 or simp_count[simp] > 1:
            ambiguous.append(entry)
        else:
            unambiguous.append(entry)

    def sort_key(entry):
        try:
            return preference.index(entry)
        except ValueError:
            raise ValueError(
                "Missing preference for ambiguous entry:\n {} {} [{}]".format(*entry)
            )
    return sorted(ambiguous, key=sort_key) + sorted(unambiguous)


def print_xml():
    cedict_url = 'https://cc-cedict.org/editor/editor_export_cedict.php?c=gz'

    cedict_file = gunzip_urlopen(cedict_url)

    print('<root>')

    comments = [
        'This file was generated from CC-CEDICT.',
        'The original copyright notice follows below.',
        '',
    ]
    entries = set()
    for line in cedict_file:
        if line[0] == '#':  # comment line
            assert comments is not None, 'Unexpected comment:\n' + line
            comments.append(line[1:].strip())
        else:
            if comments is not None:
                print('<!--\n' + '\n'.join(comments) + '\n-->')
                comments = None
            entries.add(parse_entry(line))

    entries = remove_prefixes(entries)
    entries = sorted_entries(entries, mandarin_preference.preference)
    for i, (trad, simp, pinyin) in enumerate(entries):
        assert '"' not in trad+simp+pinyin
        print('<item id="{}" simp="{}" trad="{}" pinyin="{}" />'.format(
            i+1, simp, trad, join_pinyin(pinyin)
        ))

    print('</root>')


if __name__ == '__main__':
    print_xml()
