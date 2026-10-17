# Copyright (C) 2026 Open Source Robotics Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Decide whether a change needs to be built and tested.

Usage:
        gzdev filter-build-and-test
                [--build-platform=none]
                [--build-system=(cmake|bazel)]
                [--return-if-none=N]
                [--base=REF] [--head=REF]
                [--repo-path=DIR]

For now the answer is either "no build needed" or "build and run all tests":
a change needs neither a build nor tests when every file it touches matches the
patterns in plugins/config/filter-build-and-test.patterns.

Exit codes:
        0       the tool ran fine, the change needs a build and tests
        N       the tool ran fine, the change needs neither (--return-if-none)
        1       the tool could not decide (git, pattern file)
        2       bad arguments

Logs go to stderr. stdout is kept for the machine-readable result of later
versions and stays empty for now.

This module uses only the Python standard library so it can run on machines
without gzdev's requirements installed.
"""

import os
import re

PLATFORMS = ('none',)
BUILD_SYSTEMS = ('cmake', 'bazel')
KNOWN_SECTIONS = (('common',)
                  + tuple('build-system:' + s for s in BUILD_SYSTEMS)
                  + tuple('build-platform:' + p for p in PLATFORMS))
DEFAULT_PATTERNS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'config', 'filter-build-and-test.patterns')
SECTION_RE = re.compile(r'\[([a-z:-]+)\]')


class FilterBuildAndTestError(Exception):
    """The tool cannot decide; main() turns it into exit code 1."""


# --- patterns --------------------------------------------------------------

def compile_pattern(text, where):
    try:
        return re.compile(text)
    except re.error as ex:
        raise FilterBuildAndTestError('%s: invalid regular expression %r: %s'
                                      % (where, text, ex))


def load_patterns(path):
    """Return {section name: [compiled patterns]} read from a pattern file."""
    try:
        with open(path, encoding='utf-8') as patterns_file:
            lines = patterns_file.read().splitlines()
    except OSError as ex:
        raise FilterBuildAndTestError('cannot read %s: %s' % (path, ex))
    sections = {}
    current = None
    for number, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        where = '%s:%d' % (path, number)
        header = SECTION_RE.fullmatch(line)
        if header:
            current = header.group(1)
            if current not in KNOWN_SECTIONS:
                raise FilterBuildAndTestError('%s: unknown section [%s]'
                                              % (where, current))
            sections.setdefault(current, [])
        elif current is None:
            raise FilterBuildAndTestError('%s: pattern outside any section'
                                          % where)
        else:
            sections[current].append(compile_pattern(line, where))
    return sections


def active_sections(build_platform, build_system):
    return ['common', 'build-system:' + build_system,
            'build-platform:' + build_platform]


def active_patterns(sections, build_platform, build_system):
    patterns = []
    for name in active_sections(build_platform, build_system):
        patterns.extend(sections.get(name, []))
    return patterns


def is_ignorable(path, patterns):
    return any(pattern.search(path) for pattern in patterns)
