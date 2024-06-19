# Developed by smr@dt3.org; please let them know if this already exists somewhere.

def breadth_first_combinations(sequence, r):
    """ Variant of itertools.combinations() that is breadth-first rather than depth-first. """
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
