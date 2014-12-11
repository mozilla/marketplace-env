#!/usr/bin/env python
import argcomplete
import sys
import cmds


def parse():
    parser = cmds.create_parser()
    argcomplete.autocomplete(parser)
    known_args = parser.parse_known_args()
    argv = []
    try:
        args, argv = known_args
    except IndexError:
        pass

    # If you have a method that accepts known args, then add the attribute
    # of argv to the func. Otherwise it will raise an error.
    if not hasattr(args.func, 'argv') and argv:
        parser.error('unrecognized arguments: %s' % ' '.join(argv))

    return args, parser, argv


def main():
    args, parser, argv = parse()

    # If the func accepts argv, then pass it in as well.
    if hasattr(args.func, 'argv'):
        return args.func(args, parser, argv)
    else:
        return args.func(args, parser)


if __name__ == "__main__":
    sys.exit(main())
