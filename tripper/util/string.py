from re import split


def sort_and_simplify(s):
    return ' '.join(sorted(split(' und |\s?,\s?', s)))
