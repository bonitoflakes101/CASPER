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
        # Store global vars in a SymbolTable
        self.global_symbols = SymbolTable()
        self.errors = []
        self.reported_undeclared_vars = set()

        # Track function declarations to disallow duplicates/overloading
        self.declared_functions = {}

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

        # If node is a list, recurse on each item.
        if isinstance(node, list):
            for item in node:
                self.visit(item, symtable)
            return

        if isinstance(node, tuple):
            for subnode in node:
                if isinstance(subnode, (ASTNode, list, tuple)):
                    self.visit(subnode, symtable)
            return

        # If node is an ASTNode, dispatch to the correct visitor method.
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
            self.visit(node.children[0], symtable)  
        if len(node.children) > 1 and node.children[1]:
            self.visit(node.children[1], symtable)  
        if len(node.children) > 2 and node.children[2]:
    
            main_scope = SymbolTable(parent=symtable)
            self.visit(node.children[2], main_scope)

    def visit_global_dec(self, node, symtable):
        for child in node.children:
            self.visit(child, symtable)

    def visit_global_statement(self, node, symtable):
        data_type_node = node.children[0]
        ident_node = node.children[1]
        var_name = ident_node.value
        var_type = data_type_node.value

        # Add variable to the global symbols
        try:
            self.global_symbols.add(var_name, var_type)
        except SemanticError as e:
            self.errors.append(str(e))

        # If there's a third child, it might be an assignment or commas
        if len(node.children) > 2 and node.children[2]:
            tail_node = node.children[2]
            # Instead of self.visit_global_statement_tail(...)
            # rename to a private helper method
            self._process_global_statement_tail(tail_node, symtable, var_type, var_name)



    def visit_var_call(self, node, symtable):
        """
        node.value = the variable name (e.g. '$i')
        node.children = [maybe an index if it's $i[...]?]
        """
        var_name = node.value
        try:
            symtable.lookup(var_name)
        except SemanticError as e:
            # Only report once
            if var_name not in self.reported_undeclared_vars:
                self.errors.append(str(e))
                self.reported_undeclared_vars.add(var_name)

        # Also visit any children (like array indices)
        self.generic_visit(node, symtable)

    def visit_var_statement(self, node, symtable):
        """
        node.children = [data_type_node, IDENT_node, var_tail_node]
        """
        if len(node.children) < 3:
            self.generic_visit(node, symtable)
            return

        data_type_node = node.children[0]
        ident_node = node.children[1]
        var_tail_node = node.children[2]

        declared_type = getattr(data_type_node, "value", None)
        var_name = getattr(ident_node, "value", None)

     
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


        self.check_var_tail(var_tail_node, symtable, declared_type, var_name)

    def check_global_assignment(self, assigned_node, symtable, declared_type, var_name):
        """
        assigned_node: the AST node for the right-hand side
        declared_type: e.g. "int"
        var_name: e.g. "$hello"
        """

        rhs_type = self.get_expression_type(assigned_node, symtable)

        if declared_type == "bln" and rhs_type in ("int", "flt"):
            # int/float -> bln
            pass    
        elif declared_type == "int" and rhs_type in ("bln", "flt"):
            # bln/float -> int
            pass
        elif declared_type == "flt" and rhs_type in ("bln", "int"):
            # bln/int -> float
            pass
        elif rhs_type != declared_type:
            self.errors.append(
                f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
            )


    def _process_global_statement_tail(self, node, symtable, declared_type, var_name):
        # same logic you already have
        if node is None:
            return
        # 1) Recursively visit everything
        self.visit(node, symtable)
        # 2) Attempt to find an expression node
        if len(node.children) > 0:
            assigned_node = node.children[0]
            if assigned_node is not None:
                self.check_global_assignment(assigned_node, symtable, declared_type, var_name)

    def check_var_tail(self, var_tail_node, symtable, declared_type, var_name):
        if var_tail_node is None:
            return

        if hasattr(var_tail_node, "children") and var_tail_node.children:
            for child in var_tail_node.children:
                if child and getattr(child, "type", None) == "value":
                    rhs_type = self.get_expression_type(child, symtable)


                    if declared_type == "bln" and rhs_type in ("int", "flt"):
                        # int/float -> bln
                        pass
                    elif declared_type == "int" and rhs_type in ("bln", "flt"):
                        # bln/float -> int
                        pass
                    elif declared_type == "flt" and rhs_type in ("bln", "int"):
                        # bln/int -> float
                        pass
                    elif rhs_type != declared_type:
                        self.errors.append(
                            f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
                        )
                else:
                    self.visit(child, symtable)


    def get_expression_type(self, node, symtable):
        if node is None:
            return None
        if isinstance(node, ASTNode):
            for child in node.children:
                self.visit(child, symtable)  
            
            if node.type == "value":
                if node.children:
                    return self.get_expression_type(node.children[0], symtable)
            elif node.type == "expression":
                left_type = self.get_expression_type(node.children[0], symtable)
                if len(node.children) > 1 and node.children[1]:
                    tail = node.children[1]
                    if tail.children and len(tail.children) >= 2:
                        operator = tail.children[0] 
                        op_val = operator if isinstance(operator, str) else operator.value
                        right_type = self.get_expression_type(tail.children[1], symtable)
                        if op_val == "+" and (left_type == "chr" or right_type == "chr"):
                            self.errors.append("Type Error: Cannot add characters.")
                            return None
                        if left_type is None or right_type is None:
                            return None
                        if left_type == right_type:
                            return left_type
                        else:
                            return None
                return left_type


            elif node.type == "factor":
                if node.children:
                    return self.get_expression_type(node.children[0], symtable)
            elif node.type == "type_cast":
                conversion_function = node.value 
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
            elif node.type == "var_call":
                var_name = node.value
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
                    if hasattr(ret_type, "value"):
                        ret_type = ret_type.value
                    return ret_type
                else:
                    self.errors.append(f"Semantic Error: Function '{func_name}' is not declared.")
                    return None
            else:
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
        """
        node.children = [control_variable, expression, update, statements]
        This ensures the loop variable is declared in the current (function) scope,
        so $i remains visible after the loop.
        """

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



    # def visit_FUNCTION_NAME(self, node, symtable):
    #     func_name = node.value
    #     if func_name in self.declared_functions:
    #         self.errors.append(
    #             f"Semantic Error: Function '{func_name}' is already declared."
    #         )
    #     else:
    #         self.declared_functions.add(func_name)
    def visit_function_declaration(self, node, symtable):
        """
        node.children = [ret_type, FUNCTION_NAME, parameters, statements, revive]
        """
        if len(node.children) < 2:
            self.generic_visit(node, symtable)
            return

        func_name_node = node.children[1]
        func_name = func_name_node.value
        if func_name in self.declared_functions:
            self.errors.append(f"Semantic Error: Function '{func_name}' is already declared.")
        else:
            ret_type_node = node.children[0]
            ret_val = ret_type_node.value.value if hasattr(ret_type_node.value, "value") else ret_type_node.value
            ret_type = ret_val if isinstance(ret_val, str) else str(ret_val)
            if ret_type.startswith("function_"):
                ret_type = ret_type[len("function_"):]
            if ret_type == "function":
                ret_type = "void"
            parameters_node = node.children[2]
            param_types = self.extract_parameters(parameters_node)
            self.declared_functions[func_name] = (ret_type, param_types)

        func_scope = SymbolTable(parent=symtable)
        func_scope.expected_return_type = self.declared_functions[func_name][0]

        if parameters_node is not None:
            params_info = self.extract_parameters_info(parameters_node)
            for (param_name, param_type) in params_info:
                try:
                    func_scope.add(param_name, param_type)
                except SemanticError as e:
                    self.errors.append(f"Semantic Error in function '{func_name}': {str(e)}")
            self.generic_visit(node, func_scope)

    
    def extract_parameters_info(self, node):
        """
        Given a parameters node with children [data_type, IDENT, parameters_tail],
        return a list of (parameter_name, parameter_type) tuples.
        """
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
        """
        Given a parameters_tail node (created from the rule:
        parameters_tail : empty | COMMA data_type IDENT parameters_tail),
        return a list of (parameter_name, parameter_type) tuples.
        """
        params = []
        if node is None:
            return params
        if node.type == "parameters_tail" and node.children and len(node.children) >= 2:
            # Expecting children: [data_type, IDENT, parameters_tail]
            param_type = node.children[0].value
            param_name = node.children[1].value
            params.append((param_name, param_type))
            tail = node.children[2] if len(node.children) > 2 else None
            params.extend(self.extract_parameters_tail_info(tail))
        return params

    def extract_parameters(self, node):
        """
        Helper method to extract parameter types from a 'parameters' AST node.
        Returns a list of types (as strings). If no parameters, returns an empty list.
        """
        types = []
        if node is None or node.type != "parameters":
            return types
        # Expecting node.children = [data_type, IDENT, parameters_tail]
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
        """
        node.children = [FUNCTION_NAME_node, arguments_node]
        NEW: Checks that the function is declared and that the argument types match the function signature.
        """
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
        """
        Checks that the type of the expression in the revive statement
        matches the function's declared (expected) return type.
        Mimics Java behavior: if a function is void, it should not return a value.
        """
        expected = getattr(symtable, "expected_return_type", None)
        if expected == "void":
            if node.children:
                self.errors.append("Return Type Error: Void function should not return a value.")
        else:
            if node.children:
                expr_type = self.get_expression_type(node.children[0], symtable)
                if expr_type != expected:
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
