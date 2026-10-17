#
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
"""Unittests for filter_build_and_test.py."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree

import filter_build_and_test

GZDEV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'gzdev.py')


# Keep the tests away from the user's git configuration (signing, hooks...)
GIT_ENV = {
    'GIT_CONFIG_GLOBAL': os.devnull,
    'GIT_CONFIG_NOSYSTEM': '1',
    'GIT_AUTHOR_NAME': 'filter-build-and-test',
    'GIT_AUTHOR_EMAIL': 'filter-build-and-test@example.com',
    'GIT_COMMITTER_NAME': 'filter-build-and-test',
    'GIT_COMMITTER_EMAIL': 'filter-build-and-test@example.com',
}
_saved_env = {}


def setUpModule():
    for key, value in GIT_ENV.items():
        _saved_env[key] = os.environ.get(key)
        os.environ[key] = value


def tearDownModule():
    for key, value in _saved_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def run_git(cwd, *args):
    result = subprocess.run(
        ['git', '-c', 'init.defaultBranch=main', '-c', 'commit.gpgsign=false',
         '-C', cwd] + list(args),
        capture_output=True, check=True)
    return result.stdout.decode('utf-8').strip()


class GitRepo:
    """A throwaway repository; commit() returns the new commit SHA."""

    def __init__(self, path):
        self.path = path
        os.makedirs(path)
        run_git(path, 'init', '-q')

    def write(self, relative_path, content='content\n'):
        full_path = os.path.join(self.path, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as written_file:
            written_file.write(content)

    def commit(self, message, files):
        for relative_path, content in files.items():
            self.write(relative_path, content)
        run_git(self.path, 'add', '-A')
        run_git(self.path, 'commit', '-q', '-m', message)
        return run_git(self.path, 'rev-parse', 'HEAD')

    def git(self, *args):
        return run_git(self.path, *args)


def run_main(argv, env=None,
             patterns_file=filter_build_and_test.DEFAULT_PATTERNS_FILE):
    """Return (exit code, stdout, stderr) of filter_build_and_test.main()."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = filter_build_and_test.main(
                argv, env if env is not None else {}, patterns_file)
        except SystemExit as ex:
            code = ex.code
    return code, out.getvalue(), err.getvalue()


class TempDirTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='filter_build_and_test_')
        self.addCleanup(shutil.rmtree, self.tmp)

    def tmp_path(self, *parts):
        return os.path.join(self.tmp, *parts)

    def write_file(self, name, content):
        path = self.tmp_path(name)
        with open(path, 'w', encoding='utf-8') as written_file:
            written_file.write(content)
        return path


