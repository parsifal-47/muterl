#!/usr/bin/env python3

import os
import shutil
import subprocess
import unittest
import muterl_lex
import muterl_logic
import muterl_clause
import muterl_constants

good_sources = [{'name': 'jsx',
                 'git': 'https://github.com/talentdeficit/jsx',
                 'revision': 'c61be973b95ba4cc5fd646d1f80b65b8eeba8376'},
                {'name': 'mochiweb',
                 'git': 'https://github.com/mochi/mochiweb',
                 'revision': 'aacb8f2e2fd98a729bd4f54e028c6b742bfb9dcb'},
                {'name': 'poolboy',
                 'git': 'https://github.com/devinus/poolboy',
                 'revision': 'd378f996182daa6251ad5438cee4d3f6eb7ea50f'},
#                {'name': 'lfe',
#                 'git': 'https://github.com/rvirding/lfe',
#                 'revision': 'c05fa59ecf51e345069787476b9e699e42be8cf6'}
                 ]

TEST_TEMP_DIR = 'test_tmp'
TEST_DATA_DIR = 'test_data'

def contents(filename):
    with open(filename) as file:
        return file.read()

def parse_source(source):
    path = os.getcwd()
    subprocess.check_call("git clone " + source["git"] + ' ' + TEST_TEMP_DIR + '/' + source["name"], shell=True)
    os.chdir(path + '/' + TEST_TEMP_DIR + '/' + source["name"])
    subprocess.check_call("git checkout "+ source["revision"], shell=True)
    try:
        subprocess.check_call("../../muterl --check-parsing", shell=True)
    finally:
        os.chdir(path)

class TestMutations(unittest.TestCase):
    def setUp(self) -> None:
        if os.path.isdir(TEST_TEMP_DIR):
            shutil.rmtree(TEST_TEMP_DIR)
        os.mkdir(TEST_TEMP_DIR)
        return super().setUp()

    def test_parsing(self):
        list(map(parse_source, good_sources))

    def test_removeclause(self):
        ast = muterl_lex.lex(('simple.erl', contents("test_data/simple.erl")))
        self.assertEqual(muterl_clause.clause_count(ast), 5)
        muterl_clause.clause_remove(0, ast, TEST_TEMP_DIR + "/simple_remove0.erl.res")
        muterl_clause.clause_remove(1, ast, TEST_TEMP_DIR + "/simple_remove1.erl.res")
        subprocess.check_call('diff ' + TEST_TEMP_DIR + '/simple_remove0.erl.res ' + TEST_DATA_DIR + '/simple_remove0.erl', shell=True)
        subprocess.check_call('diff ' + TEST_TEMP_DIR + '/simple_remove1.erl.res ' + TEST_DATA_DIR + '/simple_remove1.erl', shell=True)

    def test_inverse(self):
        ast = muterl_lex.lex(('simple2.erl', contents(TEST_DATA_DIR + '/simple2.erl')))
        muterl_logic.inverse(0, ast, TEST_TEMP_DIR + '/simple2_inverse.erl.res')
        subprocess.check_call('diff  ' + TEST_TEMP_DIR + '/simple2_inverse.erl.res ' + TEST_DATA_DIR + '/simple2_inverse.erl', shell=True)

    def test_constants(self):
        ast = muterl_lex.lex(('simple2.erl', contents(TEST_DATA_DIR + '/simple2.erl')))
        muterl_constants.change(0, ast, TEST_TEMP_DIR + '/simple2_constant.erl.res')
        subprocess.check_call('diff ' + TEST_TEMP_DIR + '/simple2_constant.erl.res ' + TEST_DATA_DIR + '/simple2_constant.erl', shell=True)

if __name__ == '__main__':
    unittest.main()