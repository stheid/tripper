from itertools import chain
from re import split
from typing import Set


def sort_and_simplify(s):
    return ' '.join(sorted(split(' und |\s?,\s?', s)))


def to_bag_of_words(iter_) -> Set[str]:
    return set(filter(lambda word: len(word) > 3, chain.from_iterable(map(lambda s: s.split(), iter_))))
