#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from mandarin import parse_entry, join_pinyin, sorted_entries


class TestParseEntry(unittest.TestCase):
    def test_simple_entry(self):
        self.assertEqual(
            ('往初', '往初', 'wang3 chu1'),
            parse_entry(
                '往初 往初 [wang3 chu1] /(literary) former times/in olden days/'
            )
        )

    def test_entry_with_reference(self):
        self.assertEqual(
            ('張勳復辟', '张勋复辟', 'Zhang1 Xun1 Fu4 bi4'),
            parse_entry(
                '張勳復辟 张勋复辟 [Zhang1 Xun1 Fu4 bi4] /Manchu Restoration of 1917, an attempt by general 張勳|张勋[Zhanɡ1 Xun1] to reinstate the monarchy in China by restoring the abdicated emperor Puyi 溥儀|溥仪[Pu3 yi2] to the throne/'
            )
        )

    def test_umlaut(self):
        self.assertEqual(
            ('鑢', '鑢', 'Lv4'),
            parse_entry(
                '鑢 鑢 [Lu:4] /surname Lü/'
            )
        )


class TestJoinPinyin(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(
            'qin2wu4yuan2',
            join_pinyin(
                'qin2 wu4 yuan2'
            )
        )

    def test_name(self):
        self.assertEqual(
            'Sheng4 He4le4na2 Dao3',
            join_pinyin(
                'Sheng4 He4 le4 na2 Dao3'
            )
        )

    def test_couplet(self):
        # running the words together like this is not nice,

        # but at least the comma is spaced properly
        self.assertEqual(
            'you3jie4you3huan2, zai4jie4bu4nan2',
            join_pinyin(
                'you3 jie4 you3 huan2 , zai4 jie4 bu4 nan2'
            )
        )


class TestSortedEntries(unittest.TestCase):
    preference = [
        ('得', '得', 'de5'),
        ('得', '得', 'dei3'),
    ]

    def test_happy_path(self):
        self.assertEqual(
            self.preference + [('呢', '呢', 'ne5')],
            sorted_entries(
                self.preference + [('呢', '呢', 'ne5')],
                self.preference
            )
        )

    def test_missing_preference(self):
        with self.assertRaisesRegexp(ValueError, '呢'):
            sorted_entries(
                self.preference + [
                    ('呢', '呢', 'ne5'),
                    ('呢', '呢', 'ni2'),
                ],
                self.preference
            )


if __name__ == '__main__':
    unittest.main()
