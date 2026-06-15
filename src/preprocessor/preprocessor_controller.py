import os
import sys
from pathlib import Path
import importlib.util

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

def preprocess(portal_name, html):
    file_path = GENERATED_DIR / f"{portal_name.lower()}_preprocessor.py"
    if not file_path.exists():
        raise FileNotFoundError(f"Preprocessor for {portal_name.lower()} does not exist")

    module_name = f"{portal_name.lower()}_preprocessor"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if hasattr(module, 'preprocess_faktencheck'):
        return module.preprocess_faktencheck(html)
    else:
        raise AttributeError(f"Preprocessor for {portal_name.lower()} has no function preprocess_faktencheck.")