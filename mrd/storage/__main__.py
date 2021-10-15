
import argparse

import logging

from .version import version


def main():
    logging.info(f"MRD Storage Server v. {version}")

    parser = argparse.ArgumentParser(description=f"MRD Storage Server v. {version}",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-p', '--port', type=int, default=9112,
                        help="")

    parser.add_argument('--database')
    parser.add_argument('--blob-storage')

    args = parser.parse_args()

    # This is a bit weird. Don't know how to get from here to gunicorn. Let's see.

    logging.info("Parsed some arguments. All right!")
    print(args)


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)-15s %(levelname)s %(message)s", level=logging.INFO)
    main()
