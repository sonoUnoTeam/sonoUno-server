#! /usr/bin/env python3
"""This script generates a new bcrypt password salt."""

import bcrypt

print(str(bcrypt.gensalt())[2:-1])