class TestPatternFile(TempDirTest):

    def test_sections_comments_and_union(self):
        path = self.write_file('p', '# comment\n\n[common]\n^README\\.md$\n'
                               '[build-system:cmake]\nBUILD\\.bazel$\n'
                               '[build-platform:none]\n^\\.github/\n')
        sections = filter_build_and_test.load_patterns(path)
        self.assertEqual(sorted(sections), ['build-platform:none',
                                            'build-system:cmake', 'common'])
        patterns = filter_build_and_test.active_patterns(sections, 'none',
                                                         'cmake')
        self.assertEqual([p.pattern for p in patterns],
                         ['^README\\.md$', 'BUILD\\.bazel$', '^\\.github/'])

    def test_sections_missing_from_the_file_are_empty(self):
        path = self.write_file('p', '[common]\n^LICENSE$\n')
        sections = filter_build_and_test.load_patterns(path)
        patterns = filter_build_and_test.active_patterns(sections, 'none',
                                                         'bazel')
        self.assertEqual([p.pattern for p in patterns], ['^LICENSE$'])

    def test_crlf_line_endings_load_the_same_patterns(self):
        # gzdev cloned on Windows with core.autocrlf=true
        path = self.tmp_path('p')
        with open(path, 'w', encoding='utf-8', newline='\r\n') as crlf_file:
            crlf_file.write('# comment\n[common]\n^README\\.md$\n')
        sections = filter_build_and_test.load_patterns(path)
        self.assertEqual([p.pattern for p in sections['common']],
                         ['^README\\.md$'])
        self.assertTrue(filter_build_and_test.is_ignorable('README.md',
                                                           sections['common']))

    def test_unknown_section_is_an_error(self):
        path = self.write_file('p', '[build-platform:travis]\n^a$\n')
        with self.assertRaisesRegex(
                filter_build_and_test.FilterBuildAndTestError,
                'unknown section'):
            filter_build_and_test.load_patterns(path)

    def test_pattern_outside_any_section_is_an_error(self):
        path = self.write_file('p', '^README\\.md$\n[common]\n')
        with self.assertRaisesRegex(
                filter_build_and_test.FilterBuildAndTestError,
                'outside any section'):
            filter_build_and_test.load_patterns(path)

    def test_invalid_regular_expression_is_an_error(self):
        path = self.write_file('p', '[common]\n[unclosed\n')
        with self.assertRaisesRegex(
                filter_build_and_test.FilterBuildAndTestError,
                'p:2: invalid regular expression'):
            filter_build_and_test.load_patterns(path)

    def test_missing_file_is_an_error(self):
        with self.assertRaisesRegex(
                filter_build_and_test.FilterBuildAndTestError,
                'cannot read'):
            filter_build_and_test.load_patterns(self.tmp_path('missing'))


class TestShippedPatterns(unittest.TestCase):

    CASES = [
        # path, build platform, build system, ignorable
        # [common]
        ('README.md', 'none', 'cmake', True),
        ('README.md', 'none', 'bazel', True),
        ('Changelog.md', 'none', 'cmake', True),
        ('Migration.md', 'none', 'cmake', True),
        ('CONTRIBUTING.md', 'none', 'cmake', True),
        ('LICENSE', 'none', 'cmake', True),
        ('.github/CODEOWNERS', 'none', 'cmake', True),
        ('.pre-commit-config.yaml', 'none', 'cmake', True),
        ('.pre-commit-config.yml', 'none', 'bazel', True),
        ('docker/Dockerfile.base', 'none', 'cmake', True),
        ('test/docker/Dockerfile', 'none', 'cmake', False),
        ('.gitignore', 'none', 'cmake', True),
        ('test/.gitignore', 'none', 'bazel', True),
        ('.dockerignore', 'none', 'cmake', True),
        ('docker/.dockerignore', 'none', 'cmake', True),
        # [build-system:cmake]
        ('BUILD.bazel', 'none', 'cmake', True),
        ('src/BUILD.bazel', 'none', 'cmake', True),
        ('MODULE.bazel', 'none', 'cmake', True),
        ('.bazelrc', 'none', 'cmake', True),
        ('.bazelversion', 'none', 'cmake', True),
        ('.bcr/metadata.template.json', 'none', 'cmake', True),
        ('bazel/gz_sim_system_libraries.bzl', 'none', 'cmake', True),
        ('bazel/BUILD.bazel', 'none', 'bazel', False),
        ('src/bazel/Foo.cc', 'none', 'cmake', False),
        ('BUILD.bazel', 'none', 'bazel', False),
        ('MODULE.bazel', 'none', 'bazel', False),
        # [build-system:bazel]
        ('CMakeLists.txt', 'none', 'cmake', False),
        ('CMakeLists.txt', 'none', 'bazel', True),
        ('sdf/1.12/CMakeLists.txt', 'none', 'bazel', True),
        ('cmake/FindFoo.cmake', 'none', 'bazel', False),
        # [build-platform:jenkins]
        ('CONTRIBUTING.md', 'jenkins', 'cmake', True),
        ('BUILD.bazel', 'jenkins', 'cmake', True),
        ('.github/workflows/ci.yml', 'jenkins', 'cmake', True),
        ('.github/ci/packages.apt', 'jenkins', 'cmake', False),
        ('codecov.yml', 'jenkins', 'cmake', False),
        # [build-platform:gh-actions]
        ('README.md', 'gh-actions', 'bazel', True),
        ('src/BUILD.bazel', 'gh-actions', 'cmake', True),
        ('.github/workflows/ci.yml', 'gh-actions', 'cmake', False),
        ('codecov.yml', 'gh-actions', 'cmake', False),
        # [build-platform:none]
        ('.github/workflows/ci.yml', 'none', 'cmake', True),
        ('.github/ci/packages.apt', 'none', 'cmake', True),
        ('codecov.yml', 'none', 'cmake', True),
        ('.codecov.yaml', 'none', 'bazel', True),
        # files that always need a build and tests
        ('src/Foo.cc', 'none', 'cmake', False),
        ('include/gz/foo/Foo.hh', 'none', 'cmake', False),
        ('test/README.md', 'none', 'cmake', False),
        ('LICENSE.txt', 'none', 'cmake', False),
    ]

    def test_shipped_file_loads(self):
        sections = filter_build_and_test.load_patterns(
            filter_build_and_test.DEFAULT_PATTERNS_FILE)
        self.assertIn('common', sections)

    def test_cases(self):
        sections = filter_build_and_test.load_patterns(
            filter_build_and_test.DEFAULT_PATTERNS_FILE)
        for path, platform, system, ignorable in self.CASES:
            with self.subTest(path=path, platform=platform, system=system):
                patterns = filter_build_and_test.active_patterns(
                    sections, platform, system)
                self.assertEqual(
                    filter_build_and_test.is_ignorable(path, patterns),
                    ignorable)


