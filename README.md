Time lock a file on your system clock speed
===========================================

Original code and theory is not mine, but I am modifying to fit my needs.

Ideal additions:

- Encrypt straight string, not file.
- Allow unlock date as argument, not calculated via seconds.
- Allow minutes, hours, etc.
- Save decoded output to filesystem, not just stdout. Puzzle progress is saved, but not output.
- Allow progress files to be placed and named in specific folders.
- Use argparse

