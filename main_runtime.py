import json
import os
from src.crawler.sitemap_crawler import search_sitemap_by_url
from src.crawler.sitemap_crawler import load_bulk
from src.parser.parser_controller import parse
import src.storage.html_cache_manager as html_cache_manager
from src.preprocessor import preprocessor_controller
from src.storage import fact_check_manager
import logging
import logging.config
from logging_config import LOGGING_SETUP
import argparse

#Load logging Config:
logging.config.dictConfig(LOGGING_SETUP)
logger = logging.getLogger(__name__)

CONFIG_PORTALS = "config/portals.json"
PORTAL_DATA = "data/input/url_list.json"
OUTPUT = "data/output/export.csv"

def _load_json_data(file_path):
    """
    Loads the JSON file .

    :param file_path: path of the JSON file to be loaded
    :return: list of dictionaries containing the loaded data
    """
    if not os.path.exists(file_path):
        logger.critical(f"Error: {file_path} does not exist")
        raise FileNotFoundError(f"Error: {file_path} does not exist")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Management of the fact-checking extraction pipeline."
    )
    parser.add_argument(
        '--html-db-version-mode',nargs='+', type=str,
        help="1 modus, 2 copy path"
    )
    parser.add_argument(
        '--html-db-version', type=str,
        help=""
    )
    parser.add_argument(
        '--factcheck-db-version-mode',nargs='+', type=str,
        help="1 modus, 2 copy path"
    )
    parser.add_argument(
        '--factcheck_db_version', type=str,
        help=""
    )
    parser.add_argument(
        '--use-url-list', action='store_true',
        help=""
    )
    parser.add_argument(
        '--use-preprocessor', action='store_true',
        help=""
    )
    parser.add_argument(
        '--use-generated-parser', action='store_true',
        help=""
    )


    args = parser.parse_args()

    logger.info("Start Runtime pipeline...")

    if args.html_db_version:
        if args.html_db_version_mode[0] == "load":
            logger.info("Start Loading given html database...")
            try:
                hcm = html_cache_manager.HTMLCacheManager(version=args.html_db_version, mode="load")
            except Exception as e:
                logger.critical(f"Error: {e}")
        elif args.html_db_version_mode[0] == "copy":
            logger.info("Start copying given html database...")
            try:
                hcm = html_cache_manager.HTMLCacheManager(version=args.html_db_version, mode="copy", source_path=args.html_db_version_mode[1])
            except Exception as e:
                logger.critical(f"Error: {e}")
        else:
            logger.critical(f"Error: {args.html_db_version_mode} mode does not exist for HTMLCacheManager.\n Exiting pipline.")

    else:
        hcm = html_cache_manager.HTMLCacheManager(version=args.html_db_version, mode="create")

    if args.factcheck_db_version:
        if args.factcheck_db_version_mode == "load":
            logger.info("Start Loading given factcheck database...")
            try:
                fcm = fact_check_manager.FactCheckManager(version=args.factcheck_db_version, mode="load")
            except Exception as e:
                logger.critical(f"Error: {e}")
        elif args.factcheck_db_version_mode == "copy":
            logger.info("Start copying given factcheck database...")
            try:
                fcm = fact_check_manager.FactCheckManager(version=args.factcheck_db_version, mode="copy", source_path=args.factcheck_db_version_mode[1])
            except Exception as e:
                logger.critical(f"Error: {e}")
        else:
            logger.critical(f"Error: {args.factcheck_db_version_mode} mode does not exist for FactCheckManager.\n Exiting pipline.")
    else:
        fcm = fact_check_manager.FactCheckManager(version=args.factcheck_db_version, mode="create")

    logger.info("Start Crawling...")

    if args.use_url_list:
        logger.info("Using URL list...")
        portal_data = _load_json_data(PORTAL_DATA)
        load_bulk(portal_data,hcm)
    else:
        logger.info("Using integrated Crawler...")
        config = _load_json_data(CONFIG_PORTALS)
        for portal in config["portals"]:
            search_sitemap_by_url(portal["portal"], portal["url"], hcm)

    logger.info("Finished Crawling...")

    if args.use_preprocessor:
        logger.info("Start Preprocessing...")

        preprocessor_hcm = html_cache_manager.HTMLCacheManager(version= args.html_db_version +"_after_preprocessor", mode="create")
        while factcheck := hcm.pop_next_page():
            try:
                preprocessed = preprocessor_controller.preprocess(factcheck['portal'],factcheck['html_content'])
                preprocessor_hcm.save_html(factcheck['url'], factcheck['portal'], factcheck['portal_url'], preprocessed)
            except Exception as e:
                logger.error(f"Error: {e}")
        hcm = preprocessor_hcm


    if args.use_generated_parser:
        logger.info("Start Extraction via generated Parser ...")
        while factcheck := hcm.pop_next_page():
            try:
                data = parse(factcheck['portal'], factcheck['html_content'])
                fcm.add_fact_check(factcheck['portal'],factcheck['portal_url'], factcheck['url'], data)
            except Exception as e:
                logger.error(f"Error: {e}")

    else:
        logger.info("Start Extraction via LLM Parser ...")
        while factcheck := hcm.pop_next_page():
            try:
                data = parse(factcheck['portal'], factcheck['html_content'], True)
                fcm.add_fact_check(factcheck['portal'],factcheck['portal_url'], factcheck['url'], data)
            except Exception as e:
                logger.error(f"Error: {e}")

    fcm.export_as_csv(OUTPUT)
if __name__ == "__main__":
    main()
