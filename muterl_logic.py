from functools import reduce

good_ops = {'+': '-', '-': '+', '=<': '==', '>=': '==',
            '==': '=/=', '=/=': '==', '<':'>', '>': '<'}

def count(ast):
    if ast.expr_name == "binary_operator":
        return 1 if ast.text in good_ops else 0
    if ast.children:
        return sum(map(count, ast.children))
    return 0

def inverse(number, ast, filename):
    if ast.expr_name == "binary_operator":
        if ast.text not in good_ops:
            return number

        if number == 0:
            with open(filename, 'w') as file:
                file.write(ast.full_text[:ast.start])
                file.write(good_ops[ast.text])
                file.write(ast.full_text[ast.end:])

        return number - 1
    if ast.children:
        return reduce(lambda a, x: inverse(a, x, filename), ast.children, number)
    return number