class TestChangeDetection(TempDirTest):

    def make_origin(self):
        """main: A then B (src/b.cc); feature from A: C (README.md)."""
        origin = GitRepo(self.tmp_path('origin'))
        origin.git('config', 'uploadpack.allowAnySHA1InWant', 'true')
        commits = {'A': origin.commit('A', {'README.md': 'a\n',
                                            'src/a.cc': 'a\n'})}
        origin.git('checkout', '-q', '-b', 'feature')
        commits['C'] = origin.commit('C', {'README.md': 'c\n'})
        origin.git('checkout', '-q', 'main')
        commits['B'] = origin.commit('B', {'src/b.cc': 'b\n'})
        return origin, commits

    def make_pr_merge_clone(self):
        """Shallow clone of a test-merge commit, as actions/checkout does."""
        origin, commits = self.make_origin()
        origin.git('checkout', '-q', '-b', 'pr-merge', 'main')
        origin.git('merge', '-q', '--no-ff', '-m', 'merge', 'feature')
        clone = self.tmp_path('clone')
        run_git(self.tmp, 'clone', '-q', '--depth=1', '--branch', 'pr-merge',
                'file://' + origin.path, clone)
        return clone, commits

    def event_file(self, base_sha):
        return self.write_file('event.json', json.dumps(
            {'pull_request': {'base': {'sha': base_sha}}}))

    def test_jenkins_diffs_from_the_merge_base(self):
        origin, commits = self.make_origin()
        clone = self.tmp_path('clone')
        run_git(self.tmp, 'clone', '-q', origin.path, clone)
        env = {'ghprbTargetBranch': 'main', 'ghprbActualCommit': commits['C']}
        self.assertEqual(filter_build_and_test.jenkins_changes(clone, env),
                         ['README.md'])

    def test_jenkins_ignores_target_changes_merged_into_the_pr(self):
        origin, commits = self.make_origin()
        origin.git('checkout', '-q', 'feature')
        origin.git('merge', '-q', '--no-ff', '-m', 'merge main', 'main')
        head = origin.git('rev-parse', 'HEAD')
        clone = self.tmp_path('clone')
        run_git(self.tmp, 'clone', '-q', origin.path, clone)
        env = {'ghprbTargetBranch': 'main', 'ghprbActualCommit': head}
        self.assertEqual(filter_build_and_test.jenkins_changes(clone, env),
                         ['README.md'])

    def test_jenkins_unknown_target_branch_is_an_error(self):
        origin, commits = self.make_origin()
        clone = self.tmp_path('clone')
        run_git(self.tmp, 'clone', '-q', origin.path, clone)
        env = {'ghprbTargetBranch': 'gz-sim99',
               'ghprbActualCommit': commits['C']}
        with self.assertRaisesRegex(
                filter_build_and_test.FilterBuildAndTestError,
                'merge-base origin/gz-sim99'):
            filter_build_and_test.jenkins_changes(clone, env)

    def test_jenkins_outside_a_pull_request(self):
        self.assertIsNone(filter_build_and_test.jenkins_changes(self.tmp, {}))
        self.assertIsNone(filter_build_and_test.jenkins_changes(
            self.tmp, {'ghprbTargetBranch': 'main'}))

    def test_jenkins_rejects_a_commit_that_is_not_a_sha(self):
        env = {'ghprbTargetBranch': 'main', 'ghprbActualCommit': '--all'}
        with self.assertRaisesRegex(
                filter_build_and_test.FilterBuildAndTestError,
                'not a commit SHA'):
            filter_build_and_test.jenkins_changes(self.tmp, env)

    def test_gh_actions_fetches_the_base_into_a_shallow_clone(self):
        clone, commits = self.make_pr_merge_clone()
        self.assertFalse(
            filter_build_and_test.commit_exists(clone, commits['B']))
        env = {'GITHUB_EVENT_NAME': 'pull_request',
               'GITHUB_EVENT_PATH': self.event_file(commits['B'])}
        self.assertEqual(filter_build_and_test.gh_actions_changes(clone, env),
                         ['README.md'])
        self.assertTrue(
            filter_build_and_test.commit_exists(clone, commits['B']))

    def test_gh_actions_full_history_checkout(self):
        origin, commits = self.make_origin()
        origin.git('checkout', '-q', '-b', 'pr-merge', 'main')
        origin.git('merge', '-q', '--no-ff', '-m', 'merge', 'feature')
        clone = self.tmp_path('clone')
        run_git(self.tmp, 'clone', '-q', '--branch', 'pr-merge',
                origin.path, clone)
        self.assertTrue(
            filter_build_and_test.commit_exists(clone, commits['B']))
        env = {'GITHUB_EVENT_NAME': 'pull_request',
               'GITHUB_EVENT_PATH': self.event_file(commits['B'])}
        self.assertEqual(filter_build_and_test.gh_actions_changes(clone, env),
                         ['README.md'])

    def test_gh_actions_stale_base_only_adds_files(self):
        clone, commits = self.make_pr_merge_clone()
        env = {'GITHUB_EVENT_NAME': 'pull_request_target',
               'GITHUB_EVENT_PATH': self.event_file(commits['A'])}
        changes = filter_build_and_test.gh_actions_changes(clone, env)
        assert changes is not None
        self.assertEqual(sorted(changes), ['README.md', 'src/b.cc'])

    def test_gh_actions_outside_a_pull_request(self):
        self.assertIsNone(filter_build_and_test.gh_actions_changes(
            self.tmp, {'GITHUB_EVENT_NAME': 'push'}))

    def test_gh_actions_unreadable_event_is_an_error(self):
        bad_event = self.write_file('bad.json', '{"pull_request": {}}')
        for path in ('', self.tmp_path('missing.json'), bad_event):
            with self.subTest(path=path):
                env = {'GITHUB_EVENT_NAME': 'pull_request',
                       'GITHUB_EVENT_PATH': path}
                with self.assertRaises(
                        filter_build_and_test.FilterBuildAndTestError):
                    filter_build_and_test.gh_actions_changes(self.tmp, env)

    def test_none_includes_uncommitted_and_untracked_files(self):
        repo = GitRepo(self.tmp_path('repo'))
        repo.commit('A', {'README.md': 'a\n', 'src/a.cc': 'a\n'})
        repo.write('src/a.cc', 'changed\n')
        repo.write('CONTRIBUTING.md', 'staged\n')
        repo.git('add', 'CONTRIBUTING.md')
        repo.write('docs/new.md', 'untracked\n')
        repo.write('build/ignored.o', 'ignored\n')
        repo.write('.gitignore', 'build/\n')
        self.assertEqual(
            sorted(filter_build_and_test.working_tree_changes(repo.path,
                                                              'main')),
            ['.gitignore', 'CONTRIBUTING.md', 'docs/new.md', 'src/a.cc'])

    def test_a_rename_lists_both_paths(self):
        repo = GitRepo(self.tmp_path('repo'))
        base = repo.commit('A', {'src/old.cc': 'same content\n' * 20})
        repo.git('mv', 'src/old.cc', 'Migration.md')
        head = repo.commit('B', {})
        self.assertEqual(
            sorted(filter_build_and_test.explicit_changes('jenkins', repo.path,
                                                          base, head)),
            ['Migration.md', 'src/old.cc'])

    def test_unusual_paths_are_returned_verbatim(self):
        repo = GitRepo(self.tmp_path('repo'))
        base = repo.commit('A', {'README.md': 'a\n'})
        head = repo.commit('B', {'docs/ñandú file.md': 'b\n'})
        self.assertEqual(
            filter_build_and_test.explicit_changes('none', repo.path, base,
                                                   head),
            ['docs/ñandú file.md'])


