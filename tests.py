#!/usr/bin/env nosetests

import os
import imp
import subprocess
import muterl_lex
import muterl_logic
import muterl_clause
import muterl_constants

good_sources = [{'name': 'jsx',
                 'git': 'https://github.com/talentdeficit/jsx',
                 'revision': 'c61be973b95ba4cc5fd646d1f80b65b8eeba8376'},
                {'name': 'mochiweb',
                 'git': 'https://github.com/mochi/mochiweb',
                 'revision': 'aacb8f2e2fd98a729bd4f54e028c6b742bfb9dcb'}]

from nose.tools import eq_

def test_parsing():
    map(parse_source, good_sources)

def contents(filename):
    with open(filename) as file:
        return file.read()

def parse_source(source):
    path = os.getcwd()
    subprocess.check_call("git clone " + source["git"], shell=True)
    os.chdir(path + "/" + source["name"])
    subprocess.check_call("git checkout "+ source["revision"], shell=True)
    subprocess.check_call("../muterl --check-parsing", shell=True)
    os.chdir(path)

def test_removeclause():
    ast = muterl_lex.lex(("simple.erl", contents("test_data/simple.erl")))
    eq_(muterl_clause.clause_count(ast), 5)
    muterl_clause.clause_remove(0, ast, "test_data/simple_remove0.erl.res")
    muterl_clause.clause_remove(1, ast, "test_data/simple_remove1.erl.res")
    subprocess.check_call("diff test_data/simple_remove0.erl.res test_data/simple_remove0.erl", shell=True)
    subprocess.check_call("diff test_data/simple_remove1.erl.res test_data/simple_remove1.erl", shell=True)

def test_inverse():
    ast = muterl_lex.lex(("simple2.erl", contents("test_data/simple2.erl")))
    muterl_logic.inverse(0, ast, "test_data/simple2_inverse.erl.res")
    subprocess.check_call("diff test_data/simple2_inverse.erl.res test_data/simple2_inverse.erl", shell=True)

def test_constants():
    ast = muterl_lex.lex(("simple2.erl", contents("test_data/simple2.erl")))
    muterl_constants.change(0, ast, "test_data/simple2_constant.erl.res")
    subprocess.check_call("diff test_data/simple2_constant.erl.res test_data/simple2_constant.erl", shell=True)
