#!/usr/bin/env python
#
# Tested with yarn 1.22.19 and Python 3.10.8.

from datetime import datetime
from sys import stderr
from typing import Optional
from urllib.request import urlopen
from json import loads
from dataclasses import dataclass
from subprocess import run

def is_valid_pkg_prefix(c: str) -> bool:
    return c == '@' or c.isalnum()

## Collect packages

# --depth=0 is required so it won't list the same package twice. It will still list
# transient dependencies though.
dirty_pkgs = run(['yarn', 'list', '--silent', '--depth=0'], capture_output=True) \
    .stdout \
    .decode('utf-8') \
    .split('\n')

@dataclass
class Pkg:
    name: str
    version: str
    publish_date: Optional[datetime]

## Parse packages to remove non-useful characters
pkgs: list[Pkg] = []
for dirty_pkg in dirty_pkgs:
    for i, c in enumerate(dirty_pkg):
        # https://www.npmjs.com/package/validate-npm-package-name
        if is_valid_pkg_prefix(c):
            # pkg name has started.
            full_name = dirty_pkg[i::] # with version

            v_index = full_name.rindex('@')
            name = full_name[:v_index:]
            version = full_name[v_index + 1::]

            pkgs.append(Pkg(name, version, None))
            break

## Get packages' versions
for pkg in pkgs:
    url = f'https://registry.npmjs.com/{pkg.name}'
    body = loads(urlopen(url).read().decode('utf-8'))

    version_publish_date = body['time'].get(pkg.version)
    if version_publish_date is None:
        print(
            f'Could not find publish date for package {pkg.name}, version {pkg.version}. '
            f'Available versions are: {body["time"]}.',
            file=stderr
        )
    else:
        version_publish_date = datetime.strptime(version_publish_date, '%Y-%m-%dT%H:%M:%S.%f%z')
        pkg.publish_date = version_publish_date

## Print all, ordering by date
for pkg in sorted(pkgs, key=lambda p : p.publish_date):
    readable_publish_date = datetime.strftime(pkg.publish_date, '%Y/%m/%d %H:%M:%S')

    print(f'{pkg.name}: {readable_publish_date}')
