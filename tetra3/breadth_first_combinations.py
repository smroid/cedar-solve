import unittest

# Variant of itertools.combinations() that is breadth-first rather than depth-first.
# See the unit test below for an example.
# Developed by smr@dt3.org; please let them know if this already exists somewhere.

def breadth_first_combinations(sequence, r):
    if r == 1:
        for item in sequence:
            yield (item,)
        return

    index = r - 1
    while index < len(sequence):
        right_most_elt = sequence[index]
        for prefix_combination in breadth_first_combinations(sequence[:index], r-1):
            yield prefix_combination + (right_most_elt,)
        index += 1


# Unit test.
def main():
    test_case = unittest.TestCase()
    test_case.assertEqual(
        list(breadth_first_combinations([1, 2, 3, 4, 5, 6], 3)),
        [(1, 2, 3),
         (1, 2, 4), (1, 3, 4), (2, 3, 4),
         (1, 2, 5), (1, 3, 5), (2, 3, 5), (1, 4, 5), (2, 4, 5), (3, 4, 5),
         (1, 2, 6), (1, 3, 6), (2, 3, 6), (1, 4, 6), (2, 4, 6), (3, 4, 6), (1, 5, 6), (2, 5, 6), (3, 5, 6), (4, 5, 6)])

if __name__ == '__main__':
    main()
