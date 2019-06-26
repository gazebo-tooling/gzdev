import unittest
import repository

class TestBase(unittest.TestCase):
    def setUp(self):
        self.config = repository.load_config_file('plugins/config/_test_repository.yaml')

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
                repository.get_repo_url('osrf','prerelease', self.config),
                'http://prerelease')

    def test_no_repo(self):
        with self.assertRaises(SystemExit) as cm:
            repository.get_repo_url('invalid_repo','invalid_type', self.config)

    def test_no_type(self):
        with self.assertRaises(SystemExit) as cm:
            repository.get_repo_url('osrf','invalid_tye', self.config)

class TestProjectNameResolution(TestBase):
    def test_direct_match(self):
        repo_name, repo_type = repository.load_project("ignition-math6", self.config)
        self.assertEqual(repo_name, 'osrf')
        self.assertEqual(repo_type, 'stable')

    def test_non_exist(self):
        with self.assertRaises(SystemExit) as cm:
            repo_name, repo_type = repository.load_project("fooooo", self.config)

    def test_regexp(self):
        repo_name, repo_type = repository.load_project("ignition-plugin", self.config)
        self.assertEqual(repo_name, 'osrf')
        self.assertEqual(repo_type, 'regexp')


if __name__ == '__main__':
    unittest.main()

