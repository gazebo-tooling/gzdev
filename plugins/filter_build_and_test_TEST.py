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


if __name__ == '__main__':
    unittest.main()
