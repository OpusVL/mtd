"""Useful generic tools for processing dictionaries"""

def map_keys(func, dictionary):
    return {func(key): value for (key, value) in dictionary.items()}


def restrict_with_fill_values(dictionary, wanted_keys, fill_value):
    """Return dictionary with only wanted_keys, missing keys set to fill_value.
    """
    return {
        key: dictionary.get(key, fill_value)
        for key in wanted_keys
    }
