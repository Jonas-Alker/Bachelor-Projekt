import argparse

from evaluation.preprocess_and_parse_evaluation import test_extraction_quality_with_claims_kg
from evaluation.preprocess_and_parse_evaluation import test_extraction
import logging.config
from logging_config import LOGGING_SETUP

#Load logging Config:
logging.config.dictConfig(LOGGING_SETUP)
logger = logging.getLogger("main_evaluation")


def main():
    parser = argparse.ArgumentParser(
        description="Management of the fact-checking evaluation pipeline."
    )
    parser.add_argument(
        '--run-claims-kg',
        action='store_true',
        help="Runs the ClaimsKG-Extractions-evaluations."
    )
    parser.add_argument(
        '--run-all',
        action='store_true',
        help="Runs all available evaluations one after the other."
    )
    args = parser.parse_args()

    if not any(vars(args).values()):
        logger.warning("No evaluation has been selected. View help.")
        parser.print_help()
        return

    logger.info("Start evaluation pipeline...")

    try:
        if args.run_claims_kg or args.run_all:
            logger.info("Start ClaimsKG evaluation (“test_extraction_quality_with_claims_kg”)...")


            test_extraction_quality_with_claims_kg()

            logger.info("ClaimsKG evaluation successfully completed.")

    except Exception as e:
        logger.error(f"Critical error during evaluation: {e}")

    logger.info("Evaluation pipeline finished.")


if __name__ == "__main__":
    main()