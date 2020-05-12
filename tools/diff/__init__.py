#!/usr/bin/python
# -*- coding: utf-8 -*-

"""This is a script for comparing different possible transcriptions of the same
sentences and for tallying up which differences are the most common.
"""

from __future__ import division, print_function

import collections
import difflib
import itertools


def print_utf8(text):
    if type(text) != str:
        print(text.encode('utf-8'))
    else:
        print(text)


def read_transcriptions(filename):
    """Read transcriptions from a file in the format used for Tatoeba exports:

    Sentence ID, language code, script code, user name and transcription, each
    separated by tabs.
    """
    with open(filename, 'rb') as f:
        transcriptions = {
            (id, lang, script): (user, transcription)
            for id, lang, script, user, transcription
            in (
                line.decode('utf-8').rstrip('\n').split('\t')
                for line in f.readlines()
            )
        }
    some_reviewed = any(user for user, transcription in transcriptions.values())
    if some_reviewed:
        # If there are reviewed transcriptions, the automatically generated ones
        # are uninteresting.
        return {
            k: transcription
            for k, (user, transcription) in transcriptions.items()
            if user
        }
    else:
        return {
            k: transcription
            for k, (user, transcription) in transcriptions.items()
        }


def shared_substring(*args):
    """Given an arbitrary number of strings, determine a long substring they all
    have in common.
    """
    # There can be multiple equally valid solutions,
    # e.g. shared_substring('ab', 'ba') could be either 'a' or 'b'.
    # To reduce the nondeterminism a bit, we sort the input, so the output does
    # not depend on the particular order of the input strings.
    args = sorted(args)
    shared = args[0]
    while True:
        pre_shared = shared
        for arg in args:
            shared = ''.join(
                shared[i:i+n]
                for i, j, n
                in difflib.SequenceMatcher(None, shared, arg).get_matching_blocks()
            )
        # In theory, `shared` should now be a subsequence of all arguments.
        # In practice, Python's SequenceMatcher applies some heuristics against
        # spurious matches, so we iterate until those are eliminated.
        if shared == pre_shared:
            return shared


def align(*args):
    """Split an arbitrary number of strings into a sequence of substrings that
    correspond to each other, thus highlighting differences between the strings.
    """
    shared = shared_substring(*args)
    matches = [
        difflib.SequenceMatcher(None, shared, arg).get_matching_blocks()
        for arg in args
    ]
    # Some matching blocks may be merged in some strings and not others, so we
    # determine all indices that start a match in any of the strings.
    starts = sorted(set(i for m in matches for i, j, n in m))
    # The corresponding block ends at the next start or the end of the string.
    ends = starts[1:]+[len(shared)]
    # Then we can split larger blocks into smaller ones.
    matches = [
        [
            (j + start - i, end - start)
            for i, j, n in m
            for start, end in zip(starts, ends)
            if start in range(i, i+n)
        ]
        for m in matches
    ]

    # The matching blocks also determine the position of the mismatches:
    # A mismatch occurs either at the beginning or directly after a match.
    starts = [
        [0] + [index for i, n in m for index in (i, i+n)]
        for m in matches
    ]
    # The corresponding block ends at the next start or the end of the string.
    ends = [
        s[1:]+[len(arg)]
        for s, arg in zip(starts, args)
    ]
    # Given start and end, we can split each string into a list of blocks.
    blocks = [
        [arg[start:end] for start, end in zip(s, e)]
        for s, e, arg in zip(starts, ends, args)
    ]
    # ...and group corresponding blocks together, removing empty ones.
    blocks = list(filter(any, zip(*blocks)))

    return blocks


class DiffWithContext(object):
    """A block that is part of an alignment of multiple strings, together with
    the context to the left and right."""

    def __init__(self, sentence_id, aligned, index):
        self.sentence_id = sentence_id
        self.block = aligned[index]
        # self.block is included in the zip below only to get the correct length
        self.left_context = [
            ''.join(string[1:]) for string in zip(self.block, *aligned[:index])
        ]
        self.right_context = [
            ''.join(string[1:]) for string in zip(self.block, *aligned[index+1:])
        ]

    def left_len(self):
        """The size of the context to the left."""
        return max(map(len, self.left_context))

    def right_len(self):
        """The size of the context to the right."""
        return max(map(len, self.right_context))

    def with_context(self, left_len, right_len, left_sep='', right_sep=''):
        """A representation of the block, with up to the given number of
        characters from the context to the left and right, with optional
        separators in between."""

        left = [
            string[max(0, len(string)-left_len):] for string in self.left_context
        ]
        right = [
            string[:right_len] for string in self.right_context
        ]
        return tuple(
            l+left_sep+b+right_sep+r for l, b, r in zip(left, self.block, right)
        )


