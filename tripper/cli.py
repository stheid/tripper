import logging

import click
import yaml

from tripper.exec import Runner


@click.command()
@click.option('-config', default='config.yaml', help='Config file')
@click.option('-loglevel', default=logging.INFO, help='Config file')
def main(config, loglevel, **kwargs):
    logging.basicConfig(level=loglevel)
    if config is not None:
        with open(config) as f:
            conf_data = yaml.safe_load(f)
    else:
        conf_data = dict()
    config = {**conf_data, **kwargs}
    Runner(config['runner']).run()


if __name__ == '__main__':
    main()
