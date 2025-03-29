from Parser import ASTNode

class CodeGenerator:
    def __init__(self):
        self.variables = {}

    def flatten_nodes(self, nodes):
        flat = []
        if not isinstance(nodes, list):
            return [nodes]
        for item in nodes:
            if isinstance(item, list):
                flat.extend(self.flatten_nodes(item))
            else:
                flat.append(item)
        return flat

    def generate(self, ast):
        self.execute_node(ast)

    def execute_node(self, node):
        if node is None:
            return None

        if isinstance(node, list):
            results = []
            for subnode in self.flatten_nodes(node):
                res = self.execute_node(subnode)
                if res is not None:
                    results.append(res)
            return results if results else None

        if not hasattr(node, 'type'):
            return None

        if node.children:
            node.children = self.flatten_nodes(node.children)

        method_name = f"execute_{node.type}"
        executor = getattr(self, method_name, self.generic_execute)
        return executor(node)

    def generic_execute(self, node):
        result = None
        if node.children:
            for child in self.flatten_nodes(node.children):
                self.execute_node(child)
        return result

    def execute_program(self, node):
        main_function = None
        for child in self.flatten_nodes(node.children):
            if hasattr(child, 'type') and child.type == "main_function":
                main_function = child
            else:
                self.execute_node(child)

        if main_function:
            self.execute_main_function(main_function)
        else:
            print("Error: main_function node not found.")

    def execute_main_function(self, node):
        if node.children:
            statements = node.children[0]
            self.execute_node(statements)
        else:
            print("Warning: main_function node has no statements.")

    def execute_output_statement(self, node):
        if len(node.children) >= 1:
            value_node = node.children[0]
            result = self.execute_node(value_node)
            print(result)
        else:
            print("Warning: output_statement has no children.")

    def execute_value(self, node):
        if node.children:
            return self.execute_node(node.children[0])
        return None

    def execute_expression(self, node):
        left = self.execute_node(node.children[0])
        if len(node.children) > 1 and node.children[1]:
            factor_tail = node.children[1]
            if factor_tail.children and len(factor_tail.children) >= 2:
                operator_node = factor_tail.children[0]
                operator = operator_node.value if hasattr(operator_node, 'value') else operator_node
                right = self.execute_node(factor_tail.children[1])
                if operator == '+':
                    return left + right
                elif operator == '-':
                    return left - right
                elif operator == '*':
                    return left * right
                elif operator == '/':
                    return left / right
        return left

    def execute_literal(self, node):
        return node.value

    def execute_str_lit(self, node):
        return node.value.strip('"')

    def execute_var_statement(self, node):
        var_name = node.children[1].value if len(node.children) > 1 else None
        value = None
        if len(node.children) > 3:
            value = self.execute_node(node.children[3])
        if var_name is not None:
            self.variables[var_name] = value
        return None

    def execute_var_call(self, node):
        var_name = node.children[0].value if node.children else None
        return self.variables.get(var_name, None)

    def execute_assignment_statement(self, node):
        var_call_node = node.children[0] if len(node.children) > 0 else None
        var_name = None
        if var_call_node and var_call_node.children:
            var_name = var_call_node.children[0].value
        value_node = node.children[2] if len(node.children) > 2 else None
        value = self.execute_node(value_node)
        if var_name is not None:
            self.variables[var_name] = value
        return None

    def execute_function_declaration(self, node):

        if len(node.children) >= 4:
            statements = node.children[3]
            self.execute_node(statements)
        else:
            print("Error: Incomplete function declaration.")

    def execute_function_call(self, node):

        if not node.children:
            return None
        func_name_node = node.children[0]
        func_name = func_name_node.value if hasattr(func_name_node, 'value') else None

        args_node = node.children[1] if len(node.children) > 1 else None
        args = []
        if args_node and args_node.children:
            for arg in self.flatten_nodes(args_node.children):
                val = self.execute_node(arg)
                args.append(val)

        if func_name == "display":
            print(*args)
        return None


def run_code_generation(ast):
    generator = CodeGenerator()
    generator.generate(ast)
