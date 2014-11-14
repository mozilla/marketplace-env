#!/usr/bin/env python
import sys
import cmds


def main():

    parser = cmds.create_parser()
    args = parser.parse_args()
    args.func(args, parser)

if __name__ == "__main__":
    sys.exit(main())
