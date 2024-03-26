#
# Copyright (C) 2020 Open Source Robotics Foundation
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
"""Unittests for repository.py."""

import unittest

import repository


class TestBase(unittest.TestCase):

    def setUp(self):
        self.config = repository.load_config_file('config/_test_repository.yaml')


class TestBasicOperations(TestBase):

    def test_config_file_path(self):
        self.assertTrue(self.config)


class TestRepoKey(TestBase):

    def test_basic_ok(self):
        self.assertEqual(
            repository.get_repo_key('osrf', self.config),
            'ABC1234567890')


class TestRepo_URL(TestBase):

    def test_basic_ok(self):
        self.assertEqual(
            repository.get_repo_url('osrf', 'prerelease', self.config),
            'http://prerelease-' + repository.get_linux_distro())

    def test_no_repo(self):
        with self.assertRaises(SystemExit):
            repository.get_repo_url('invalid_repo', 'invalid_type', self.config)

    def test_no_type(self):
        with self.assertRaises(SystemExit):
            repository.get_repo_url('osrf', 'invalid_tye', self.config)


class TestProjectNameResolution(TestBase):

    def test_direct_match(self):
        project_config = \
            repository.get_first_valid_project_config('ignition-math6',
                                                      self.config,
                                                      'jammy')
        for p in repository.get_repositories_config(project_config):
            self.assertEqual(p['name'], 'osrf')
            self.assertEqual(p['type'], 'stable')

    def test_non_exist(self):
        self.assertIsNone(
            repository.get_first_valid_project_config('fooooo',
                                                      self.config,
                                                      'jammy'))

    def test_regexp(self):
        project_config = \
            repository.get_first_valid_project_config('ignition-plugin',
                                                      self.config,
                                                      'jammy')
        for p in repository.get_repositories_config(project_config):
            self.assertEqual(p['name'], 'osrf')
            self.assertEqual(p['type'], 'regexp')

    def test_precedence(self):
        project_config = \
            repository.get_first_valid_project_config('ignition-transport7',
                                                      self.config,
                                                      'jammy')
        for p in repository.get_repositories_config(project_config):
            self.assertEqual(p['name'], 'osrf')
            self.assertEqual(p['type'], 'stable')


class TestProjectInstall(TestBase):

    def test_no_distributions(self):
        repository.process_project_install('ignition-math6',
                                           self.config,
                                           'jammy',
                                           dry_run=True)

    def test_distributions(self):
        repository.process_project_install('ignition-transport7',
                                           self.config,
                                           'jammy',
                                           dry_run=True)

    def test_non_exist(self):
        with self.assertRaises(SystemExit):
            repository.process_project_install('fooooo',
                                               self.config,
                                               'jammy',
                                               dry_run=True)


if __name__ == '__main__':
    unittest.main()
