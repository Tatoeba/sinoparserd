#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from __init__ import shared_substring, align, DiffWithContext


class TestSharedSubstring(unittest.TestCase):
    def test_equal(self):
        string = 'Abc {test} def.'
        self.assertEqual(
            string,
            shared_substring(string, string, string)
        )

    def test_different(self):
        strings = (
            'Abc {test} def.',
            'Abc {text} def.',
            'Abc {fork} def.',
        )
        self.assertEqual(
            'Abc {} def.',
            shared_substring(*strings)
        )


class TestAlign(unittest.TestCase):
    def test_equal(self):
        string = 'Abc {test} def.'
        self.assertEqual(
            [(string, string, string)],
            align(string, string, string)
        )

    def test_different(self):
        strings = (
            'Abc {test} def.',
            'Abc {text} def.',
            'Abc {fork} def.',
        )
        self.assertEqual(
            [
                3 * ('Abc {',),
                ('test', 'text', 'fork'),
                3 * ('} def.',),
            ],
            align(*strings)
        )


class TestDiffWithContext(unittest.TestCase):
    def test_with_context(self):
        dwc = DiffWithContext(
            1234,
            [
                3 * ('Abc {',),
                ('test', 'text', 'fork'),
                3 * ('} def.',),
            ],
            1
        )
        self.assertEqual(
            ('c {[test]}', 'c {[text]}', 'c {[fork]}'),
            dwc.with_context(3, 1, left_sep='[', right_sep=']')
        )


if __name__ == '__main__':
    unittest.main()
