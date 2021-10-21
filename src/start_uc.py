import argparse
import sys
from typing import List

import alertstorm.main as alertstorm
import troubleshoot.main as troubleshoot
import troubleshoot_basic.main as troubleshoot_basic
import timeseries.main as timeseries

AVAILABLE_USE_CASES = {
    troubleshoot_basic.USE_CASE_ID: troubleshoot_basic.main,
    troubleshoot.USE_CASE_ID: troubleshoot.main,
    alertstorm.USE_CASE_ID: alertstorm.main,
    timeseries.USE_CASE_ID: timeseries.main
    ## Put the next usecase here!
}

def get_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        'usecase',
        type=str,
        choices=AVAILABLE_USE_CASES,
        help="The use case to start."
    )
    return parser

def start_uc(usecase: int, args: List[str]) -> None:
    if usecase not in AVAILABLE_USE_CASES: raise OSError("Invalid use case")
    AVAILABLE_USE_CASES[usecase](args)

def main(args: List[str]) -> None:
    parser = get_cli_parser()
    cli_options, remaining = parser.parse_known_args(args)
    start_uc(cli_options.usecase, remaining)


if __name__ == '__main__':
    main(sys.argv[1:])
