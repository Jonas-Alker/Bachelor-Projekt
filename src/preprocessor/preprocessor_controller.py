import os
from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parent / "generated"

def get_existing_preprocessors():
    """
    Returns the portals for which a parser has already been generated
    :return: list of Portals
    """
    preprocessors = []

    if not os.path.exists(GENERATED_DIR):
        return[]

    for filename in os.listdir(GENERATED_DIR):
        if filename.endswith("_preprocessor.py"):
            portal_name = filename.replace("_preprocessor.py", "")
            preprocessors.append(portal_name)

    return preprocessors
