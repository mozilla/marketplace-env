#!/usr/bin/env python
import argcomplete
import sys
import cmds


def main():
    parser = cmds.create_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args, parser)

if __name__ == "__main__":
    sys.exit(main())
