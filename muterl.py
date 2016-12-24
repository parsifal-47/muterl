#!/usr/bin/env python

import re
import os
import glob
import shutil
import random
import subprocess
from parsimonious.grammar import Grammar
import parsimonious.exceptions

default_config = {'files': "src/*.erl",
                  'mutants': 100,
                  'runner': './rebar eunit',
                  'backup_folder': 'muterl.backup'}

class ParseError(Exception):
    pass

def lex(text):
    grammar = Grammar("""\
    entry = _ (form _ "." _)*
    form = ("-spec" _ atom typed_vals _ "->" _ expression _ )
           / ("-define" _ "(" _ function_call _ "," _ expression _ ")" _)
           / ("-" atom _ typed_vals)
           / ("-" atom _ attr_vals) / ("-" atom _) / function
    typed_vals = ("()" _ ) / ("(" _ typed_val _ ("," _ typed_val)* _ ")") / ( typed_val _ )
    typed_val = expression _ ("::" _ expression _)?
    attr_vals = ("(" _ expression_list ")") / (expression)

    expression_list = expression _ ("," _ expression _ )*

    function = function_clause _ (";" _ function_clause _)*
    function_clause = function_head _ guard? "->" _ expression_list
    function_head = atom function_args
    guard = "when" _ expression _ (guard_op _ expression _)*
    guard_op = "orlese" / "or" / "andalso" / "and" / "," / ";"

    expression = ("begin" _ expression_list "end" _ )
           / ("(" _ expression _ ")" _ "(" expression_list ")"
             _ (binary_operator _ expression _)* )
           / ("(" _ expression _ ")" _ (binary_operator _ expression _)* )
           / ("!" expression _) / ( value _ binary_operator _ expression _)
           / (value _)

    binary_operator = "++" / "-" / "*" / "/" / "+" / "=:=" / "=/=" / "=="
                    / "=<" / "=" / "|" / ">=" / ">" / "<" / "andalso" / "orelse"

    value =  record_update / record_field / function_ref
          / if / case / fun_type / lambda / trycatch
          / function_call / boolean / atom / char
          / list_comprehension / list / tuple / map / string / macros
          / binary / number / identifier / record / triple_dots

    macros = "?" (atom / identifier) function_args?

    record_update = identifier record

    function_ref = "fun" _ ((atom / macros) _ ":")? atom "/" ~"[0-9]*" _

    record_field = identifier "#" atom "." atom _

    function_call = ((atom / identifier) function_args)
                  / ((atom / identifier) ":" atom function_args)

    function_args = ("()" _) / ("(" _ expression_list ")" _)

    triple_dots = "..." _

    fun_type = "fun" _ "(" _ function_args _ "->" _ expression _ ")" _
    lambda = "fun" _ lambda_clause (";" _ lambda_clause)* "end"
    lambda_clause = function_args _ guard? "->" _ expression_list

    if = ("if" _ if_clause (";" _ if_clause)* "end" _)
    if_clause = expression _ "->" _ expression_list _

    case = "case" _ expression _ "of" _ case_clause (";" _ case_clause)* "end" _
    case_clause = expression _ guard? "->" _ expression_list _

    trycatch = ("try" _ expression _ "of" _
                case_clause (";" _ case_clause)*
               "catch" _ catch_body "end" _)
             / ("try" _ expression_list "catch" _ catch_body "end" _)

    catch_body = expression _ ":" _ expression _ "->" _ expression_list

    atom = ~"[a-z][0-9a-zA-Z_]*" / ("'" ~"[^']*" "'")
    identifier = ~"[A-Z_][0-9a-zA-Z_]*"
    _ = ~"\s*" (~"%[^\\r\\n]*\s*")*
    list = ("[" _ expression_list ("|" _ expression _)? "]" _) / ("[" _ "]" _)
    list_comprehension = "[" _ expression _ "||" _ expression _ (("," / "<-" / "<=") _ expression _)* _ "]" _
    tuple = ("{" _ expression_list "}" _) / ("{" _ "}" _)
    map   = ("#{" _ keyvalue (_ "," _ keyvalue)* _ "}" _) / ("#{" _ "}" _)
    record =("#" atom "{" _ expression (_ "," _ expression)* _ "}" _)
          / ("#" atom "{" _ "}" _)
    char = "$" "\\\\"? (~".") _
    keyvalue = value _ "=>" _ expression _
    string = '"' ~r'(\\\\.|[^"])*' '"'
    binary = ("<<" _ ">>" _) / ("<<" _ binary_part ("," _ binary_part)* ">>" _)
    binary_part = expression _ (":" _ value _)? ("/" _ atom _)?
    boolean = "true" / "false"
    number = ~"\-?[0-9]+\#[0-9a-zA-Z]+" / ~"\-?[0-9]+(\.[0-9]+)?(e\-?[0-9]+)?"
    """)
    try:
        return grammar.parse(text)
    except parsimonious.exceptions.ParseError as e:
        raise ParseError(e)

