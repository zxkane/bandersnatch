import argparse
import bandersnatch.log
import bandersnatch.master
import bandersnatch.mirror
import bandersnatch.utils
import configparser
import logging
import logging.config
import os.path
import shutil


logger = logging.getLogger(__name__)


def mirror(config):
    # Always reference those classes here with the fully qualified name to
    # allow them being patched by mock libraries!
    master = bandersnatch.master.Master(
        config.get('mirror', 'master'),
        float(config.get('mirror', 'timeout')))
    mirror = bandersnatch.mirror.Mirror(
        config.get('mirror', 'directory'), master,
        stop_on_error=config.getboolean('mirror', 'stop-on-error'),
        workers=config.getint('mirror', 'workers'),
        delete_packages=config.getboolean('mirror', 'delete-packages'),
        hash_index=config.getboolean('mirror', 'hash-index'))
    changed_packages = mirror.synchronize()
    logger.info("{0} packages had changes".format(len(changed_packages)))
    for package_name, changes in changed_packages.items():
        logger.debug("{0} removed: {1}".format(package_name, changes[0]))
        logger.debug("{0} added: {1}".format(package_name, changes[1]))


def main():
    bandersnatch.log.setup_logging()

    parser = argparse.ArgumentParser(
        description='PyPI PEP 381 mirroring client.')
    parser.add_argument('-c', '--config', default='/etc/bandersnatch.conf',
                        help='use configuration file (default: %(default)s)')
    subparsers = parser.add_subparsers()

    # `mirror` command
    p = subparsers.add_parser(
        'mirror',
        help='Performs a one-time synchronization with '
             'the PyPI master server.')
    p.set_defaults(func=mirror)

    args = parser.parse_args()

    # Prepare default config file if needed.
    default_config = os.path.join(os.path.dirname(__file__), 'default.conf')
    if not os.path.exists(args.config):
        logger.warning('Config file \'{0}\' missing, creating default config.'.
                       format(args.config))
        logger.warning(
            'Please review the config file, then run \'bandersnatch\' again.')
        try:
            shutil.copy(default_config, args.config)
        except IOError as e:
            logger.error('Could not create config file: {0}'.format(str(e)))
        return 1

    config = configparser.ConfigParser()
    config.read([default_config, args.config])

    if config.has_option('mirror', 'log-config'):
        logging.config.fileConfig(
            os.path.expanduser(config.get('mirror', 'log-config')))
    args.func(config)