def shared_context_size(blocks):
    """Given a collection of `DiffWithContext` objects, determine the size of
    the context to the left and right that they have in common."""

    blocks = list(blocks)
    def is_shared(left_len, right_len):
        return 1 == len({b.with_context(left_len, right_len) for b in blocks})

    left_len = 0
    right_len = 0
    left_len_max = max(b.left_len() for b in blocks)
    right_len_max = max(b.right_len() for b in blocks)
    while True:
        prev_left_len = left_len
        prev_right_len = right_len
        if left_len < left_len_max and is_shared(left_len + 1, right_len):
            left_len += 1
        if right_len < right_len_max and is_shared(left_len, right_len + 1):
            right_len += 1
        if left_len == prev_left_len and right_len == prev_right_len:
            return (left_len, right_len)


def largest_subgroup(blocks):
    """Given a collection of `DiffWithContext` objects, determine the largest
    subgroup whose shared context is not the same as that of all others."""

    blocks = list(blocks)
    if len(blocks) == 1:
        return blocks

    left_len, right_len = shared_context_size(blocks)
    candidates = []
    go_left = collections.Counter(
        b.with_context(left_len + 1, right_len) for b in blocks
    )
    go_right = collections.Counter(
        b.with_context(left_len, right_len + 1) for b in blocks
    )
    if len(go_left) != 1:
        candidates.append((left_len + 1, right_len, go_left.most_common(1)[0]))
    if len(go_right) != 1:
        candidates.append((left_len, right_len + 1, go_right.most_common(1)[0]))

    if not candidates:
        # that means, no amount of context differentiates between the blocks
        # just return a single one
        return blocks[:1]

    largest = max(candidates, key=lambda c: c[2][1])
    left_len, right_len, (context, count) = largest
    return [
        b for b in blocks if context == b.with_context(left_len, right_len)
    ]


def split_into_subgroups(blocks):
    """Given a collection of `DiffWithContext` objects, split it into smaller
    groups that each share a particular context."""

    blocks = list(blocks)
    groups = []
    shared_context = shared_context_size(blocks)
    while blocks and shared_context_size(blocks) == shared_context:
        group = largest_subgroup(blocks)
        blocks = [b for b in blocks if b not in group]
        groups.append(group)

    if blocks:
        groups.append(blocks)

    return groups


def show_hierarchically(blocks):
    """Given a collection of `DiffWithContext` objects, print a representation
    that makes the hierarchy of shared contexts visible."""
    if len(blocks) == 1:
        b = blocks[0]
        print_utf8(
            '<a href="https://tatoeba.org/eng/sentences/show/{}">#{}</a><br>'.format(
                b.sentence_id, b.sentence_id
            )
        )
        print_utf8('<br>\n'.join(
            b.with_context(
                b.left_len(),
                b.right_len(),
                left_sep='<b>',
                right_sep='</b>'
            )
        ))
    else:
        shared_context = blocks[0].with_context(
            *shared_context_size(blocks),
            left_sep='<b>',
            right_sep='</b>'
        )
        print_utf8('<details>')
        print_utf8(
            u'<summary>{} ({})</summary>'.format(
                ', '.join(shared_context),
               len(blocks)
            )
        )
        print_utf8('<ul>')
        for group in split_into_subgroups(blocks):
            print_utf8('<li>')
            show_hierarchically(group)
            print_utf8('</li>')
        print_utf8('</ul>')
        print_utf8('</details>')


def diff_pattern(block):
    """Represent a difference pattern as an easily interpretable string."""
    return ' '.join(chr(ord('a') + block.index(i)) for i in block)


def main(argv):
    filenames = argv[1:]
    transcriptions = [read_transcriptions(filename) for filename in filenames]

    print_utf8(
        '<h1>Differences between transcriptions in {}</h1>'.format(
            ', '.join('<i>'+filename+'</i>' for filename in filenames)
        )
    )

    shared_keys = set.intersection(*(
        set(trans.keys()) for trans in transcriptions
    ))
    diffs_with_context = collections.defaultdict(list)
    for key in sorted(shared_keys):
        normalized = [''.join(trans[key].split()) for trans in transcriptions]
        aligned = align(*normalized)
        for i, block in enumerate(aligned):
            if len(set(block)) != 1:
                diffs_with_context[block].append(
                    DiffWithContext(key[0], aligned, i)
                )


    total = sum(map(len, diffs_with_context.values()))
    diff_pattern_counts = collections.Counter()
    for block, diffs in diffs_with_context.items():
        diff_pattern_counts[diff_pattern(block)] += len(diffs)
    for pattern, count in diff_pattern_counts.most_common(len(diff_pattern_counts)):
        print_utf8('<details>')
        print_utf8(
            '<summary>Pattern <em>{}</em>: {} times ({:.1f}%)</summary>'.format(
                pattern, count, 100 * count/total
            )
        )
        print_utf8('<ul>')
        for block, diffs in sorted(diffs_with_context.items(), key=lambda x: -len(x[1])):
            if diff_pattern(block) == pattern:
                print_utf8('<li>')
                show_hierarchically(diffs)
                print_utf8('</li>')
        print_utf8('</ul>')
        print_utf8('</details>')


if __name__ == '__main__':
    import sys
    main(sys.argv)
