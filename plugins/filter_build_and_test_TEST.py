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

import os
import shutil
import tempfile
import unittest

import filter_build_and_test


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
                               '[build-platform:jenkins]\n'
                               '^\\.github/workflows/\n')
        sections = filter_build_and_test.load_patterns(path)
        self.assertEqual(sorted(sections), ['build-platform:jenkins',
                                            'build-system:cmake', 'common'])
        patterns = filter_build_and_test.active_patterns(sections, 'jenkins',
                                                         'cmake')
        self.assertEqual([p.pattern for p in patterns],
                         ['^README\\.md$', 'BUILD\\.bazel$',
                          '^\\.github/workflows/'])

    def test_sections_missing_from_the_file_are_empty(self):
        path = self.write_file('p', '[common]\n^LICENSE$\n')
        sections = filter_build_and_test.load_patterns(path)
        patterns = filter_build_and_test.active_patterns(sections,
                                                         'gh-actions', 'bazel')
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
        ('README.md', 'jenkins', 'cmake', True),
        ('README.md', 'gh-actions', 'bazel', True),
        ('Changelog.md', 'gh-actions', 'cmake', True),
        ('Migration.md', 'none', 'cmake', True),
        ('CONTRIBUTING.md', 'jenkins', 'cmake', True),
        ('LICENSE', 'jenkins', 'cmake', True),
        ('.github/CODEOWNERS', 'gh-actions', 'cmake', True),
        ('.github/workflows/ci.yml', 'jenkins', 'cmake', True),
        ('.github/workflows/ci.yml', 'gh-actions', 'cmake', False),
        ('.github/workflows/ci.yml', 'none', 'cmake', False),
        ('BUILD.bazel', 'jenkins', 'cmake', True),
        ('src/BUILD.bazel', 'gh-actions', 'cmake', True),
        ('MODULE.bazel', 'jenkins', 'cmake', True),
        ('.bazelrc', 'jenkins', 'cmake', True),
        ('.bazelversion', 'jenkins', 'cmake', True),
        ('.bcr/metadata.template.json', 'jenkins', 'cmake', True),
        ('BUILD.bazel', 'gh-actions', 'bazel', False),
        ('MODULE.bazel', 'jenkins', 'bazel', False),
        ('CMakeLists.txt', 'jenkins', 'cmake', False),
        ('src/Foo.cc', 'jenkins', 'cmake', False),
        ('include/gz/foo/Foo.hh', 'gh-actions', 'cmake', False),
        ('.github/ci/packages.apt', 'jenkins', 'cmake', False),
        ('test/README.md', 'jenkins', 'cmake', False),
        ('LICENSE.txt', 'jenkins', 'cmake', False),
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


if __name__ == '__main__':
    unittest.main()
