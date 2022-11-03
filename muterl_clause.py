from functools import reduce

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

def clause_no_sub(number, start, end, ast):
    if ast.children:
        if any(map(lambda x: x.expr_name[-6:] == "clause", ast.children)):
            return (-1, ast.start, ast.end) if number == 0 else (number - 1, start, end)
        return reduce(lambda t, x:clause_no_sub(t[0], t[1], t[2], x),
            ast.children, (number, start, end))
    return (number, start, end)

def clause_no(number, start, end, ast):
    return reduce(lambda t, x:clause_no_sub(t[0], t[1], t[2], x),
        ast.children, (number - 1, start, end))

def find_semicolon(number, start, end, ast):
    if number == 1 and ast.full_text[ast.start:ast.end] == ";":
        return (number, ast.start, ast.end)
    if ast.expr_name[-6:] == "clause":
        return (number + 1, start, end)
    if ast.children:
        return reduce(lambda t, x:find_semicolon(t[0], t[1], t[2], x),
            ast.children, (number, start, end))
    return (number, start, end)

def firstclause(ast):
    if ast.children:
        for x in ast.children:
            if x.expr_name[-6:] == "clause":
                return (x.start, x.end)
    return (0, 0)

def clause_remove(number, ast, filename):
    if ast.expr_name in ["function", "case", "trycatch", "lambda"]:
        clauses = sum(map(clause_count, ast.children))
        if clauses <= 1:
            return number
        if number == 0:
            (start, end) = firstclause(ast)
            (_N, start2, end2) = find_semicolon(0, 0, 0, ast)
            with open(filename, 'w') as file:
                file.write(ast.full_text[:start])
                file.write(ast.full_text[end:start2])
                file.write(ast.full_text[end2:])

        if number < clauses and number > 0:
            (_N, start, end) = clause_no(number, 0, 0, ast)
            with open(filename, 'w') as file:
                file.write(ast.full_text[:start])
                file.write(ast.full_text[end:])

        return number - clauses
    if ast.children:
        return reduce(lambda a, x: clause_remove(a, x, filename), ast.children, number)
    return number
