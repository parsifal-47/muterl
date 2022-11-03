from parsimonious.grammar import Grammar
import parsimonious.exceptions

def lex(pair):
    (filename, text) = pair
    grammar = Grammar("""\
    entry = _ (form _ "." _)*
    form = (("-spec" / "-callback") _ atom _ typed_vals _ "->" _ expression _ guard?)
           / ("-define" _ "(" _ function_call _ "," _ expression _ ")" _)
           / ("-" atom _ typed_vals)
           / ("-" atom _ attr_vals) / ("-" atom _) / function
    typed_vals = ("()" _ ) / ("(" _ typed_val _ ("," _ typed_val)* _ ")") / ( typed_val _ )
    typed_val = expression _ ("::" _ expression _)?
    attr_vals = ("(" _ expression_list ")") / (expression)

    expression_list = expression _ ("," _ expression _ )*

    function = function_clause _ (";" _ function_clause _)*
    function_clause = function_head _ guard? "->" _ expression_list
    function_head = atom _ function_args
    guard = "when" _ guard_body
    guard_body = expression _ (guard_op _ expression _)*
    guard_op = "orlese" / "or" / "andalso" / "and" / "," / ";"

    expression = ("begin" _ expression_list "end" _ )
           / ("(" _ expression _ ")" _ (postfix_operation _)*
             (binary_operator _ expression _)* )
           / ("not" _ expression _) / ("-" _ expression )
           / ( value _ (postfix_operation _)* (binary_operator _ expression _)* )

    binary_operator = "++" / "-" / "*" / "/=" / "/" / "+" / "=:=" / "=/=" / "=="
                    / "=<" / "=" / "|" / ">=" / ">" / "<" / "orelse"
                    / "andalso" / "or" / "div" / "rem" / "bxor" / "and"
                    / "bsl" / "bsr" / "bor" / "band" / "!" / "::" / ".."

    postfix_operation = function_args / record_field / record_update

    value = function_ref / record_field
          / if / case / receive / fun_type / lambda / trycatch / catch
          / function_call / boolean / atom / char / binary_comprehension
          / list_comprehension / list / tuple / map / string / macros
          / binary / number / identifier / record / triple_dots

    macros = "?" (atom / identifier) function_args?

    record_update = record

    function_ref = "fun" _ ((atom / macros) _ ":")? atom "/" ~"[0-9]*" _

    record_field = "#" atom "." atom _

    function_call = ((atom / identifier) function_args)
                  / ((atom / identifier / macros) ":" (atom / identifier) function_args)

    function_args = ("()" _) / ("(" _ expression_list ")" _)

    triple_dots = "..." _

    fun_type = "fun" _ "(" _ function_args _ "->" _ expression _ ")" _
    lambda = "fun" _ lambda_clause (";" _ lambda_clause)* "end"
    lambda_clause = function_args _ guard? "->" _ expression_list

    if = ("if" _ if_clause (";" _ if_clause)* "end" _)
    if_clause = guard_body _ "->" _ expression_list _

    receive = "receive" _ (case_clause (";" _ case_clause)*)?
              ("after" _ expression _ "->" _ expression_list)? "end" _

    case = "case" _ expression _ "of" _ case_clause (";" _ case_clause)* "end" _
    case_clause = expression _ guard? "->" _ expression_list _

    catch = "catch" _ expression _

    trycatch = ("try" _ expression _ "of" _
                case_clause (";" _ case_clause)*
               "catch" _ catch_body catch_after? "end" _)
             / ("try" _ expression_list ("catch" _ catch_body)? catch_after? "end" _)

    catch_after = "after" _ expression_list
    catch_body = expression _ (":" _ expression _)? "->" _ expression_list (";" _ catch_body)*

    atom = ~"[a-z][0-9a-zA-Z_]*" / ("'" ~r"(\\\\'|[^'])*" "'")
    identifier = ~"[A-Z_][0-9a-zA-Z_]*"
    _ = ~r"\s*" (~r"%[^\\r\\n]*\s*")*
    list = ("[" _ expression_list ("|" _ expression _)? "]" _) / ("[" _ "]" _)
    list_comprehension = "[" _ comprehension_body "]" _
    binary_comprehension = "<<" _ comprehension_body ">>" _
    comprehension_body = expression _ "||" _ expression _ (("," / "<-" / "<=") _ expression _)* _
    tuple = ("{" _ expression_list "}" _) / ("{" _ "}" _)
    map   = ("#{" _ keyvalue (_ "," _ keyvalue)* _ "}" _) / ("#{" _ "}" _)
    record =("#" atom "{" _ expression (_ "," _ expression)* _ "}" _)
          / ("#" atom "{" _ "}" _)
    char = ("$\\\\" ~"[0-9]{3}" _) / ("$" "\\\\"? (~"(?s).") _)
    keyvalue = value _ "=>" _ expression _
    string = ('"' ~r'(\\\\.|[^"])*' '"' _)+
    binary = ("<<" _ ">>" _) / ("<<" _ binary_part ("," _ binary_part)* ">>" _)
    binary_part = expression _ (":" binary_size _)? ("/" _ typespecifier _)?
    binary_size = (_ value) / ("(" _ expression ")")
    typespecifier = ~"[a-z][0-9a-z\\\\-:]*"
    boolean = "true" / "false"
    number = ~r"\-?[0-9]+\#[0-9a-zA-Z]+" / ~r"\-?[0-9]+(\.[0-9]+)?((e|E)(\-|\+)?[0-9]+)?"
    """)
    try:
        return grammar.parse(text)
    except parsimonious.exceptions.ParseError as e:
        print("Parsing for " + filename + " failed, reason: " + str(e))
        print("Skipping this file")
        return None
