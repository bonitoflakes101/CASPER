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

        # NEW: If node is a tuple (e.g. ("condition_binop", left, op, right)),
        # then recurse into each item. Some may be strings/operators, others may be ASTNodes.
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

        try:
            self.global_symbols.add(var_name, var_type)
        except SemanticError as e:
           
            self.errors.append(str(e))

       
        if len(node.children) > 2 and node.children[2]:
            self.visit(node.children[2], symtable)

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

  
    def check_var_tail(self, var_tail_node, symtable, declared_type, var_name):
        if var_tail_node is None:
            return

        if hasattr(var_tail_node, "children") and var_tail_node.children:
            for child in var_tail_node.children:
                if child and getattr(child, "type", None) == "value":
                    rhs_type = self.get_expression_type(child, symtable)
                    if rhs_type and declared_type and rhs_type != declared_type:
                        self.errors.append(
                            f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
                        )
                else:
                    self.visit(child, symtable)

    def get_expression_type(self, node, symtable):
        if node is None:
            return None
        if isinstance(node, ASTNode):
            node_type = node.type

            if node_type == "value":
                if node.children:
                    return self.get_expression_type(node.children[0], symtable)

            if node_type == "factor":
                if node.children:
                    return self.get_expression_type(node.children[0], symtable)

            # Check our new literal types first.
            if node_type == "chr_lit":
                return "chr"
            if node_type == "str_lit":
                return "str"
            if node_type == "literal":
                val = node.value
                if isinstance(val, int):
                    return "int"
                if val in ("Day", "Night"):
                    return "bln"
              
             
                return "str"

            if node_type == "var_call":
                var_name = node.value
                try:
                    return symtable.lookup(var_name)
                except SemanticError:
                    return None

            # NEW: For function calls, return the declared (normalized) return type.
            if node_type == "function_call":
                func_name = node.children[0].value
                if func_name in self.declared_functions:
                    ret_type = self.declared_functions[func_name][0]
                    if hasattr(ret_type, "value"):
                        ret_type = ret_type.value
                    return ret_type
                else:
                    self.errors.append(f"Semantic Error: Function '{func_name}' is not declared.")
                    return None
                
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
                # Continue to process initializer if needed.
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
        Extracts the function signature and checks for duplicate declarations.
        """
        if len(node.children) < 2:
            self.generic_visit(node, symtable)
            return

        func_name_node = node.children[1]
        func_name = func_name_node.value
        if func_name in self.declared_functions:
            self.errors.append(f"Semantic Error: Function '{func_name}' is already declared.")
        else:
            # NEW: Extract and normalize the return type as a plain string.
            ret_type_node = node.children[0]
            ret_val = ret_type_node.value.value if hasattr(ret_type_node.value, "value") else ret_type_node.value
            ret_type = ret_val if isinstance(ret_val, str) else str(ret_val)
            if ret_type.startswith("function_"):
                ret_type = ret_type[len("function_"):]
            parameters_node = node.children[2]
            param_types = self.extract_parameters(parameters_node)
            # Store the normalized return type (e.g. "int") rather than an ASTNode.
            self.declared_functions[func_name] = (ret_type, param_types)

        # NEW: Create a new scope for the function body.
        func_scope = SymbolTable(parent=symtable)
        func_scope.expected_return_type = self.declared_functions[func_name][0]
        self.generic_visit(node, func_scope)

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
    
    # NEW: Recursively extract parameter types from a 'parameters_tail' AST node.
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

    # NEW: Helper method to extract argument types from an 'arguments' AST node.
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

    # NEW: Recursively extract argument types from an 'arg_tail' AST node.
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

    # NEW: Visitor for the revive node.
    def visit_revive(self, node, symtable):
        """
        Checks that the type of the expression in the revive statement
        matches the function's declared (expected) return type.
        """
        expected = getattr(symtable, "expected_return_type", None)
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
