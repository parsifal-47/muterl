#!/usr/bin/env python
"""muterl
Usage:
    muterl [--mutation=<number>]
    muterl -h | --help
Options:
    --mutation <number> Create particular mutation
    -h, --help       Show this help
"""

import re
import os
import glob
import shutil
import random
import docopt
import subprocess
import muterl_logic
import muterl_clause
import muterl_constants
from parsimonious.grammar import Grammar
import parsimonious.exceptions

default_config = {'files': "src/*.erl",
                  'mutants': 100,
                  'runner': './rebar eunit',
                  'report': 'muterl.report',
                  'backup_folder': 'muterl.backup'}

mutations = {'remove_clause': {'count': muterl_clause.clause_remove_count,
                               'mutate': muterl_clause.clause_remove}
#                               ,
#             'logic_inverse': {'count': muterl_logic.count,
#                               'mutate': muterl_logic.inverse},
#             'constant_change': {'count': muterl_constants.count,
#                                 'mutate': muterl_constants.change}
                                 }

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
    if not os.path.isfile(file):
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

def mutation(number, files, asts, mutation_matrix, runner,
            backup_folder, report, simulate = False):
    if not simulate:
        print "Running mutation #" + str(number)
    for mutation_name in mutation_matrix:
        for i in range(0, len(files)):
            if number < mutation_matrix[mutation_name][i]:
                mutations[mutation_name]['mutate'](number, asts[i], files[i])
                if not simulate:
                    if subprocess.call(runner, shell=True) == 0:
                        with open(report, 'a') as file:
                            file.write("Mutant #" + str(number) + " survived, affected file: " + files[i] + "\n")
                            file.write(subprocess.check_output("diff -c " +
                                       backup_folder + "/" + files[i] + " " +
                                       files[i] + "; true", shell = True))
                    restore(backup_folder, files[i])
                break
            else:
                number = number - mutation_matrix[mutation_name][i]

def main():
    args = docopt.docopt(__doc__, version='0.1.0')
    config = read_config()

    if subprocess.call(config["runner"], shell=True) != 0:
        print "Initial test check failed, exiting"
        exit(1)

    files = glob.glob(config["files"])
    backup(config["backup_folder"], files)
    asts = map(lex, map(contents, files))

    mutation_matrix = {}
    all_mutants = 0
    for name in mutations:
        mutation_matrix[name] = map(mutations[name]['count'], asts)
        all_mutants = all_mutants + sum(mutation_matrix[name])

    if args['--mutation'] is not None:
        print "All mutations count " + str(all_mutants) + ", mutating #" + \
              args['--mutation']
        mutation(int(args['--mutation']), files, asts, mutation_matrix,
        config["runner"], config["backup_folder"], config["report"], True)
    else:
        if all_mutants < config["mutants"]:
            print "Not enough possibilites to create " + str(config["mutants"]) + \
                  "only " + str(all_mutants) + " are available"
            config["mutants"] = all_mutants

        for i in range(0, config["mutants"]):
            mutation(random.randrange(all_mutants),
                     files, asts, mutation_matrix,
                     config["runner"], config["backup_folder"], config["report"])

if __name__ == '__main__':
        main()
