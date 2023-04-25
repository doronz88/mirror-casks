import json
from pathlib import Path
from typing import Mapping

import click
import requests
from plumbum import FG, local

PACKAGES = ['pycharm-ce', 'emacs', 'sublime-text', 'rectangle', 'proxyman', 'flycut']

wget = local['wget']


def query_cask_json(name: str) -> Mapping:
    return json.loads(requests.get(f'https://formulae.brew.sh/api/cask/{name}.json').text)


def download_cask_rb(name: str) -> str:
    return requests.get(f'https://raw.githubusercontent.com/Homebrew/homebrew-cask/master/Casks/{name}.rb').text


@click.command()
@click.argument('output', type=click.Path())
@click.option('--prefix', default='', help='prefix downloaded packages')
@click.option('--new-url-base', default='PATCHED_BASE', help='what to replace the original URL base with')
def cli(output: str, prefix: str, new_url_base: str):
    """ Python3 utility for mirroring brew casks """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for package_name in PACKAGES:
        package_json = query_cask_json(package_name)
        package_rb = download_cask_rb(package_name)

        assets = set()
        assets.add(package_json['url'])
        url_base = package_json['url'].rsplit('/', 1)[0]
        for variation in package_json['variations'].values():
            url = variation.get('url')
            if url is not None:
                url_base = url.rsplit('/', 1)[0]
                assert url.startswith(url_base), 'not all assets start with same base'
                assets.add(url)

        package_rb = package_rb.replace(f'cask "{package_name}" do', f'cask "{prefix}{package_name}" do')
        package_rb = package_rb.replace(url_base, new_url_base)
        (output / f'{prefix}{package_name}.rb').write_text(package_rb)

        for url in assets:
            wget[url, '--directory-prefix', output, '--no-clobber'] & FG


if __name__ == '__main__':
    cli()