class TestDecision(TempDirTest):

    def setUp(self):
        super().setUp()
        self.repo = GitRepo(self.tmp_path('repo'))
        self.base = self.repo.commit('A', {'README.md': 'a\n',
                                           'src/a.cc': 'a\n',
                                           'BUILD.bazel': 'a\n'})
        self.docs = self.repo.commit('docs', {'README.md': 'docs\n'})
        self.repo.git('checkout', '-q', '-b', 'code', self.base)
        self.code = self.repo.commit('code', {'src/a.cc': 'code\n'})
        self.repo.git('checkout', '-q', '-b', 'bazel', self.base)
        self.bazel = self.repo.commit('bazel', {'BUILD.bazel': 'bazel\n'})

    def args(self, head, *extra):
        return ['--repo-path', self.repo.path, '--base', self.base,
                '--head', head] + list(extra)

    def test_no_build_needed_returns_the_requested_code(self):
        code, out, err = run_main(self.args(self.docs, '--return-if-none',
                                            '99'))
        self.assertEqual(code, 99)
        self.assertEqual(out, '')
        self.assertIn('No build or tests needed: all 1 changed files match',
                      err)

    def test_no_build_needed_without_return_if_none_returns_0(self):
        code, out, err = run_main(self.args(self.docs))
        self.assertEqual(code, 0)
        self.assertIn('No build or tests needed', err)

    def test_build_needed_returns_0_and_lists_the_files(self):
        code, out, err = run_main(self.args(self.code, '--return-if-none',
                                            '99'))
        self.assertEqual(code, 0)
        self.assertEqual(out, '')
        self.assertIn('1 of 1 changed files need a build and tests:', err)
        self.assertIn('filter-build-and-test:   src/a.cc', err)

    def test_deleting_a_source_file_needs_a_build(self):
        self.repo.git('checkout', '-q', '-b', 'delete', self.base)
        self.repo.git('rm', '-q', 'src/a.cc')
        delete = self.repo.commit('delete', {})
        code, _, err = run_main(self.args(delete, '--return-if-none', '99'))
        self.assertEqual(code, 0)
        self.assertIn('filter-build-and-test:   src/a.cc', err)

    def test_build_system_selects_the_bazel_patterns(self):
        cmake = run_main(self.args(self.bazel, '--return-if-none', '99'))
        bazel = run_main(self.args(self.bazel, '--return-if-none', '99',
                                   '--build-system', 'bazel'))
        self.assertEqual(cmake[0], 99)
        self.assertEqual(bazel[0], 0)

    def test_empty_change_set_runs_the_tests(self):
        code, _, err = run_main(self.args(self.base, '--return-if-none',
                                          '99'))
        self.assertEqual(code, 0)
        self.assertIn('found no changed files', err)

    def test_outside_a_pull_request_runs_the_tests(self):
        code, _, err = run_main(['--build-platform', 'jenkins',
                                 '--repo-path', self.repo.path,
                                 '--return-if-none', '99'])
        self.assertEqual(code, 0)
        self.assertIn('not a pull request', err)

    def test_explicit_base_overrides_ci_detection(self):
        code, _, _ = run_main(self.args(self.docs, '--build-platform',
                                        'jenkins', '--return-if-none', '99'))
        self.assertEqual(code, 99)

    def test_git_failure_returns_1(self):
        not_a_repo = self.tmp_path('empty')
        os.makedirs(not_a_repo)
        code, out, err = run_main(['--repo-path', not_a_repo, '--base',
                                   'main', '--return-if-none', '99'])
        self.assertEqual(code, 1)
        self.assertEqual(out, '')
        self.assertIn('cannot decide', err)

    def test_bad_pattern_file_returns_1(self):
        bad = self.write_file('bad.patterns', '[nonsense]\n')
        code, _, err = run_main(self.args(self.docs, '--return-if-none',
                                          '99'), patterns_file=bad)
        self.assertEqual(code, 1)
        self.assertIn('unknown section', err)

    def test_settings_are_logged_first(self):
        _, _, err = run_main(self.args(self.docs))
        self.assertEqual(
            err.splitlines()[0],
            'filter-build-and-test: build-platform=none build-system=cmake '
            'sections=[common, build-system:cmake, build-platform:none]')

    def test_long_file_lists_are_truncated(self):
        self.repo.git('checkout', '-q', '-b', 'many', self.base)
        many = self.repo.commit('many', {'src/f%02d.cc' % i: 'x\n'
                                         for i in range(25)})
        _, _, err = run_main(self.args(many))
        self.assertIn('25 of 25 changed files need a build and tests:', err)
        self.assertIn('... and 5 more', err)

    def test_junit_report_when_no_build_is_needed(self):
        junit = self.tmp_path('build', 'test_results',
                              'filter_build_and_test.xml')
        run_main(self.args(self.docs, '--junit-output', junit))
        suite = ElementTree.parse(junit).getroot()
        self.assertEqual(suite.tag, 'testsuite')
        self.assertEqual(suite.get('skipped'), '1')
        cases = suite.findall('testcase')
        self.assertEqual([case.get('name') for case in cases],
                         ['no_build_needed'])
        skipped = cases[0].find('skipped')
        self.assertIsNotNone(skipped)
        assert skipped is not None
        self.assertTrue(skipped.get('message', '').startswith(
            'No build or tests needed'))
        self.assertEqual(skipped.text, 'README.md')

    def test_no_junit_report_when_a_build_is_needed(self):
        junit = self.tmp_path('build', 'test_results',
                              'filter_build_and_test.xml')
        run_main(self.args(self.code, '--junit-output', junit))
        self.assertFalse(os.path.exists(junit))

    def test_gh_actions_annotation_and_step_summary(self):
        summary = self.write_file('summary.md', '')
        env = {'GITHUB_STEP_SUMMARY': summary}
        code, out, err = run_main(self.args(self.docs, '--build-platform',
                                            'gh-actions'), env)
        self.assertEqual(code, 0)
        self.assertEqual(out, '')
        self.assertIn(
            '\n::notice title=CI skipped::No build or tests needed', err)
        with open(summary, encoding='utf-8') as summary_file:
            content = summary_file.read()
        self.assertIn('### CI skipped', content)
        self.assertIn('- `README.md`', content)

    def test_a_file_name_cannot_start_a_log_line(self):
        self.repo.git('checkout', '-q', '-b', 'newline', self.base)
        head = self.repo.commit('newline', {
            'src/a.cc\n::warning::injected': 'x\n'})
        code, _, err = run_main(self.args(head))
        self.assertEqual(code, 0)
        self.assertIn(
            'filter-build-and-test:   src/a.cc\\x0a::warning::injected\n', err)
        self.assertEqual(
            [line for line in err.splitlines()
             if not line.startswith('filter-build-and-test: ')], [])

    def test_ignored_file_names_are_escaped_in_every_report(self):
        name = 'x\n::warning::injected\rBUILD.bazel'
        escaped = 'x\\x0a::warning::injected\\x0dBUILD.bazel'
        self.repo.git('checkout', '-q', '-b', 'newline', self.base)
        head = self.repo.commit('newline', {name: 'x\n'})
        summary = self.write_file('summary.md', '')
        junit = self.tmp_path('filter_build_and_test.xml')
        code, _, err = run_main(
            self.args(head, '--build-platform', 'gh-actions',
                      '--return-if-none', '99', '--junit-output', junit),
            {'GITHUB_STEP_SUMMARY': summary})
        self.assertEqual(code, 99)
        self.assertEqual([line for line in err.splitlines()
                          if not line.startswith('filter-build-and-test: ')],
                         ['::notice title=CI skipped::No build or tests'
                          ' needed: all 1 changed files match the ignore'
                          ' patterns'])
        self.assertIn('filter-build-and-test:   ' + escaped + '\n', err)
        with open(summary, encoding='utf-8') as summary_file:
            self.assertIn('- `%s`\n' % escaped, summary_file.read())
        skipped = ElementTree.parse(junit).getroot().find('testcase/skipped')
        assert skipped is not None
        self.assertEqual(skipped.text, escaped)