def reduce_config(ast):
    if ast.expr_name == "number":
        return [int(ast.text)]
    elif ast.expr_name == "string":
        return [ast.text[1:-1]] # "something"
    elif ast.expr_name == "atom":
        return [ast.text]

    sub = reduce(lambda a, x: a + reduce_config(x), ast.children, [])
    if ast.expr_name == "term":
        return [tuple(sub)]
    elif ast.expr_name == "entry":
        return dict(sub)

    return sub

def read_config(file = 'muterl.conf'):
    if !os.path.isfile(file):
        return default_config

    config_grammar = Grammar("""\
    entry = _ (term "." _)*
    term = "{" _ atom _ "," _ (string / number) _ "}"
    atom = ~"[a-z][0-9a-zA-Z_]*"
    string = '"' ~r'(\\\\"|[^"])*' '"'
    number = ~"[0-9]+"
    _ = ~"\s*" (~"%[^\\r\\n]*\s*")*
    """)
    with open(file) as config:
        default_config.update(
            reduce_config(config_grammar.parse(config.read())))
        return default_config

def backup(folder, files):
    for file in files:
        if not os.path.exists(os.path.dirname(folder + "/" + file)):
            os.makedirs(os.path.dirname(folder + "/" + file))
        shutil.copyfile(file, folder + "/" + file)

def restore(folder, file):
    shutil.copyfile(folder + "/" + file, file)

def contents(filename):
    with open(filename) as file:
        return file.read()

def clause_count(ast):
    if ast.expr_name[-6:] == "clause":
        return 1
    if ast.children:
        return sum(map(clause_count, ast.children))
    return 0

def clause_remove_count(ast):
    if ast.expr_name in ["function", "case", "trycatch", "lambda"]:
        clauses = sum(map(clause_count, ast.children))
        return clauses if clauses > 1 else 0
    if ast.children:
        return sum(map(clause_remove_count, ast.children))
    return 0

def clause_no(number, start, end, ast):
    if ast.expr_name[-6:] == "clause":
        return (-1, ast.start, ast.end) if number == 0 else (number - 1, start, end)
    if ast.children:
        return reduce(lambda (a, b, c), x:clause_no(a, b, c, x),
            ast.children, (number, start, end))
    return (number, start, end)

def find_semicolon(number, start, end, ast):
    if number == 1 and ast.full_text[ast.start:ast.end] == ";":
        return (number, ast.start, ast.end)
    if ast.expr_name[-6:] == "clause":
        return (number + 1, start, end)
    if ast.children:
        return reduce(lambda (a, b, c), x:find_semicolon(a, b, c, x),
            ast.children, (number, start, end))
    return (number, start, end)

def clause_remove(number, ast, filename):
    if ast.expr_name in ["function", "case", "trycatch", "lambda"]:
        clauses = sum(map(clause_count, ast.children))
        if clauses <= 1:
            return number
        if number == 0:
            (_N, start, end) = clause_no(number, 0, 0, ast)
            (_N, start2, end2) = find_semicolon(0, 0, 0, ast)
            with open(filename, 'w') as file:
                file.write(ast.full_text[:start-1])
                file.write(ast.full_text[end+1:start2-1])
                file.write(ast.full_text[end2+1:])

        if number < clauses and number > 0:
            (_N, start, end) = clause_no(number, 0, 0, ast)
            with open(filename, 'w') as file:
                file.write(ast.full_text[:start-1])
                file.write(ast.full_text[end+1:])

        return number - clauses
    if ast.children:
        return reduce(lambda a, x: clause_remove(a, x, filename), ast.children, number)
    return number

def mutation(number, files, asts, possible_mutants, runner, backup_folder):
    print "Running mutation #" + str(number)
    for i in range(0, len(files)):
        if number < possible_mutants[i]:
            clause_remove(number, asts[i], files[i])
            if subprocess.call(runner, shell=True) == 0:
                print "Mutant survived, affected file: " + files[i]
                print "Diff:"
                subprocess.call(["diff", files[i],
                        backup_folder + "/" + files[i]], shell = True)
            restore(backup_folder, files[i])
            break
        else:
            number = number - possible_mutants[i]

def main():
    config = read_config()

    if subprocess.call(config["runner"], shell=True) != 0:
        print "Initial test check failed, exiting"
        exit(1)

    files = glob.glob(config["files"])
    backup(config["backup_folder"], files)
    asts = map(lex, map(contents, files))
    possible_mutants = map(clause_remove_count, asts)
    all_mutants = sum(possible_mutants)

    if all_mutants < config["mutants"]:
        print "Not enough possibilites to create " + str(config["mutants"]) + \
              "only " + str(all_mutants) + " are available"
        config["mutants"] = all_mutants

    for i in range(0, config["mutants"]):
        mutation(random.randrange(all_mutants),
                 files, asts, possible_mutants,
                 config["runner"], config["backup_folder"])

if __name__ == '__main__':
        main()
