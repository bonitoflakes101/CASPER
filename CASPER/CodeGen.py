# CodeGen.py

from Parser import ASTNode

class CodeGenerator:
    def __init__(self):
        self.variables = {}

    def generate(self, ast):
        self.execute_node(ast)

    def execute_node(self, node):
        if node is None:
            return

        method_name = f"execute_{node.type}"
        executor = getattr(self, method_name, self.generic_execute)
        return executor(node)

    def generic_execute(self, node):
        if node.children:
            for child in node.children:
                self.execute_node(child)

    def execute_program(self, node):
        for child in node.children:
            self.execute_node(child)

    def execute_function_call(self, node):
        function_name = node.children[0].value
        args = [self.execute_node(arg) for arg in node.children[1].children]
        
        if function_name == "out":
            print(*args)

    def execute_literal(self, node):
        return node.value

    def execute_str_lit(self, node):
        return node.value.strip('"')

    def execute_var_statement(self, node):
        data_type = node.children[0].value
        var_name = node.children[1].value
        value_node = node.children[3] if len(node.children) > 3 else None
        value = self.execute_node(value_node) if value_node else None

        self.variables[var_name] = value

    def execute_var_call(self, node):
        var_name = node.children[0].value
        return self.variables.get(var_name, None)

    def execute_assignment_statement(self, node):
        var_name = node.children[0].children[0].value
        value_node = node.children[2]
        value = self.execute_node(value_node)

        self.variables[var_name] = value

    def execute_expression(self, node):
        left = self.execute_node(node.children[0])
        if len(node.children) > 1 and node.children[1]:
            operator = node.children[1].children[0].value
            right = self.execute_node(node.children[1].children[1])

            if operator == '+':
                return left + right
            elif operator == '-':
                return left - right
            elif operator == '*':
                return left * right
            elif operator == '/':
                return left / right

        return left

# Entry-point
def run_code_generation(ast):
    generator = CodeGenerator()
    generator.generate(ast)
