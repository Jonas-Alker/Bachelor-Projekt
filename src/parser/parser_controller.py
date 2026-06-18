import src.parser.llm_parser as llm_parser
import os
import sys
from pathlib import Path
import importlib.util

GENERATED_DIR = Path(__file__).resolve().parent / "generated"

def get_existing_parsers():
    """
    Returns the portals for which a preprocessor has already been generated.

    :return: list of portals
    """
    parsers = []

    if not os.path.exists(GENERATED_DIR):
        return[]

    for filename in os.listdir(GENERATED_DIR):
        if filename.endswith("_parser.py"):
            portal_name = filename.replace("_parser.py", "")
            parsers.append(portal_name)

    return parsers


def parse(portal_name, html,llm_based=False):
    """
    If available, forwards the method call to the relevant parser of the portal after it has been dynamically loaded.
    In the case of LLM extraction (llm_based = True), this is forwarded to the LLM.

    :param portal_name: name of the portal
    :param html: HTML of the fact check to be searched
    :param llm_based: Indicator for LLM extraction

    :return:extraction results
    """
    if llm_based:
        return llm_parser.parse_factcheck(html)
    else:
        file_path = GENERATED_DIR / f"{portal_name.lower()}_parser.py"
        if not file_path.exists():
            raise FileNotFoundError(f"Parser for {portal_name.lower()} does not exist")

        module_name = f"{portal_name.lower()}_parser"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if hasattr(module, 'parse_factcheck'):
            return module.parse_factcheck(html)
        else:
            raise AttributeError(f"Preprocessor for {portal_name.lower()} has no function parse_factcheck.")