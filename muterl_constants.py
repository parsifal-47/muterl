from functools import reduce

def count(ast):
    if ast.expr_name in ["number", "boolean"]:
        return 1
    if ast.children:
        return sum(map(count, ast.children))
    return 0

def change(number, ast, filename):
    if ast.expr_name in ["number", "boolean"]:

        if number == 0:
            with open(filename, 'w') as file:
                file.write(ast.full_text[:ast.start])
                file.write(mutate_constant(ast.expr_name, ast.text))
                file.write(ast.full_text[ast.end:])

        return number - 1
    if ast.children:
        return reduce(lambda a, x: change(a, x, filename), ast.children, number)
    return number

def mutate_constant(type, text):
    if type == "boolean":
        return "false" if text == "true" else "false"

    if "." in text:
        return str(float(text) * 10)

    if "#" in text:
        (a, b) = text.split("#", 2)
        return str(int(b, int(a)) + 1)

    return str(int(text) + 1)
