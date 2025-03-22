# Semantics.py

from Parser import ASTNode
from Token import TokenType

class SemanticError(Exception):
    """Exception raised for semantic errors."""
    pass

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.expected_return_type = None

    def add(self, name, var_type):
        if name in self.symbols:
            raise SemanticError(f"Symbol '{name}' already declared in this scope.")
        self.symbols[name] = var_type

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        else:
            raise SemanticError(f"Symbol '{name}' not declared.")

class SemanticAnalyzer:
    def __init__(self):
        self.global_symbols = SymbolTable()
        self.errors = []
        self.reported_undeclared_vars = set()
        self.declared_functions = {}  # maps function name -> (return_type, [parameter_types])

    def analyze(self, ast):
        print("=== DEBUG: AST Structure ===")
        debug_print_ast(ast)
        print("=== END DEBUG ===\n")
        self.visit(ast, self.global_symbols)

        # Example debug note for 'str $num = 3' usage
        if "str $num" in str(ast) and not any("Cannot assign" in e for e in self.errors):
            self.errors.append(
                "[DEBUG NOTE] The analyzer did NOT detect a type mismatch for 'str $num = 3'."
            )
            self.errors.append(
                "Check your var_tail logic or expand get_expression_type if you still expect an error."
            )
        return self.errors

    def visit(self, node, symtable):
        if node is None:
            return
        if isinstance(node, list):
            for item in node:
                self.visit(item, symtable)
            return
        if isinstance(node, tuple):
            for subnode in node:
                if isinstance(subnode, (ASTNode, list, tuple)):
                    self.visit(subnode, symtable)
            return
        if not hasattr(node, "type"):
            return
        method_name = 'visit_' + node.type
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, symtable)

    def generic_visit(self, node, symtable):
        if hasattr(node, "children") and node.children:
            for child in node.children:
                self.visit(child, symtable)

    def visit_program(self, node, symtable):

        if len(node.children) > 0 and node.children[0]:
            for global_node in node.children[0]:
                self.visit(global_node, symtable)

        if len(node.children) > 1 and node.children[1]:
            for func_node in node.children[1]:
                self.visit(func_node, symtable)

        if len(node.children) > 2 and node.children[2]:
            main_scope = SymbolTable(parent=symtable)
            self.visit(node.children[2], main_scope)



    def visit_global_dec(self, node, symtable):
        for child in node.children:
            self.visit(child, symtable)

    def visit_global_statement(self, node, symtable):
        # Expecting children: [data_type, IDENT, (optional var tail)]
        data_type_node = node.children[0]
        ident_node = node.children[1]
        var_name = ident_node.value
        var_type = data_type_node.value

        try:
            self.global_symbols.add(var_name, var_type)
        except SemanticError as e:
            self.errors.append(str(e))
        if len(node.children) > 2 and node.children[2]:
            tail_node = node.children[2]
            self._process_global_statement_tail(tail_node, symtable, var_type, var_name)

    def visit_var_call(self, node, symtable):
        # In the new AST, the variable name is in the first child (type "IDENT")
        var_name = node.children[0].value
        try:
            symtable.lookup(var_name)
        except SemanticError as e:
            if var_name not in self.reported_undeclared_vars:
                self.errors.append(str(e))
                self.reported_undeclared_vars.add(var_name)
        self.generic_visit(node, symtable)

    def visit_var_statement(self, node, symtable):
        """
        node.children = [
            data_type_node,   # e.g. str
            IDENT_node,       # e.g. $hello
            None,             # from list_dec if empty
            local_var_assign  # the assignment node
        ]
        """
        if len(node.children) < 2:
            self.generic_visit(node, symtable)
            return

        data_type_node = node.children[0]
        ident_node = node.children[1]
        declared_type = data_type_node.value
        var_name = ident_node.value

        if var_name in self.global_symbols.symbols:
            self.errors.append(
                f"Semantic Error: Local variable '{var_name}' conflicts with global variable '{var_name}'."
            )
            return
        else:
            try:
                if var_name and declared_type:
                    symtable.add(var_name, declared_type)
            except SemanticError as e:
                self.errors.append(str(e))

        for child in node.children[2:]:
            if child is not None:
                self.check_var_tail(child, symtable, declared_type, var_name)


    def check_global_assignment(self, assigned_node, symtable, declared_type, var_name):
        rhs_type = self.get_expression_type(assigned_node, symtable)
        if declared_type == "bln" and rhs_type in ("int", "flt"):
            pass
        elif declared_type == "int" and rhs_type in ("bln", "flt"):
            pass
        elif declared_type == "flt" and rhs_type in ("bln", "int"):
            pass
        elif rhs_type != declared_type:
            self.errors.append(
                f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
            )

    def _process_global_statement_tail(self, node, symtable, declared_type, var_name):
        if node is None:
            return
        self.visit(node, symtable)
        if len(node.children) > 0:
            assigned_node = node.children[0]
            if assigned_node is not None:
                self.check_global_assignment(assigned_node, symtable, declared_type, var_name)

    def check_var_tail(self, var_tail_node, symtable, declared_type, var_name):
        if var_tail_node is None:
            return
        # If var_tail_node is a list, iterate over each element.
        if isinstance(var_tail_node, list):
            for item in var_tail_node:
                self.check_var_tail(item, symtable, declared_type, var_name)
            return

        # Process the node: if it has children, check each child.
        if hasattr(var_tail_node, "children") and var_tail_node.children:
            for child in var_tail_node.children:
                # Try to get the type of the child regardless of its node type.
                rhs_type = self.get_expression_type(child, symtable)
                if rhs_type is None:
                    continue  # No type deduced; skip.
                # Allow some implicit conversions for booleans and numerics if desired.
                if declared_type == "bln" and rhs_type in ("int", "flt"):
                    continue
                elif declared_type == "int" and rhs_type in ("bln", "flt"):
                    continue
                elif declared_type == "flt" and rhs_type in ("bln", "int"):
                    continue
                if rhs_type != declared_type:
                    self.errors.append(
                        f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
                    )
        else:
            # If the node doesn't have children, try to get its type directly.
            rhs_type = self.get_expression_type(var_tail_node, symtable)
            if rhs_type is not None and rhs_type != declared_type:
                self.errors.append(
                    f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
                )


    def combine_numeric_types(self, left_type, right_type):
        if left_type == "chr" or right_type == "chr":
            self.errors.append("Type Error: Cannot perform arithmetic on characters.")
            return None
    
        if left_type in ("flt", "bln") or right_type in ("flt", "bln"):
            return "flt"

        if left_type == "int" and right_type == "int":
            return "int"
        return None
    
    def get_expression_type(self, node, symtable):
        if node is None:
            return None

        if isinstance(node, ASTNode):
            # Visit child nodes first to catch undeclared vars, etc.
            for child in node.children:
                self.visit(child, symtable)

            if node.type == "value":
                # The parser sometimes wraps the RHS in a "value" node.
                if node.children:
                    return self.get_expression_type(node.children[0], symtable)
                return None

            elif node.type == "expression":
                # Usually has children like [leftSide, maybeTail].
                left_type = self.get_expression_type(node.children[0], symtable)
                if len(node.children) > 1 and node.children[1]:
                    tail = node.children[1]
                    if tail.children and len(tail.children) >= 2:
                        operator = tail.children[0]
                        op_val = operator if isinstance(operator, str) else operator.value
                        right_type = self.get_expression_type(tail.children[1], symtable)

                        if "str" in (left_type, right_type):
                            if left_type == "str" and right_type == "str" and op_val == "+":
                                return "str"
                            else:
                                self.errors.append(
                                    "Type Error: Mixing string values with non-string values "
                                    "is not allowed unless type-casted."
                                )
                                return None

                        if left_type is None or right_type is None:
                            return None

                        if left_type == right_type:
                            return left_type
                        else:
                            return self.combine_numeric_types(left_type, right_type)
                return left_type

            elif node.type == "factor":
                # If you still have "factor" nodes, handle them here.
                if node.children:
                    return self.get_expression_type(node.children[0], symtable)

            elif node.type == "type_cast":
                conversion_function = node.children[0].value
                if conversion_function == "to_int":
                    return "int"
                elif conversion_function == "to_flt":
                    return "flt"
                elif conversion_function == "to_bln":
                    return "bln"
                elif conversion_function == "to_str":
                    return "str"
                else:
                    return None

            elif node.type == "chr_lit":
                return "chr"

            elif node.type == "str_lit":
                return "str"

            elif node.type == "literal":
                val = node.value
                if isinstance(val, int):
                    return "int"
                elif isinstance(val, float):
                    return "flt"
                elif val in ("Day", "Night"):
                    return "bln"
                return "str"

            elif node.type == "factor_literal1":
                val = node.value
                if isinstance(val, int):
                    return "int"
                elif isinstance(val, float):
                    return "flt"
                elif val in ("Day", "Night"):
                    return "bln"
                return "str"

            elif node.type == "local_var_assign":
                if node.children:
                    return self.get_expression_type(node.children[0], symtable)
                return None

            elif node.type == "var_call":
                var_name = node.children[0].value
                try:
                    return symtable.lookup(var_name)
                except SemanticError as e:
                    if var_name not in self.reported_undeclared_vars:
                        self.errors.append(str(e))
                        self.reported_undeclared_vars.add(var_name)
                    return None

            elif node.type == "function_call":
                func_name = node.children[0].value
                if func_name in self.declared_functions:
                    ret_type = self.declared_functions[func_name][0]
                    return ret_type
                else:
                    self.errors.append(f"Semantic Error: Function '{func_name}' is not declared.")
                    return None

            # If we haven't handled this node type, just do a generic visit.
            self.generic_visit(node, symtable)
            return None

        elif isinstance(node, tuple):
            tag = node[0]
            if tag in ("condition_binop", "for_loop_condition_binop", "until_loop_condition_binop"):
                return "bln"
            return None

        else:
            return None



    def visit_for_loop(self, node, symtable):

        self.visit(node.children[0], symtable)
        self.visit(node.children[1], symtable)
        self.visit(node.children[2], symtable)
        self.visit(node.children[3], symtable)

    def visit_control_variable(self, node, symtable):
        if len(node.children) < 2:
            return
        data_type_node = node.children[0]
        ident_node = node.children[1]
        var_name = ident_node.value
        declared_type = data_type_node.value.lower()
        if var_name in self.global_symbols.symbols:
            self.errors.append(
                f"Semantic Error: Local variable '{var_name}' conflicts with global variable '{var_name}'."
            )
            return
        try:
            symtable.add(var_name, declared_type)
        except SemanticError as e:
            self.errors.append(str(e))
        if len(node.children) > 2 and node.children[2]:
            initializer = node.children[2]
            init_type = self.get_expression_type(initializer, symtable)
            if init_type != declared_type:
                self.errors.append(
                    f"Type Error: Cannot assign '{init_type}' to control variable '{var_name}' of type '{declared_type}'."
                )
            else:
                self.visit(initializer, symtable)

    def visit_function_declaration(self, node, symtable):
        if len(node.children) < 2:
            self.generic_visit(node, symtable)
            return

        func_name_node = node.children[1]
        func_name = func_name_node.value

        if func_name in self.declared_functions:
            self.errors.append(f"Semantic Error: Function '{func_name}' is already declared.")
        else:
            ret_type_info = node.children[0]
            if isinstance(ret_type_info, tuple):
                if ret_type_info[0] == "ret_type_void":
                    ret_type = "void"
                else:
                    ret_type = ret_type_info[1]
            elif hasattr(ret_type_info, "value"):
                ret_type = ret_type_info.value
            else:
                ret_type = str(ret_type_info)

            if isinstance(ret_type, str) and ret_type.startswith("function_"):
                ret_type = ret_type[len("function_"):]
            if ret_type == "function":
                ret_type = "void"

            parameters_node = node.children[2]
            if isinstance(parameters_node, list):
                parameters_node = ASTNode("parameters", parameters_node)

            param_types = self.extract_parameters(parameters_node)
            self.declared_functions[func_name] = (ret_type, param_types)

        func_scope = SymbolTable(parent=symtable)
        func_scope.expected_return_type = self.declared_functions[func_name][0]

        statements_node = node.children[3]
        if isinstance(statements_node, list):
            statements_node = ASTNode("statements", statements_node)
            node.children[3] = statements_node

        if isinstance(node.children[2], list):
            node.children[2] = ASTNode("parameters", node.children[2])

        params_info = self.extract_parameters_info(node.children[2])
        for (param_name, param_type) in params_info:
            try:
                func_scope.add(param_name, param_type)
            except SemanticError as e:
                self.errors.append(f"Semantic Error in function '{func_name}': {str(e)}")

        # ✅ Visit the revive statement (return) to check type match
        if len(node.children) > 4:
            revive_node = node.children[4]
            if revive_node:
                self.visit_revive(revive_node, func_scope)

        self.generic_visit(node, func_scope)



    def extract_parameters_info(self, node):
        params = []
        if node is None or node.type != "parameters":
            return params
        if node.children and len(node.children) >= 2:
            param_type = node.children[0].value
            param_name = node.children[1].value
            params.append((param_name, param_type))
            tail = node.children[2] if len(node.children) > 2 else None
            params.extend(self.extract_parameters_tail_info(tail))
        return params

    def extract_parameters_tail_info(self, node):
        params = []
        if node is None:
            return params
        if node.type == "parameters_tail" and node.children and len(node.children) >= 2:
            param_type = node.children[0].value
            param_name = node.children[1].value
            params.append((param_name, param_type))
            tail = node.children[2] if len(node.children) > 2 else None
            params.extend(self.extract_parameters_tail_info(tail))
        return params

    def extract_parameters(self, node):
        types = []
        if node is None or node.type != "parameters":
            return types
        if node.children and len(node.children) >= 2:
            types.append(node.children[0].value)
            tail = node.children[2] if len(node.children) > 2 else None
            types.extend(self.extract_parameters_tail(tail))
        return types

    def extract_parameters_tail(self, node):
        types = []
        if node is None:
            return types
        if node.type == "parameters_tail" and node.children:
            types.append(node.children[0].value)
            tail = node.children[2] if len(node.children) > 2 else None
            types.extend(self.extract_parameters_tail(tail))
        return types

    def visit_function_call(self, node, symtable):
        # children: [FUNCTION_NAME node, arguments node]
        func_name = node.children[0].value
        if func_name not in self.declared_functions:
            self.errors.append(f"Semantic Error: Function '{func_name}' is not declared.")
            return
        signature = self.declared_functions[func_name]  # (return_type, [parameter_types])
        expected_param_types = signature[1]
        args_node = node.children[1]
        arg_types = self.extract_arguments(args_node, symtable)
        if len(arg_types) != len(expected_param_types):
            self.errors.append(
                f"Argument Mismatch Error: Function '{func_name}' expects {len(expected_param_types)} arguments, got {len(arg_types)}."
            )
        else:
            for i, (arg_type, expected_type) in enumerate(zip(arg_types, expected_param_types)):
                if arg_type != expected_type:
                    self.errors.append(
                        f"Type Error: Argument {i+1} of function '{func_name}' expected type '{expected_type}', got '{arg_type}'."
                    )
        self.generic_visit(node, symtable)

    def extract_arguments(self, node, symtable):
        arg_types = []
        if node is None or node.type != "arguments":
            return arg_types
        if node.children:
            first_arg_type = self.get_expression_type(node.children[0], symtable)
            if first_arg_type is not None:
                arg_types.append(first_arg_type)
            if len(node.children) > 1 and node.children[1] is not None:
                arg_types.extend(self.extract_arg_tail(node.children[1], symtable))
        return arg_types

    def extract_arg_tail(self, node, symtable):
        arg_types = []
        if node is None:
            return arg_types
        if hasattr(node, "children") and node.children:
            first_arg = node.children[0]
            arg_type = self.get_expression_type(first_arg, symtable)
            if arg_type is not None:
                arg_types.append(arg_type)
            if len(node.children) > 1 and node.children[1] is not None:
                arg_types.extend(self.extract_arg_tail(node.children[1], symtable))
        return arg_types

    def visit_revive(self, node, symtable):
        expected = getattr(symtable, "expected_return_type", None)
        if expected == "void":
            if node.children:
                self.errors.append("Return Type Error: Void function should not return a value.")
        else:
            if node.children:
                expr_type = self.get_expression_type(node.children[0], symtable)

                # Allow exact match
                if expr_type == expected:
                    return

                # Implicit conversion rules
                allowed_implicit_conversions = {
                    ("int", "flt"),   # int → float
                    ("flt", "int"),   # float → int
                    ("bln", "flt"),   # bool → float
                    ("flt", "bln"),   # float → bool
                    ("int", "bln"),   # int → bool
                    ("bln", "int"),   # bool → int
                }

                if (expr_type, expected) in allowed_implicit_conversions:
                    return

                self.errors.append(
                    f"Return Type Error: Function expects return type '{expected}', but got '{expr_type}'."
                )
            else:
                self.errors.append("Return Type Error: No return expression provided.")



def debug_print_ast(node, indent=0):
    if node is None:
        print(" " * indent + "None")
        return
    if isinstance(node, list):
        for item in node:
            debug_print_ast(item, indent)
        return
    if not hasattr(node, "type"):
        print(" " * indent + f"Non-AST node: {node}")
        return
    line = f"{node.type}"
    if node.value is not None:
        line += f" (value={node.value})"
    print(" " * indent + line)
    if hasattr(node, "children") and node.children:
        for child in node.children:
            debug_print_ast(child, indent + 2)

def run_semantic_analysis(ast):
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)
    return errors
