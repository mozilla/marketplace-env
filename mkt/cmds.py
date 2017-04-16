import argparse
import ConfigParser as configparser
import functools
import os
import subprocess
import sys
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
join = functools.partial(os.path.join, ROOT)

if 'mkt-data' in os.listdir(ROOT):
    join = functools.partial(os.path.join, ROOT, 'mkt-data')

CONFIG_PATH = os.path.expanduser('~/.wharfie')
FIG_PATH = os.getenv('FIG_FILE', os.path.expanduser('~/.mkt.fig.yml'))
BRANCHES = [
    'fireplace',
    'solitude',
    'spartacus',
    'webpay',
    'zamboni',
    'zippy',
]


def indent(text, times=1):
    wrapper = textwrap.TextWrapper(
        initial_indent='  '*times, width=90, subsequent_indent='  '*times
    )
    for line in text.splitlines():
        print wrapper.fill(line)


def get_dir(name, *args):
    root_dir = get_config_value('paths', 'root', None)
    if not root_dir:
        raise ValueError('"root" not set, run: mkt root [directory].')
    return os.path.join(root_dir, *args)


def check_git_config(args, parser):
    for branch in BRANCHES:
        branch_dir = get_dir(branch)
        cur_dir = os.getcwd()
        if os.path.isdir(branch_dir):
            try:
                os.chdir(branch_dir)
                print "[{0}]".format(branch)
                indent("[remotes]")
                indent(subprocess.check_output(['git', 'remote', '-v']), 2)
                indent("[Master branch origin]")
                origin = subprocess.check_output(['git', 'config', '--get',
                                                  'branch.master.remote'])
                indent(origin, 2)
                print
            finally:
                os.chdir(cur_dir)


def checkout(args, parser, gh_username=None):
    if not gh_username:
        gh_username = whoami(quiet=True)
    if not gh_username:
        parser.error('Please set a github username with the "whoami" '
                     'command first')

    for branch in BRANCHES:
        branch_dir = get_dir(branch)
        if not os.path.isdir(branch_dir):
            subprocess.call([
                'git', 'clone', '-o', args.moz_remote_name,
                'git@github.com:mozilla/{0}.git'.format(branch),
                branch_dir
            ])

            subprocess.call([
                'git', 'remote', 'add', args.fork_remote_name,
                'git@github.com:{0}/{1}.git'.format(gh_username, branch)
            ], cwd=branch_dir)

            subprocess.call([
                'git', 'config', 'branch.master.remote', args.fork_remote_name
            ])


def get_image(args, parser):
    image_name = args.name
    image_dir = get_dir('images', image_name)

    if not os.path.isdir(image_dir):
        parser.error('image_dir: {0} does not exist. '
                     'Exiting'.format(image_dir))

    return {
        'name': image_name,
        'dir': image_dir,
    }


def whoami(args=None, parser=None, quiet=False):
    user = os.environ.get('MKT_GITHUB_USERNAME', None)
    if not user:
        user = get_config_value('github', 'user') or user

    if args and args.github_username:
        user = args.github_username
        if user:
            set_config_value('github', 'user', user)

    if not quiet:
        if user:
            print('github user: {0}'.format(user))
        else:
            print('Try setting your github username with '
                  '"mkt whoami [github_username]"')

    return user


def shell(args, parser):
    image = get_image(args, parser)
    image_name = image['name']
    return subprocess.call(['docker', 'run', '-a', 'stdin', '-a', 'stdout',
                            '-i', '-t', image_name + '_img', '/bin/bash'])


def get_config_value(section, key, default=None):
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    try:
        return config.get(section, key)
    except configparser.NoSectionError:
        pass
    return default


def set_config_value(section, key, value):
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    try:
        config.add_section(section)
    except configparser.DuplicateSectionError:
        pass

    config.set(section, key, value)
    print('Saving {0} to {1}'.format(key, CONFIG_PATH))
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)


def root(args, parser):
    directory = os.path.abspath(os.path.expandvars(args.directory))
    if not os.path.exists(directory):
        raise ValueError('Directory {0} does not exist.'.format(directory))
    set_config_value('paths', 'root', directory)
    update(args, parser)


def locations():
    """
    Reports the locations of the main components of wharfie.
    """
    return {
        # Where the checked out projects to work on actually live.
        'tree': get_config_value('paths', 'root'),
        # Where the images live, will be local or in the installed file path.
        'image': join('images'),
        # Where the fig config lives, will be local or in the installed
        # file path.
        'fig.dist': join('fig.yml.dist'),
        # Where fig that the FIG_FILE uses lives.
        'fig': FIG_PATH
    }


def update(args, parser):
    context = locations()
    src_file = context['fig.dist']
    with open(src_file, 'r') as src:
        src_data = src.read()

    dest_file = context['fig']
    with open(dest_file, 'w') as dest:
        print 'Written fig file to {0}'.format(FIG_PATH)
        dest.write(src_data.format(**context))


def check_env():
    context = locations()
    default = os.getenv('FIG_FILE')
    if context['fig'] != default:
        print 'Set the following environment variable: '
        print 'FIG_FILE={0}'.format(FIG_PATH)
        print

    for path in ['tree', 'image']:
        if not os.path.exists(context[path]):
            print 'Path {0} does not exist.'


def create_parser():
    parser = argparse.ArgumentParser(description='Wharfie')

    subparsers = parser.add_subparsers(
        help='See each command for additional help',
        title='Sub-commands', description='Valid commands'
    )

    parser_root = subparsers.add_parser(
        'root', help='Set the root directory of wharfie trees.'
    )
    parser_root.add_argument(
        'directory', help='Path to an existing directory.'
    )
    parser_root.set_defaults(func=root)

    parser_update = subparsers.add_parser(
        'update', help='Updates the fig file from the template'
    )
    parser_update.set_defaults(func=update)

    parser_shell = subparsers.add_parser(
        'shell', help='Run image, and drop into a shell on it.'
    )
    parser_shell.add_argument(
        'name', help='The name of the image to run a shell on',
        metavar="IMAGE_NAME",
    )
    parser_shell.set_defaults(func=shell)
    parser_shell = subparsers.add_parser(
        'chkgitconfig', help='Print out the git config for mkt branches'
    )
    parser_shell.set_defaults(func=check_git_config)

    parser_whoami = subparsers.add_parser(
        'whoami', help='Check your github credentials'
    )
    parser_whoami.add_argument(
        'github_username', help='Your github username e.g. "jrrtolkien"',
        metavar="USER_NAME", default=None, nargs='?'
    )
    parser_whoami.set_defaults(func=whoami)

    parser_checkout = subparsers.add_parser(
        'checkout', help='Checkout your forks of sourcecode'
    )
    parser_checkout.add_argument(
        '--moz_remote_name',
        help='What to call the mozilla repo remote for this project. '
             'Following github terminology this defaults to "upstream"',
        metavar="MOZ_REMOTE_NAME",
        default='upstream', nargs='?'
    )
    parser_checkout.add_argument(
        '--fork_remote_name',
        help='What to call your fork remote for this project. Following '
             'github terminology this defaults to "origin"',
        metavar="FORK_REMOTE_NAME", default='origin', nargs='?'
    )
    parser_checkout.set_defaults(func=checkout)
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        check_env()
        args.func(args, parser)
    except Exception as e:
        print('Error: {0}'.format(e.message))
        raise

if __name__ == "__main__":
    sys.exit(main())
