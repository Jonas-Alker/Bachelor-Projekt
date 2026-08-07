import argparse

from evaluation.evaluation_preprocess_and_parse import (
    test_llm_directly_extraction_quality_against_ground_truth,
    test_llm_preprocessed_extraction_quality_against_ground_truth,
    test_claims_kg_quality_against_ground_truth,
    test_parser_against_ground_truth
)
from evaluation.evaluation_crawl import test_ClaimsKG_comparision
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
        '--run-llm-directly-ground-truth', action='store_true',
        help="Runs test_llm_directly_extraction_quality_against_ground_truth."
    )
    parser.add_argument(
        '--run-llm-preprocessed-ground-truth', action='store_true',
        help="Runs test_llm_preprocessed_extraction_quality_against_ground_truth."
    )
    parser.add_argument(
        '--run-claims-kg-ground-truth', action='store_true',
        help="Runs test_claims_kg_quality_against_ground_truth."
    )
    parser.add_argument(
        '--run-parser-ground-truth', action='store_true',
        help="Runs test_parser_against_ground_truth."
    )
    parser.add_argument(
        '--run-crawl-evaluation', action='store_true',
        help="Runs the crawl evaluation for politifact. WARNING: May take a very long time."
    )
    parser.add_argument(
        '--run-all', action='store_true',
        help="Runs all available evaluations one after the other."
    )
    parser.add_argument(
        '--run-all-extraction', action='store_true',
        help="Runs all extraction evaluations one after the other (excluding run-crawl-evaluation)."
    )
    parser.add_argument(
        '--language', type=str, default="english",
        help="Language parameter for ground truth evaluations (default: 'english' || Options: 'english'; 'german' )."
    )

    args = parser.parse_args()

    run_flags = [
        args.run_llm_directly_ground_truth,
        args.run_llm_preprocessed_ground_truth,
        args.run_claims_kg_ground_truth,
        args.run_parser_ground_truth,
        args.run_crawl_evaluation,
        args.run_all,
        args.run_all_extraction
    ]

    if not any(run_flags):
        logger.warning("No evaluation has been selected. View help.")
        parser.print_help()
        return

    if not any(vars(args).values()):
        logger.warning("No evaluation has been selected. View help.")
        parser.print_help()
        return


    logger.info("Start evaluation pipeline...")

    try:
        if args.run_all or args.run_all_extraction or args.run_llm_directly_ground_truth:
            logger.info(
                f"Running: test_llm_directly_extraction_quality_against_ground_truth (language: {args.language})...")
            test_llm_directly_extraction_quality_against_ground_truth(language=args.language)

        if args.run_all or args.run_all_extraction  or args.run_llm_preprocessed_ground_truth:
            logger.info(
                f"Running: test_llm_preprocessed_extraction_quality_against_ground_truth (language: {args.language})...")
            test_llm_preprocessed_extraction_quality_against_ground_truth(language=args.language)

        if args.run_all or args.run_all_extraction  or args.run_claims_kg_ground_truth:
            logger.info("Running: test_claims_kg_quality_against_ground_truth...")
            test_claims_kg_quality_against_ground_truth()

        if args.run_all or args.run_all_extraction  or args.run_parser_ground_truth:
            logger.info(f"Running: test_parser_against_ground_truth (language: {args.language})...")
            test_parser_against_ground_truth(language=args.language)

        if args.run_all or args.run_crawl_evaluation:
            logger.info("Running: crawl_evaluation...")
            test_ClaimsKG_comparision()

    except Exception as e:
        logger.error(f"Critical error during evaluation: {e}")

    logger.info("Evaluation pipeline finished.")


if __name__ == "__main__":
    main()