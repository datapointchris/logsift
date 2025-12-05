"""Test file with refurb violations - pathlib suggestions."""

# FURB109: Use Path.read_text() instead of open().read()
with open('file.txt') as f:
    content = f.read()

# FURB103: Use Path.write_text() instead of open().write()
with open('output.txt', 'w') as f:
    f.write('hello')
