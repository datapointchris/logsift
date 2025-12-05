"""Test file with refurb violations - list comprehension suggestions."""

# FURB129: Use list comprehension instead of map
numbers = [1, 2, 3, 4, 5]
doubled = list(map(lambda x: x * 2, numbers))

# FURB148: Use list comprehension instead of filter
even_numbers = list(filter(lambda x: x % 2 == 0, numbers))
