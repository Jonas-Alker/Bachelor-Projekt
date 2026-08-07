import os
import sys
from pathlib import Path
import importlib.util
import logging

#Getting Logger
logger = logging.getLogger(__name__)

GENERATED_DIR = Path(__file__).resolve().parent / "generated"

def get_existing_preprocessors():
    """
    Returns the portals for which a preprocessors has already been generated.

    :return: list of portals
    """
    preprocessors = []

    if not os.path.exists(GENERATED_DIR):
        logger.debug(f"Generated preprocessor directory not found at {GENERATED_DIR}. Returning empty list.")
        return[]

    for filename in os.listdir(GENERATED_DIR):
        if filename.endswith("_preprocessor.py"):
            portal_name = filename.replace("_preprocessor.py", "")
            preprocessors.append(portal_name)

    return preprocessors

def preprocess(portal_name, html):
    """
    If available, forwards the method call to the relevant preprocessor of the portal after it has been dynamically loaded.

    :param portal_name: name of the portal
    :param html: HTML of the fact check to be preprocessed

    :return:preprocess results
    """
    file_path = GENERATED_DIR / f"{portal_name.lower()}_preprocessor.py"
    if not file_path.exists():
        logger.error(f"Preprocessor for {portal_name.lower()} does not exist")
        raise FileNotFoundError(f"Preprocessor for {portal_name.lower()} does not exist")

    module_name = f"{portal_name.lower()}_preprocessor"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    if hasattr(module, 'preprocess_factcheck'):
        logger.debug(f"Successfully loaded and executing preprocessor script for {portal_name.lower()}.")
        try:
            return module.preprocess_factcheck(html)
        except Exception as e:
            logger.error(f"Error during preprocessing via {portal_name.lower()}: {e}")
            return None
    else:
        logger.error(f"Preprocessor for {portal_name.lower()} has no function preprocess_factcheck.")
        raise AttributeError(f"Preprocessor for {portal_name.lower()} has no function preprocess_factcheck.")