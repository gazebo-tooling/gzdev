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
                [--build-platform=(none|jenkins)]
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

import argparse
import os
import re
import subprocess
import sys

PLATFORMS = ('none', 'jenkins')
BUILD_SYSTEMS = ('cmake', 'bazel')
KNOWN_SECTIONS = (('common',)
                  + tuple('build-system:' + s for s in BUILD_SYSTEMS)
                  + tuple('build-platform:' + p for p in PLATFORMS))
DEFAULT_PATTERNS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'config', 'filter-build-and-test.patterns')
SECTION_RE = re.compile(r'\[([a-z:-]+)\]')
SHA_RE = re.compile(r'[0-9a-f]{40}([0-9a-f]{24})?')
EXIT_OK = 0
EXIT_FAILURE = 1
MIN_RETURN_IF_NONE = 3
MAX_RETURN_IF_NONE = 125
MAX_LISTED_FILES = 20
# Control characters, escaped wherever a file name is reported
CONTROL_RE = re.compile('[\x00-\x1f\x7f-\x9f]')


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


# --- change set ------------------------------------------------------------

def git(repo_path, *args):
    """Run git in repo_path and return its stdout."""
    cmd = ['git', '-C', repo_path] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True)
    except OSError as ex:
        raise FilterBuildAndTestError('cannot run git: %s' % ex)
    if result.returncode != 0:
        raise FilterBuildAndTestError("'%s' failed: %s" % (
            ' '.join(cmd), result.stderr.decode('utf-8', 'replace').strip()))
    return result.stdout.decode('utf-8', 'surrogateescape')


def split_nul(output):
    return [path for path in output.split('\0') if path]


def diff_paths(repo_path, *revisions):
    """Paths changed between revisions; one revision means the working tree."""
    return split_nul(git(repo_path, 'diff', '--name-only', '--no-renames',
                         '-z', *revisions))


def merge_base(repo_path, first, second):
    return git(repo_path, 'merge-base', first, second).strip()


def check_sha(value, origin):
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise FilterBuildAndTestError('%s is not a commit SHA: %r'
                                      % (origin, value))
    return value


def working_tree_changes(repo_path, base):
    """Changes since the merge-base, uncommitted and untracked included."""
    paths = diff_paths(repo_path, merge_base(repo_path, base, 'HEAD'))
    untracked = split_nul(git(repo_path, 'ls-files', '--others',
                              '--exclude-standard', '-z'))
    return paths + [path for path in untracked if path not in paths]


def explicit_changes(platform, repo_path, base, head):
    if head:
        return diff_paths(repo_path, merge_base(repo_path, base, head), head)
    if platform == 'none':
        return working_tree_changes(repo_path, base)
    return diff_paths(repo_path, merge_base(repo_path, base, 'HEAD'), 'HEAD')


def jenkins_changes(repo_path, env):
    """Changes of a ghprb pull request, or None outside a pull request."""
    target = env.get('ghprbTargetBranch', '')
    commit = env.get('ghprbActualCommit', '')
    if not target or not commit:
        return None
    commit = check_sha(commit, 'ghprbActualCommit')
    base = merge_base(repo_path, 'origin/' + target, commit)
    return diff_paths(repo_path, base, commit)


def changed_files(args, env):
    """Return the changed paths, or None when the run is not a pull request."""
    if args.base:
        return explicit_changes(args.build_platform, args.repo_path,
                                args.base, args.head)
    return jenkins_changes(args.repo_path, env)


# --- reporting -------------------------------------------------------------

def printable(text):
    """Escape control characters, so the text stays on one line."""
    return CONTROL_RE.sub(lambda match: '\\x%02x' % ord(match.group()), text)


def log(message):
    # A file name with a newline must not start a line of its own, such as a
    # GitHub workflow command
    print('filter-build-and-test: ' + printable(message), file=sys.stderr)


def no_build_message(changed):
    return ('No build or tests needed: all %d changed files match the ignore'
            ' patterns' % len(changed))


def log_paths(title, paths):
    log(title)
    for path in paths[:MAX_LISTED_FILES]:
        log('  ' + path)
    if len(paths) > MAX_LISTED_FILES:
        log('  ... and %d more' % (len(paths) - MAX_LISTED_FILES))


# --- decision --------------------------------------------------------------

def decide(args, env, patterns_file):
    """Return the exit code for a parsed command line."""
    patterns = active_patterns(load_patterns(patterns_file),
                               args.build_platform, args.build_system)
    changed = changed_files(args, env)
    if changed is None:
        log('not a pull request: build and run all tests')
        return EXIT_OK
    if not changed:
        log('found no changed files: build and run all tests')
        return EXIT_OK
    needs_build = [path for path in changed
                   if not is_ignorable(path, patterns)]
    if needs_build:
        log_paths('%d of %d changed files need a build and tests:'
                  % (len(needs_build), len(changed)), needs_build)
        return EXIT_OK
    log_paths(no_build_message(changed) + ':', changed)
    if args.return_if_none is None:
        return EXIT_OK
    return args.return_if_none


# --- command line ----------------------------------------------------------

def return_code(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError('%r is not an integer' % text)
    if not MIN_RETURN_IF_NONE <= value <= MAX_RETURN_IF_NONE:
        raise argparse.ArgumentTypeError(
            'must be between %d and %d, got %d'
            % (MIN_RETURN_IF_NONE, MAX_RETURN_IF_NONE, value))
    return value


def git_ref(text):
    if not text or text.startswith('-'):
        raise argparse.ArgumentTypeError('invalid git reference %r' % text)
    return text


def build_parser():
    parser = argparse.ArgumentParser(
        prog='gzdev filter-build-and-test', allow_abbrev=False,
        description='Decide whether a change needs to be built and tested.')
    parser.add_argument('--build-platform', choices=PLATFORMS,
                        default='none')
    parser.add_argument('--build-system', choices=BUILD_SYSTEMS,
                        default='cmake')
    parser.add_argument('--return-if-none', type=return_code, metavar='N',
                        help='exit code when no build or tests are needed'
                        ' (%d-%d)' % (MIN_RETURN_IF_NONE, MAX_RETURN_IF_NONE))
    parser.add_argument('--base', type=git_ref, metavar='REF')
    parser.add_argument('--head', type=git_ref, metavar='REF')
    parser.add_argument('--repo-path', default='.', metavar='DIR')
    return parser


def parse_args(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.head and not args.base:
        parser.error('--head requires --base')
    if args.build_platform == 'none' and not args.base:
        parser.error('--build-platform=none requires --base')
    return args


def main(argv=None, env=None, patterns_file=DEFAULT_PATTERNS_FILE):
    args = parse_args(argv)
    if env is None:
        env = os.environ
    log('build-platform=%s build-system=%s sections=[%s]' % (
        args.build_platform, args.build_system,
        ', '.join(active_sections(args.build_platform, args.build_system))))
    try:
        return decide(args, env, patterns_file)
    except FilterBuildAndTestError as ex:
        log('cannot decide: %s' % ex)
        return EXIT_FAILURE


if __name__ == '__main__':
    sys.exit(main())
