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
        
allowed_implicit_conversions = {
    ("int", "flt"),
    ("flt", "int"),
    ("bln", "flt"),
    ("flt", "bln"),
    ("int", "bln"),
    ("bln", "int"),
}
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

        if len(node.children) < 2:
            self.generic_visit(node, symtable)
            return

        # 1) Extract basic info
        data_type_node = node.children[0]
        ident_node = node.children[1]
        base_type = data_type_node.value
        var_name = ident_node.value
        list_dec = node.children[2]  

        # 2) Distinguish 1D vs. 2D
        if list_dec is not None:
            if list_dec.children and list_dec.children[0] is not None:
                declared_type = f"{base_type}[][]"
            else:
                declared_type = f"{base_type}[]"
        else:
            declared_type = base_type

        # 3) Print debug info
        print(f"DEBUG: Declaring variable {var_name} with type {declared_type}")

        # 4) Check local vs. global conflict
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

        for child in node.children[3:]:
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
        # If the variable is declared as a list (e.g. "int[]", "int[][]", "flt[]", "bln[][]", etc.)
        if '[' in declared_type:
            rhs_type = self.get_expression_type(var_tail_node, symtable)
            print(f"DEBUG: {var_name} declared as {declared_type}, initializer type = {rhs_type}")

            # 1) If the initializer has no type, or is not recognized as a list, mismatch
            if rhs_type is None or '[' not in rhs_type:
                self.errors.append(
                    f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
                )
                return

            # 2) Check dimension match by counting how many "[]" pairs each type has
            declared_dim = declared_type.count("[]")   # e.g. "int[][]" -> 2
            rhs_dim = rhs_type.count("[]")            # e.g. "int[]"   -> 1
            if declared_dim != rhs_dim:
                # Keep your original dimension mismatch error
                self.errors.append(
                    f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
                )
                return

            # 3) Strip off the "[]" pairs to find the base types (e.g. "int[][]" -> "int")
            declared_base = declared_type.replace("[]", "")
            rhs_base = rhs_type.replace("[]", "")

            # 4) If base types match exactly (e.g. "int" vs. "int"), no error
            if declared_base == rhs_base:
                return

            # 5) Otherwise, apply your “C‐style” numeric/boolean conversions:
            #    int -> float => add .0
            #    float -> int => truncate
            #    bln -> float => 1.0 or 0.0
            #    float -> bln => 0.0 => false, else true
            #    int -> bln => 0 => false, else true
            #    bln -> int => true => 1, false => 0

            if declared_base == "int" and rhs_base in ("flt", "bln"):
                return
            if declared_base == "flt" and rhs_base in ("int", "bln"):
                return
            if declared_base == "bln" and rhs_base in ("int", "flt"):
                return

            # 6) If none of the above, we raise a type mismatch
            self.errors.append(
                f"Type Error: Cannot assign '{rhs_type}' to variable '{var_name}' of type '{declared_type}'."
            )
            return

        # If it's not a list type, fall through to your existing scalar logic:
        if var_tail_node is None:
            return

        if isinstance(var_tail_node, list):
            for item in var_tail_node:
                self.check_var_tail(item, symtable, declared_type, var_name)
            return

        if hasattr(var_tail_node, "children") and var_tail_node.children:
            for child in var_tail_node.children:
                rhs_type = self.get_expression_type(child, symtable)
                if rhs_type is None:
                    continue
                # The same numeric/boolean conversions for scalars:
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

        # If not an ASTNode, bail out
        for child in node.children:
                self.visit(child, symtable)

        if node.type == "value":
            if node.children:
                return self.get_expression_type(node.children[0], symtable)
            return None

        elif node.type == "expression":
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
                                "Type Error: Mixing string values with non-string values is not allowed unless type-casted."
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
            if node.children:
                return self.get_expression_type(node.children[0], symtable)

        elif node.type == "type_cast":
            conv_function = node.value
            if conv_function is None:
                return None

            conv_function = conv_function.lower()

            if node.children and len(node.children) > 0:
                self.get_expression_type(node.children[0], symtable)

            if conv_function in ("convert_to_int", "to_int"):
                return "int"
            elif conv_function in ("convert_to_flt", "to_flt"):
                return "flt"
            elif conv_function in ("convert_to_bln", "to_bln"):
                return "bln"
            elif conv_function in ("convert_to_str", "to_str"):
                return "str"
            else:
                return None

        elif node.type == "chr_lit":
            return "chr"

        elif node.type == "str_lit":
            return "str"

        elif node.type == "list_value":
            return self.get_list_literal_type(node, symtable)

        elif node.type == "literal":
            print("DEBUG in literal:", node.value, type(node.value))
            val = node.value
            if isinstance(val, int):
                return "int"
            elif isinstance(val, float):
                return "flt"
            elif val in ("Day", "Night"):
                return "bln"
            return "str"
        
        elif node.type == "literal_element":
            if node.children:
                return self.get_expression_type(node.children[0], symtable)
            return None
    
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

        elif node.type in ("neg_int", "factor_neg_int"):
            return "int"
        elif node.type in ("neg_flt", "factor_neg_flt"):
            return "flt"

        elif node.type in ("var_postfix", "factor_var_postfix"):
            var_type = self.get_expression_type(node.children[0], symtable)
            return var_type

        elif node.type in ("paren", "factor_paren"):
            return self.get_expression_type(node.children[0], symtable)

        elif node.type == "factor_tail_binop":
            operator_node = node.children[0]
            right_node = node.children[1]
            tail_node = node.children[2]

            op = operator_node if isinstance(operator_node, str) else operator_node.value
            right_type = self.get_expression_type(right_node, symtable)

            if tail_node is not None:
                tail_type = self.get_expression_type(tail_node, symtable)
                if right_type and tail_type:
                    return self.combine_numeric_types(right_type, tail_type)
                return right_type or tail_type

            return right_type

        # ### REORDER: Now we do a fallback "visit" last, in case we missed anything
        self.generic_visit(node, symtable)
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

            if isinstance(node.children[2], list):
                node.children[2] = ASTNode("parameters", node.children[2])
            params_info = self.extract_parameters_info(node.children[2])
            param_types = []
            for (param_name, param_type) in params_info:
                param_types.append(param_type)
            self.declared_functions[func_name] = (ret_type, param_types)

        func_scope = SymbolTable(parent=symtable)
        func_scope.expected_return_type = self.declared_functions[func_name][0]

        for (param_name, param_type) in self.extract_parameters_info(node.children[2]):
            try:
                func_scope.add(param_name, param_type)
            except SemanticError as e:
                self.errors.append(f"Semantic Error in function '{func_name}': {str(e)}")

        statements_node = node.children[3]
        if isinstance(statements_node, list):
            statements_node = ASTNode("statements", statements_node)
            node.children[3] = statements_node
        self.visit(statements_node, func_scope)

        revive_node = node.children[4] if len(node.children) > 4 else None
        has_expected_return = func_scope.expected_return_type != "void"
        if revive_node:
            self.visit_revive(revive_node, func_scope)
        elif has_expected_return:
            self.errors.append(
                f"Return Type Error: Function '{func_name}' expects a return value of type '{func_scope.expected_return_type}', but no 'revive' statement was found."
            )

        if len(node.children) > 5:
            for child in node.children[5:]:
                self.visit(child, func_scope)





    def extract_parameters_info(self, node):
        params = []
        if node is None or node.type != "parameters":
            return params

        for child in node.children:
            if hasattr(child, "type") and child.type == "param_decl" and len(child.children) >= 2:
            
                param_type = child.children[0].value
                param_name = child.children[1].value
                params.append((param_name, param_type))

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
        for child in node.children:
            if hasattr(child, "type") and child.type == "param_decl" and len(child.children) >= 2:
                types.append(child.children[0].value)
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
        func_name = node.children[0].value
        if func_name not in self.declared_functions:
            self.errors.append(f"Semantic Error: Function '{func_name}' is not declared.")
            return

        signature = self.declared_functions[func_name] 
        expected_param_types = signature[1]

        # Extract the argument types
        args_node = node.children[1]
        arg_types = self.extract_arguments(args_node, symtable)

        # Check for mismatch in argument count
        if len(arg_types) != len(expected_param_types):
            self.errors.append(
                f"Argument Mismatch Error: Function '{func_name}' expects "
                f"{len(expected_param_types)} arguments, got {len(arg_types)}."
            )
        else:
            for i, (arg_type, expected_type) in enumerate(zip(arg_types, expected_param_types)):
                if arg_type == expected_type:
                
                    continue
                elif (arg_type, expected_type) in allowed_implicit_conversions:
                    # e.g. Day (bln) → int
                    continue
                else:
                    self.errors.append(
                        f"Type Error: Argument {i+1} of function '{func_name}' "
                        f"expected type '{expected_type}', got '{arg_type}'."
                    )

     
        self.generic_visit(node, symtable)

    def extract_arguments(self, node, symtable):
        arg_types = []
        if node is None or node.type != "arguments":
            return arg_types

        # Loop over every argument node
        for child in node.children:
            arg_type = self.get_expression_type(child, symtable)
            if arg_type is not None:
                arg_types.append(arg_type)

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
                self.visit(node.children[0], symtable)
                expr_type = self.get_expression_type(node.children[0], symtable)
                if expr_type is None:
                    self.errors.append(f"Return Type Error: Function expects return type '{expected}', but got 'None'.")
                    return
                allowed_implicit_conversions = {
                    ("int", "flt"),
                    ("flt", "int"),
                    ("bln", "flt"),
                    ("flt", "bln"),
                    ("int", "bln"),
                    ("bln", "int"),
                }
                if expr_type == expected:
                    return
                elif (expr_type, expected) in allowed_implicit_conversions:
                    return
                else:
                    self.errors.append(
                        f"Return Type Error: Function expects return type '{expected}', but got '{expr_type}'."
                    )
            else:
                self.errors.append("Return Type Error: No return expression provided.")
    def get_list_dimension(self, node):
        if node.type != "list_value":
            return 0
        if not node.children:
            return 1
        list_elem = node.children[0]  
        if list_elem and hasattr(list_elem, "children") and list_elem.children:
            first_item = list_elem.children[0]
            if hasattr(first_item, "type") and first_item.type == "list_value":
                return 1 + self.get_list_dimension(first_item)
        return 1
    
    def get_list_literal_type(self, node, symtable):
        if node.type != "list_value":
            return None

        dim = self.get_list_dimension(node)  
        if not node.children:
            return None

        list_elem = node.children[0]
        if not list_elem or not list_elem.children:
            return None

        first_item = list_elem.children[0]
        base_type = self.get_expression_type(first_item, symtable)
        print(f"DEBUG: list literal dimension={dim}, base_type={base_type}")

        if base_type is None:
            return None
        self._validate_list_items(list_elem, symtable, base_type)

        if len(self.errors) > 0:

            return None


        if dim == 1:
            return f"{base_type}[]"
        elif dim == 2:
            return f"{base_type}[][]"
        else:
            return f"{base_type}" + "[]" * dim

    def _validate_list_items(self, list_element_node, symtable, base_type):
        if not list_element_node or not list_element_node.children:
            return


        first_item_node = list_element_node.children[0]

        if first_item_node.type == "nested_list":

            self.errors.append(
                "Type Error: Nested list found in a 1D list declaration."
            )
        else:

            item_type = self.get_expression_type(first_item_node, symtable)
            if not self._is_cstyle_convertible(item_type, base_type):
                self.errors.append(
                    f"Type Error: Cannot convert item of type '{item_type}' to '{base_type}'."
                )


        if len(list_element_node.children) > 1:
            tail_node = list_element_node.children[1]

            if tail_node and tail_node.type == "list_element":
                self._validate_list_items(tail_node, symtable, base_type)
    
    def _is_cstyle_convertible(self, from_type, to_type):
 
        if from_type == to_type:
            return True

        if to_type == "int" and from_type in ("flt", "bln"):
            return True
        if to_type == "flt" and from_type in ("int", "bln"):
            return True
        if to_type == "bln" and from_type in ("int", "flt"):
            return True

        return False



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
