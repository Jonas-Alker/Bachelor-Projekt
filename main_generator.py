import src.preprocessor.preprocessor_controller as preprocessor_c
import src.parser.parser_controller as parser_c
import tools.generate_parser as gen_parser
import tools.generate_preprocessor as gen_preprocessor
import json

def generate_missing_codes():
    """
    Compare the portals stored in config.json with the existing parsers and preprocessors, and generate any missing ones.
    """
    with open("config/portals.json", "r") as f:
        config = json.load(f)
    existing_parser = parser_c.get_existing_parsers()
    existing_preprocessor = preprocessor_c.get_existing_preprocessors()

    for portal in config:
        if portal['name'].lower() not in existing_parser:
            gen_parser.generate_parser(portal["factcheck_example"],portal['name'].lower())
        if portal['name'].lower() not in existing_preprocessor:
            gen_preprocessor.generate_preprocessor(portal["factcheck_example"],portal['name'].lower())

if __name__ == "__main__":
    generate_missing_codes()
