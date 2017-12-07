import os
import random

BASE_DIR = os.path.dirname(__file__)

firstnames = open('{}/firstname.txt'.format(BASE_DIR), 'r').read().splitlines()
lastnames = open('{}/lastname.txt'.format(BASE_DIR), 'r').read().splitlines()


def get_random_name():
    return "{} {}".format(
        random.choice(firstnames).capitalize(),
        random.choice(lastnames).capitalize(),
    )