class TestArguments(unittest.TestCase):

    def test_defaults(self):
        args = filter_build_and_test.parse_args(['--base', 'main'])
        self.assertEqual(args.build_platform, 'none')
        self.assertEqual(args.build_system, 'cmake')
        self.assertEqual(args.repo_path, '.')
        self.assertIsNone(args.return_if_none)
        self.assertIsNone(args.junit_output)

    def test_return_if_none_range(self):
        for value in ('3', '125'):
            args = filter_build_and_test.parse_args(
                ['--base', 'main', '--return-if-none', value])
            self.assertEqual(args.return_if_none, int(value))
        for value in ('0', '1', '2', '126', '999', '-1', 'abc'):
            with self.subTest(value=value):
                code, _, _ = run_main(['--base', 'main',
                                       '--return-if-none=' + value])
                self.assertEqual(code, 2)

    def test_usage_errors(self):
        for argv in (['--build-platform', 'none'],
                     ['--head', 'HEAD'],
                     ['--base', '--all'],
                     ['--build-platform', 'travis', '--base', 'main'],
                     ['--build-system', 'make', '--base', 'main']):
            with self.subTest(argv=argv):
                code, out, _ = run_main(argv)
                self.assertEqual(code, 2)
                self.assertEqual(out, '')


class TestGzdevEntryPoint(TempDirTest):

    def test_filter_build_and_test_runs_without_site_packages(self):
        repo = GitRepo(self.tmp_path('repo'))
        base = repo.commit('A', {'README.md': 'a\n'})
        head = repo.commit('B', {'README.md': 'b\n'})
        # -S: no site-packages, so docopt and yaml cannot be imported
        result = subprocess.run(
            [sys.executable, '-S', GZDEV, 'filter-build-and-test',
             '--repo-path', repo.path, '--base', base, '--head', head,
             '--return-if-none', '42'],
            capture_output=True)
        self.assertEqual(result.returncode, 42, result.stderr)
        self.assertEqual(result.stdout, b'')

    @unittest.skipUnless(importlib.util.find_spec('docopt'),
                         'docopt is not installed')
    def test_unknown_command_exits_1(self):
        result = subprocess.run([sys.executable, GZDEV, 'no-such-command'],
                                capture_output=True)
        self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
    unittest.main()
