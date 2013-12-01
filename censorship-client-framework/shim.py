from argparse import ArgumentParser
from ConfigParser import SafeConfigParser
import os
import sys
from package_util import format_version, Blacklist, choose_eggs
import traceback

__version__ = "1.0"

if __name__ == "__main__":
    # Prevents an uncaught UnicodeEncodeError deep in many versions of sgmllib
    # that causes BeautifulSoup to crash.
    # site.py removes setdefaultencoding from sys. reload() puts it back.
    reload(sys)
    sys.setdefaultencoding("utf-8")

    # Check to see if we're running in a windows exe
    if hasattr(sys, 'frozen') and sys.frozen in ('windows_exe', 'console_exe'):
        install_path = os.path.abspath(sys.executable)
    else:
        install_path = os.path.realpath(__file__)
    
    # Change to the install directory, making life easier for init scripts.
    install_dir = os.path.split(install_path)[0]
    os.chdir(install_dir)

    parser = ArgumentParser()
    parser.add_argument('--config', default='bootstrap.cfg',
                      help='Read config from CONFIG.')
    parser.add_argument('--bootstrap', default='bootstrap',
                      help='Bootstrap package to load and run.')
    opts, other_args = parser.parse_known_args()

    config = SafeConfigParser()
    config.read(opts.config)

    # set up the path
    package_dir = os.path.abspath(config.get(opts.bootstrap, "package_dir"))
    bl = Blacklist(config)
    eggs = choose_eggs(package_dir, bl.get())
    bs_version, bs_path = (-1,), None
    if opts.bootstrap in eggs:
        bs_version, bs_path = eggs[opts.bootstrap]
        sys.path.insert(0, bs_path)
        sys.path.insert(0, package_dir)

    # import the bootstrap package, with fallback code
    try:
        mod = __import__(opts.bootstrap)
    except Exception as e:
        print >>sys.stderr, "Exception importing %s package v%s: %s %s\n%s" % (
            opts.bootstrap,
            format_version(bs_version),
            type(e),
            e,
            traceback.format_exc()
        )

        bl.add(opts.bootstrap, bs_version)
        with open(opts.config, 'wb') as f:
            config.write(f)

        os.execl(sys.executable, sys.executable, *sys.argv)

    # run the bootstrap main function as the main thread of exectution
    mod.main()
