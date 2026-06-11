import os
from pathlib import Path


GENERATED_DIR = Path(__file__).resolve().parent / "generated"

def get_existing_parsers():
    """
    Returns the portals for which a preprocessor has already been generated
    :return: list of Portals
    """
    parsers = []

    if not os.path.exists(GENERATED_DIR):
        return[]

    for filename in os.listdir(GENERATED_DIR):
        if filename.endswith("_parser.py"):
            portal_name = filename.replace("_parser.py", "")
            parsers.append(portal_name)

    return parsers
