from Parser import ASTNode

class CodeGenerator:
    def __init__(self):
        self.global_vars = {}
        self.env_stack = [self.global_vars]
        self.functions = {}
        self.return_values = []
        self.debug = False 
        self.waiting_for_input = False
        self.input_value = None
        self.input_prompt = ""
        self.ast = None
        self.paused_node = None
        self.parent_nodes = []
        self.stopped = False  # Flag to indicate if execution should be stopped
        self.completed = False  # Flag to indicate if program has completed execution
        # New variables for tracking multiple inputs
        self.input_target_queue = []  # Queue to hold pending input targets
        self.current_assignment_target = None  # Current variable being assigned to
        self.expected_type = None  # Expected type for the current input

    def log(self, message):
        if self.debug:
            pass

    def get_current_env(self):
        return self.env_stack[-1]

    def push_scope(self):
        self.env_stack.append({})

    def pop_scope(self):
        if len(self.env_stack) > 1:
            self.env_stack.pop()
        else:
            pass

    def lookup_variable(self, var_name):
        # Search through the environment stack, starting with the most local scope
        for i, env in enumerate(reversed(self.env_stack)):
            scope_name = "local" if i == 0 else f"parent {i}"
            if var_name in env:
                value = env[var_name]
                return value
        return None

    def assign_variable(self, var_name, value):
        self.log(f"Assigning '{var_name}' = {value}")
        
        # First try to find and update the variable in an existing scope
        for env in reversed(self.env_stack):
            if var_name in env:
                # Make sure we're assigning a clean value to prevent memory corruption
                if isinstance(value, int):
                    env[var_name] = int(value)  # Ensure it's a clean int
                else:
                    env[var_name] = value
                self.log(f"Updated existing variable '{var_name}' = {value} in scope")
                return
        
        # If not found, add to current scope
        if isinstance(value, int):
            self.get_current_env()[var_name] = int(value)  # Ensure it's a clean int
        else:
            self.get_current_env()[var_name] = value
        self.log(f"Created new variable '{var_name}' = {value} in current scope")

    def flatten_nodes(self, nodes):
        if not isinstance(nodes, list):
            return [nodes]
        flat = []
        for item in nodes:
            if isinstance(item, list):
                flat.extend(self.flatten_nodes(item))
            else:
                flat.append(item)
        return flat

    def generate(self, ast):
        """
        Main entry point for code generation.
        If ast is None, it means we're resuming execution after input.
        """
        
        if self.stopped:
            self.completed = True  # Make sure any stopped program is marked as completed
            return None
            
        if ast is not None:
            self.ast = ast
            # Debug print AST structure
            if self.debug:
                pass
            
        # Only return early if we have no AST, no paused node, and are not waiting for input
        if ast is None and not self.waiting_for_input and self.paused_node is None:       
            return
            
      
        result = self.execute_node(ast)
        # Mark program as completed when done executing
        if not self.waiting_for_input:
            self.completed = True
        else:
            pass
        return result

    def execute_node(self, node):
        # Check if execution is stopped
        if self.stopped:
            return None
            
        if node is None and self.paused_node and not self.waiting_for_input:
            temp_node = self.paused_node
            self.paused_node = None
            
            # If this is an input statement that just received input, execute it and continue with next node
            if hasattr(temp_node, 'type') and temp_node.type == "input_statement":
                self.log("Resuming execution of paused input node")
                input_result = self.execute_input_statement(temp_node)
                
                # Find the variable to update with the input value if we have a tracked assignment target
                if self.current_assignment_target:
                    var_name = self.current_assignment_target
                    self.log(f"Updating tracked variable {var_name} with input value: {input_result}")
                    
                    # Apply type conversion based on expected type if available
                    if self.expected_type and input_result is not None:
                        input_result = self.convert_type(input_result, self.expected_type)
                        self.log(f"Converted input to expected type {self.expected_type}: {input_result}")
                    
                    # Update the variable with the input result
                    self.assign_variable(var_name, input_result)
                    
                    # Move to next input target if available
                    if self.input_target_queue:
                        next_target = self.input_target_queue.pop(0)
                        self.current_assignment_target = next_target.get('variable')
                        self.expected_type = next_target.get('type')
                        self.log(f"Moving to next input target: {self.current_assignment_target} of type {self.expected_type}")
                    else:
                        # Clear tracking if no more targets
                        self.current_assignment_target = None
                        self.expected_type = None
                
                # If parent is main_function, directly look at its children structure
                if hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0:
                    parent = self.parent_nodes.pop()
                    
                    if hasattr(parent, 'type') and parent.type == "main_function":
                        # Get the main statements list (first child)
                        if parent.children and len(parent.children) > 0:
                            statements_list = parent.children[0]
                            
                            # Find the parent list that contains our input statement
                            if isinstance(statements_list, list):
                                found_index = -1
                                for i, stmt_group in enumerate(statements_list):
                                    # Each statement may be wrapped in a list
                                    if isinstance(stmt_group, list) and len(stmt_group) > 0:
                                        inner_stmt = stmt_group[0]
                                        if inner_stmt == temp_node:
                                            found_index = i
                                            break
                                        
                                        # Also check if the input is inside a var_statement
                                        if hasattr(inner_stmt, 'type') and inner_stmt.type == "var_statement" and inner_stmt.children:
                                            # Look for input_statement in var_statement children
                                            for child in inner_stmt.children:
                                                if hasattr(child, 'type') and child.type == "local_var_assign" and child.children:
                                                    value_node = child.children[0]
                                                    if hasattr(value_node, 'type') and value_node.type == "value" and value_node.children:
                                                        if hasattr(value_node.children[0], 'type') and value_node.children[0].type == "input_statement":
                                                            if value_node.children[0] == temp_node:
                                                                # Get variable name from var_statement
                                                                if hasattr(inner_stmt, 'children'):
                                                                    for vchild in inner_stmt.children:
                                                                        if hasattr(vchild, 'type') and vchild.type == "IDENT":
                                                                            var_name = vchild.value.lstrip('$')
                                                                            # Only update if not already updated via tracked assignment
                                                                            if not self.current_assignment_target or self.current_assignment_target != var_name:
                                                                                self.get_current_env()[var_name] = input_result
                                                                            break
                                                            
                                                            found_index = i
                                                            break
                            
                            # Execute all statements after the input statement
                            if found_index >= 0:
                                for i in range(found_index + 1, len(statements_list)):
                                    next_stmt = statements_list[i]
                                    self.execute_node(next_stmt)
                
                # Return the input result
                return input_result
            
            # Otherwise just continue with the paused node
            return self.execute_node(temp_node)

        if self.waiting_for_input:
            return None
            
        if node is None:
            return None

        # Handle Day/Night literals at the node level
        if hasattr(node, 'value') and node.value == "Day":
            self.log(f"Found Day literal in node of type {node.type}")
            return True
        if hasattr(node, 'value') and node.value == "Night":
            self.log(f"Found Night literal in node of type {node.type}")
            return False

        if isinstance(node, list):
            results = []
            
            # If this is a doubly-nested list (like in the main_function), handle each inner list
            if len(node) > 0 and isinstance(node[0], list):
                for inner_list in node:
                    inner_result = self.execute_node(inner_list)
                    if inner_result is not None:
                        results.append(inner_result)
            # Otherwise just execute each item in the list
            else:
                for subnode in self.flatten_nodes(node):
                    if self.waiting_for_input:
                        break
                    res = self.execute_node(subnode)
                    if res is not None:
                        results.append(res)
                        
            return results if results else None

        if not hasattr(node, 'type'):
            return None

        
        if node.type == "input_statement" and self.input_value is not None and not self.waiting_for_input:
            input_val = self.input_value
           
            self.input_value = None
            return input_val
        
 
        if node.type in ["conditional_statement", "condition", "otherwise_check", "otherwise"]:
            self.log(f"DEBUG: Found conditional structure node of type: {node.type}")
            self.log(f"DEBUG: Node details - ID: {id(node)}, Children count: {len(node.children) if node.children else 0}")
            self.print_node_structure(node)
        
        if node.children:
            node.children = self.flatten_nodes(node.children)
        
        if node.type == "conditional_statement":
            self.log("CONDITIONAL: Routing to execute_conditional_statement")
            return self.execute_conditional_statement(node)
        elif node.type == "condition":
            self.log("CONDITIONAL: Routing to execute_condition")
            return self.execute_condition(node)
        elif node.type == "otherwise_check":
            self.log("CONDITIONAL: Routing to execute_otherwise_check")
            return self.execute_otherwise_check(node)
        elif node.type == "otherwise":
            self.log("CONDITIONAL: Routing to execute_otherwise")
            return self.execute_otherwise(node)
        elif node.type == "switch_statement":
            self.log("SWITCH: Routing to execute_switch_statement")
            return self.execute_switch_statement(node)
        
        method_name = f"execute_{node.type}"
        executor = getattr(self, method_name, self.generic_execute)
        result = executor(node)
        self.log(f"Result of execute_{node.type}: {result}")
        return result

    def generic_execute(self, node):
        self.log(f"Using generic_execute for node type: {node.type}")
        
        results = []
        if node.children:
            for child in node.children:
                result = self.execute_node(child)
                results.append(result)
        return results[-1] if results else None

    # ==========================
    #    TOP-LEVEL EXECUTION
    # ==========================

    def execute_program(self, node):
        self.log("Executing program")
        results = []
   
        for child in node.children:
            if hasattr(child, 'type') and child.type == "function_declaration":
                self.execute_function_declaration(child)
      
        for child in node.children:
            if hasattr(child, 'type'):
                if child.type == "global_statement":
                    result = self.execute_global_statement(child)
                    results.append(result)
                elif child.type == "main_function":
                    result = self.execute_main_function(child)
                    results.append(result)
                elif child.type != "function_declaration": 
                    result = self.execute_node(child)
                    results.append(result)
        
        return results[-1] if results else None

    def execute_main_function(self, node):
        self.log("Executing main_function")
        if not node.children or len(node.children) < 1:
            self.log("No statements in main function")
            return None
    
        # Create a new scope for the main function
        self.push_scope()
        
        self.log(f"Main function has {len(node.children)} statements")
        
        # Check if we have a statements block
        if len(node.children) > 0 and node.children[0] is not None:
            # For resuming from input, track this as a parent node
            self.parent_nodes.append(node)
            
            result = self.execute_node(node.children[0])
            
            if not self.waiting_for_input:
                self.parent_nodes.pop()  # Clean up parent node reference
                self.pop_scope()  # Only pop scope if we're not waiting for input
                
            return result
        
        self.pop_scope()  # Pop scope if there were no children
        return None

    # ==========================
    #    FUNCTION HANDLING
    # ==========================
    
    def execute_function_declaration(self, node):
        self.log("Executing function_declaration")
        
        func_name = None
        for child in node.children:
            if hasattr(child, 'type') and child.type == "FUNCTION_NAME":
                func_name = child.value
                break
                
        if not func_name:
            return None
            
        self.log(f"Defining function: {func_name}")
        

        self.functions[func_name] = {
            'node': node,
            'params': []
        }

        for child in node.children:
            if hasattr(child, 'type') and child.type == "parameters":
                param_nodes = []
                for param in child.children:
                    if hasattr(param, 'type') and param.type == "param_decl":
                        param_data = {"name": None, "type": None}
                        for param_child in param.children:
                            if hasattr(param_child, 'type'):
                                if param_child.type == "IDENT":
                              
                                    param_data["name"] = param_child.value.lstrip('$')
                                elif param_child.type == "data_type":
                                    param_data["type"] = param_child.value
                        self.functions[func_name]['params'].append(param_data)
                        self.log(f"Added parameter: {param_data}")
        
        return None  
        
    def execute_function_call(self, node):
        self.log("Executing function_call")
        
        try:
            func_name = None
            for child in node.children:
                if hasattr(child, 'type') and child.type == "FUNCTION_NAME":
                    func_name = child.value
                    break
                    
            if not func_name:
                self.log("ERROR: Function call missing function name")
                print("Error: Invalid function call - missing function name")
                self.stopped = True
                return None
                
            self.log(f"Calling function: {func_name}")
            
            if func_name not in self.functions:
                self.log(f"ERROR: Undefined function: {func_name}")
                print(f"Error: Undefined function: {func_name}")
                self.stopped = True
                return None
                
            args = []
            for child in node.children:
                if hasattr(child, 'type') and child.type == "arguments":
                    for arg in child.children:
                        arg_value = self.execute_node(arg)
                        args.append(arg_value)
                        self.log(f"Argument value: {arg_value}")
            
            # Check argument count against parameter count
            expected_params = len(self.functions[func_name]['params'])
            actual_args = len(args)
            if actual_args != expected_params:
                self.log(f"ERROR: Function {func_name} expected {expected_params} arguments, got {actual_args}")
                print(f"Error: Function {func_name} expected {expected_params} arguments, got {actual_args}")
                self.stopped = True
                return None
       
            self.push_scope()
            
            for i, param in enumerate(self.functions[func_name]['params']):
                if i < len(args):
                    param_name = param["name"]
                    param_type = param.get("type")
                    arg_value = args[i]
                    
                    # Type check and conversion
                    if param_type and arg_value is not None:
                        if self.casper_to_python_type(param_type) != type(arg_value).__name__.lower():
                            try:
                                # Apply conversion if types don't match
                                converted_value = self.convert_type(arg_value, param_type)
                                self.log(f"Converted argument from {type(arg_value).__name__} to {param_type}: {arg_value} → {converted_value}")
                                arg_value = converted_value
                            except Exception as e:
                                self.log(f"ERROR: Failed to convert argument to expected type for function {func_name}: {str(e)}")
                                print(f"Error: Type mismatch in function {func_name} for parameter '{param_name}'. Expected {param_type}, got {type(arg_value).__name__}")
                                self.stopped = True
                                self.pop_scope()
                                return None
                    
                    self.get_current_env()[param_name] = arg_value
                    self.log(f"Bound parameter '{param_name}' to value {arg_value}")
     
            func_node = self.functions[func_name]['node']
            for child in func_node.children:
                if self.stopped:
                    break
                    
                if hasattr(child, 'type') and child.type == "statements":
                    for statement in child.children:
                        if self.stopped:
                            break
                        self.execute_node(statement)
                else:
                    self.execute_node(child)

            return_value = None
            if self.return_values:
                return_value = self.return_values.pop()
                self.log(f"Function returned: {return_value}")

            self.pop_scope()
            
            return return_value
        except Exception as e:
            self.log(f"ERROR: Exception in function call {func_name if func_name else 'unknown'}: {str(e)}")
            print(f"Error: Exception in function call: {str(e)}")
            self.stopped = True
            if 'scope_pushed' in locals() and scope_pushed:
                self.pop_scope()
            return None

    def execute_revive_statement(self, node):
        self.log("Executing revive_statement")

        if not node.children:
            self.log("revive_statement has no children")
            return None

        value = self.execute_node(node.children[0])
        self.log(f"Return value: {value}")

        self.return_values.append(value)
        
        return value

    # ==========================
    #    STATEMENTS
    # ==========================
    
    def execute_global_statement(self, node):
        self.log("Executing global_statement")
        self.log(f"Global statement children: {node.children}")
        
        var_name = None
        var_value = None
        data_type = None
        
        for child in node.children:
            if child is None:
                continue
                
            if hasattr(child, 'type'):
                if child.type == "data_type":
                    data_type = child.value
                elif child.type == "IDENT":
                    var_name = child.value.lstrip('$')
                elif child.type == "expression":
                    var_value = self.execute_node(child)
                elif child.type == "literal":
                    var_value = child.value
        
        self.log(f"Parsed global: name={var_name}, type={data_type}, value={var_value}")
        
        if var_value is None:
            if data_type == "int":
                var_value = 0
            elif data_type == "string":
                var_value = ""
            elif data_type == "float":
                var_value = 0.0
            elif data_type == "bool":
                var_value = False

        if var_name:
            self.global_vars[var_name] = var_value
            self.log(f"Set global variable '{var_name}' to {var_value}")
        
        return var_value

    def execute_var_statement(self, node):
        """Execute a var statement"""
        self.log("Executing var_statement")

        valid_children = [n for n in node.children if n is not None]
        
        if len(valid_children) < 2:
            self.log(f"var_statement has insufficient children: {len(valid_children)}")
            return None
        
        # Get the data type and variable name
        data_type_node = valid_children[0]
        ident_node = valid_children[1]
        
        if not hasattr(data_type_node, 'value') or not hasattr(ident_node, 'value'):
            self.log("Missing data_type or ident value")
            return None
        
        data_type = data_type_node.value
        var_name = ident_node.value.lstrip('$')
        
        self.log(f"Variable declaration: {data_type} {var_name}")
        
        if not var_name:
            return None
        
        # Initialize with default value based on data type
        default_value = None
        if data_type == "int":
            default_value = 0
        elif data_type == "string" or data_type == "str":
            default_value = ""
        elif data_type == "float" or data_type == "flt":
            default_value = 0.0
        elif data_type == "bool" or data_type == "bln":
            default_value = False
        
        # Find assignment if it exists
        assign_node = None
        contains_input = False
        for child in valid_children:
            if hasattr(child, 'type'):
                if child.type == "local_var_assign" or child.type == "expression" or child.type == "function_call":
                    assign_node = child
                    # Check if this assignment contains an input statement
                    if child.type == "local_var_assign" and child.children:
                        for gc in child.children:
                            if hasattr(gc, 'type') and gc.type == "value" and gc.children:
                                for gcc in gc.children:
                                    if hasattr(gcc, 'type') and gcc.type == "input_statement":
                                        contains_input = True
                                        break
                    break
                elif child.type == "input_statement":
                    assign_node = child
                    contains_input = True
                    break
        
        # If this is an input assignment, track it
        if contains_input:
            self.current_assignment_target = var_name
            self.expected_type = data_type
            self.log(f"Setting input target: {var_name} with expected type {data_type}")
        
        # Get the value from the assignment if it exists
        if assign_node:
            assigned_value = self.execute_node(assign_node)
            
            # Apply type conversion based on the variable's declared data type
            if assigned_value is not None and data_type:
                original_value = assigned_value
                assigned_value = self.convert_type(assigned_value, data_type)
                self.log(f"Applied type conversion for variable declaration: {type(original_value).__name__} -> {data_type}: {original_value} -> {assigned_value}")
            
            # Update the variable's value
            self.get_current_env()[var_name] = assigned_value
        else:
            # Initialize with default value if no assignment
            self.get_current_env()[var_name] = default_value
            
        return self.get_current_env()[var_name]
        
    def casper_to_python_type(self, casper_type):
        """Convert CASPER type names to Python type names."""
        if casper_type == "int":
            return "int"
        elif casper_type == "float" or casper_type == "flt":
            return "float"
        elif casper_type == "bool" or casper_type == "bln":
            return "bool"
        elif casper_type == "string" or casper_type == "str":
            return "string"
        else:
            self.log(f"Unknown CASPER type: {casper_type}")
            return None

    def execute_local_var_assign(self, node):
        self.log("Executing local_var_assign")

        if not node.children or len(node.children) < 1:
            return None
       
        value_node = node.children[0]
        
        result = self.execute_node(value_node)
        
        return result
        
    def execute_value(self, node):
        
        if not node.children or len(node.children) < 1:
            return None
            
        value_expr = node.children[0]
        
        result = self.execute_node(value_expr)
        
        return result
        
    def execute_expression(self, node):
        
        if not node.children or len(node.children) < 1:
            return None
        
        left_node = node.children[0]
        
        left_value = self.execute_node(left_node)
        
        # Check if there's an expression_chain (binary operation)
        if len(node.children) > 1 and node.children[1] is not None:
            binop_node = node.children[1]
            
            # Check if we have a logical expression (&&, ||)
            if isinstance(binop_node, list) or len(binop_node.children) > 1:
                # Special handling for logical operations to ensure correct precedence
                for child in binop_node.children:
                    if hasattr(child, 'type') and hasattr(child, 'value') and child.value in ["&&", "||"]:
                        self.log(f"EXPRESSION DEBUG: Handling logical operator: {child.value}")
                        return self.evaluate_logical_expression(left_value, binop_node)
            
            result = self.evaluate_expression_chain(left_value, binop_node)
            
            return result
        
        return left_value
        
    def evaluate_expression_chain(self, left_value, binop_node):
        
        if not binop_node or not binop_node.children:
            return left_value
        
        # Get operator, right value, and possible tail
        operator_node = binop_node.children[0]
        right_node = binop_node.children[1]
        tail_node = binop_node.children[2] if len(binop_node.children) > 2 else None
        
        # Get the operator value
        operator = operator_node.value if hasattr(operator_node, 'value') else operator_node
        
        # Evaluate the right side
        right_value = self.execute_node(right_node)
        
        # Apply the operator with appropriate error handling
        try:
            result = self.apply_operator(operator, left_value, right_value)
            
            # If there's a tail, recursively evaluate it
            if tail_node is not None and not self.stopped:
                result = self.evaluate_expression_chain(result, tail_node)
            
            return result
        except Exception as e:
            self.log(f"ERROR: Expression evaluation failed: {left_value} {operator} {right_value} - {str(e)}")
            print(f"Error: Expression evaluation failed: {str(e)}")
            self.stopped = True
            return 0

    def execute_output_statement(self, node):
        self.log("Executing output_statement")
        
        if not node.children:
            pass
            return None
        
        # Special handling for IDENT nodes (variable display)
        # This is to directly handle variables within output statements
        if len(node.children) == 1 and hasattr(node.children[0], 'type'):
            child = node.children[0]
            
            # If it's a var_call node, get the variable and directly display its value
            if child.type == "var_call" and child.children and hasattr(child.children[0], 'value'):
                var_name = child.children[0].value.lstrip('$')
                value = self.lookup_variable(var_name)
                self.log(f"Directly displaying variable {var_name} = {value}")
                
                # Ensure we never display numeric values as Day/Night
                if value is not None:
                    if isinstance(value, bool) and not (isinstance(value, int) and not isinstance(value, bool)):
                        # Only format as Day/Night if it's SPECIFICALLY a boolean (not an int)
                        formatted_value = "Day" if value else "Night"
                        print(formatted_value, end="")
                    else:
                        # Never format integers or other types as Day/Night
                        print(value, end="")  # Changed to not add newline
                return value
        
        # Standard processing for other types of output children
        for child in node.children:
            result = self.execute_node(child)
            self.log(f"Output result: {result}")
            
            # Handle string literals containing formatting instructions
            if isinstance(result, str) and result.startswith('"') and result.endswith('"'):
                # Remove the quotes and handle escape sequences
                result = result[1:-1].replace('\\n', '\n').replace('\\t', '\t')
            # Format boolean values as Day/Night ONLY IF they are specifically boolean, not int
            elif isinstance(result, bool) and not (isinstance(result, int) and not isinstance(result, bool)):
                result = "Day" if result else "Night"
            
            # Make sure we display the result properly, even if it's a number
            if result is not None:
                print(result, end="")  # Changed to not add newline
        
        return None  # The output statement doesn't return a value
        
    def execute_display_statement(self, node):
        self.log("Executing display_statement")

        # Check if there's an expression to evaluate
        if not node.children or len(node.children) == 0:
            return None
        
        # Get the expression to display
        expr_node = node.children[0]
        
        # Evaluate the expression
        result = self.execute_node(expr_node)
        
        # Ensure a proper string representation for display
        if isinstance(result, bool):
            # Convert boolean to "Day" or "Night"
            formatted_value = "Day" if result else "Night"
            print(formatted_value, end="")
        elif result is None:
            formatted_value = ""
        else:
            # Display the result without adding a newline
            print(result, end="")
        
        return result

    # ==========================
    #    EXPRESSIONS
    # ==========================

    def execute_factor_tail_binop(self, node):
        self.log(f"Executing factor_tail_binop: {node}")
        return None

    def execute_operator(self, node):
        self.log(f"Executing operator: {node}")
        return node.value

    def apply_operator(self, operator, left, right):
        self.log(f"Applying operator: {left} {operator} {right}")
        
        # Apply implicit type conversion based on the operation type
        left, right = self.apply_implicit_conversion(left, right, operator)
        
        try:
            if operator == "+":
                return left + right
            elif operator == "-":
                return left - right
            elif operator == "*":
                return left * right
            elif operator == "/":
                if right == 0:
                    self.log("ERROR: Division by zero detected")
                    print("Error: Division by zero")
                    self.stopped = True
                    return 0
                return left / right
            elif operator == "%":
                if right == 0:
                    self.log("ERROR: Modulo by zero detected")
                    print("Error: Modulo by zero")
                    self.stopped = True
                    return 0
                return left % right
            elif operator == "||":
                return bool(left) or bool(right)
            elif operator == "&&":
                return bool(left) and bool(right)
            elif operator == "==":
                return left == right
            elif operator == "!=":
                return left != right
            elif operator == ">":
                return left > right
            elif operator == "<":
                return left < right
            elif operator == ">=":
                return left >= right
            elif operator == "<=":
                return left <= right
            else:
                self.log(f"WARNING: Unknown operator '{operator}'")
                return None
        except OverflowError:
            self.log(f"ERROR: Numeric overflow in operation {left} {operator} {right}")
            print(f"Error: Numeric overflow in operation {left} {operator} {right}")
            self.stopped = True
            return 0
        except Exception as e:
            self.log(f"ERROR: Operation failed: {left} {operator} {right} - {str(e)}")
            print(f"Error: Operation failed: {str(e)}")
            self.stopped = True
            return 0

    def apply_implicit_conversion(self, left, right, operator=None):
        """Apply implicit type conversion based on the types of operands and the conversion table."""
        self.log(f"Applying implicit conversion: {type(left).__name__} {operator} {type(right).__name__}")
        
        if operator in ["+", "-", "*", "/", "%"]:
            if isinstance(left, int) and isinstance(right, float):
                # int → flt: Add .0
                left = float(left)
                self.log(f"Converted left from int to float: {left}")
            elif isinstance(left, float) and isinstance(right, int):
                # flt → int not applied here, keep as float for math ops
                right = float(right)
                self.log(f"Converted right from int to float: {right}")
            
            # Handle boolean conversions
            if isinstance(left, bool):
                if isinstance(right, float):
                    # bln → flt: Day → 1.0, Night → 0.0
                    left = 1.0 if left else 0.0
                    self.log(f"Converted left from bool to float: {left}")
                elif isinstance(right, int):
                    # bln → int: Day → 1, Night → 0
                    left = 1 if left else 0
                    self.log(f"Converted left from bool to int: {left}")
            
            if isinstance(right, bool):
                if isinstance(left, float):
                    # bln → flt: Day → 1.0, Night → 0.0
                    right = 1.0 if right else 0.0
                    self.log(f"Converted right from bool to float: {right}")
                elif isinstance(left, int):
                    # bln → int: Day → 1, Night → 0
                    right = 1 if left else 0
                    self.log(f"Converted right from bool to int: {right}")
        
        # For comparison operations
        elif operator in ["==", "!=", ">", "<", ">=", "<="]:
            # Try to make types match based on conversion table
            if isinstance(left, int) and isinstance(right, float):
                # int → flt: Add .0
                left = float(left)
                self.log(f"Converted left from int to float for comparison: {left}")
            elif isinstance(left, float) and isinstance(right, int):
                # int → flt: Add .0 (converting right to match left)
                right = float(right)
                self.log(f"Converted right from int to float for comparison: {right}")
            elif isinstance(left, bool) and isinstance(right, int):
                # bln → int: Day → 1, Night → 0
                left = 1 if left else 0
                self.log(f"Converted left from bool to int for comparison: {left}")
            elif isinstance(left, int) and isinstance(right, bool):
                # bln → int: Day → 1, Night → 0 (converting right to match left)
                right = 1 if right else 0
                self.log(f"Converted right from bool to int for comparison: {right}")
            elif isinstance(left, bool) and isinstance(right, float):
                # bln → flt: Day → 1.0, Night → 0.0
                left = 1.0 if left else 0.0
                self.log(f"Converted left from bool to float for comparison: {left}")
            elif isinstance(left, float) and isinstance(right, bool):
                # bln → flt: Day → 1.0, Night → 0.0 (converting right to match left)
                right = 1.0 if right else 0.0
                self.log(f"Converted right from bool to float for comparison: {right}")
        
        return left, right

    
    def convert_type(self, value, target_type):
        """Convert a value to the specified target type using the conversion rules from the table."""
        self.log(f"Converting {value} ({type(value).__name__}) to {target_type}")
        
        # No conversion needed if types match
        if type(value).__name__.lower() == target_type:
            return value
            
        # Handle specific conversions based on the table from the image
        
        # int → flt: Add .0
        if isinstance(value, int) and target_type in ["float", "flt"]:
            return float(value)
            
        # flt → int: Truncate decimal
        elif isinstance(value, float) and target_type == "int":
            return int(value)  # Python's int() truncates toward zero
            
        # bln → flt: Day → 1.0, Night → 0.0
        elif isinstance(value, bool) and target_type in ["float", "flt"]:
            result = 1.0 if value else 0.0
            return result
            
        # flt → bln: 0.0 → Night, else Day
        elif isinstance(value, float) and target_type in ["bool", "bln"]:
            result = False if value == 0.0 else True
            return result
            
        # int → bln: 0 → Night, else Day
        elif isinstance(value, int) and target_type in ["bool", "bln"]:
            result = False if value == 0 else True
            return result
            
        # bln → int: Day → 1, Night → 0
        elif isinstance(value, bool) and target_type == "int":
            result = 1 if value else 0
            return result
            
        # str conversions (handling string type)
        elif target_type in ["string", "str"]:
            # For boolean values to string, convert to "Day"/"Night" instead of "True"/"False"
            if isinstance(value, bool):
                result = "Day" if value else "Night"
                return result
            return str(value)
            
        # If no rule is defined, try a standard Python conversion
        else:
            try:
                if target_type == "int":
                    result = int(value)
                    return result
                elif target_type in ["float", "flt"]:
                    result = float(value)
                    return result
                elif target_type in ["bool", "bln"]:
                    result = bool(value)
                    return result
                elif target_type in ["string", "str"]:
                    result = str(value)
                    return result
                else:
                    self.log(f"No conversion rule for {type(value).__name__} to {target_type}")
                    return value
            except:
                self.log(f"Failed to convert {value} to {target_type}")
                return value

    def execute_literal(self, node):
        self.log(f"Executing literal: {node}, value={node.value}")
        value = node.value
        
        # Handle Day and Night literals as boolean values first
        if value == "Day":
            self.log(f"Converting Day literal to boolean True")
            return True
        elif value == "Night":
            self.log(f"Converting Night literal to boolean False")
            return False
        
        # Special handling for strings with escape sequences
        if isinstance(value, str) and value.startswith('"') and value.endswith('"'):
            # Keep quotes for now, so we can identify string literals later
            self.log(f"String literal detected: {value}")
        
        return value

    def execute_data_type(self, node):
        self.log(f"Executing data_type: {node}")
        return node.value

    # ==========================
    #    VARIABLE CALLS
    # ==========================

    def execute_var_postfix(self, node):
        self.log(f"Executing var_postfix: {node}")
        # var_postfix -> var_call
        # Then sometimes there's an extra child "None" or more
        if not node.children:
            self.log("var_postfix has no children")
            return None
            
        # Filter out None children, if any
        valid_children = [child for child in node.children if child is not None]
        if not valid_children:
            self.log("var_postfix has no valid children")
            return None
            
        # Execute first valid child (should be var_call)
        result = self.execute_node(valid_children[0])
        self.log(f"var_postfix result: {result}")
        return result

    def execute_var_call(self, node):
        self.log("Executing var_call")
        if not node.children:
            self.log("var_call has no children")
            return None
            
        # Get the variable name from the first child (IDENT node)
        ident_node = node.children[0]
        var_name = ident_node.value.lstrip('$')
        
        # Look up variable in environment
        value = self.lookup_variable(var_name)
        
        # Check for indexing operation: $arr[0], $arr[1][2] etc.
        if len(node.children) > 1 and node.children[1]:
            indices = node.children[1]
            if isinstance(value, list) and indices:
                try:
                    for idx in indices:
                        idx_val = self.execute_node(idx)
                        if isinstance(idx_val, int):
                            if 0 <= idx_val < len(value):
                                value = value[idx_val]
                            else:
                                self.log(f"ERROR: Array index out of bounds: {var_name}[{idx_val}], array length: {len(value)}")
                                print(f"Error: Array index out of bounds: {var_name}[{idx_val}], array length: {len(value)}")
                                self.stopped = True
                                return None
                        else:
                            self.log(f"ERROR: Array index must be an integer, got: {type(idx_val).__name__}")
                            print(f"Error: Array index must be an integer, got: {type(idx_val).__name__}")
                            self.stopped = True
                            return None
                except Exception as e:
                    self.log(f"ERROR: Array access failed: {var_name} - {str(e)}")
                    print(f"Error: Array access failed: {str(e)}")
                    self.stopped = True
                    return None
            elif not isinstance(value, list) and indices:
                self.log(f"ERROR: Cannot index non-array variable: {var_name}")
                print(f"Error: Cannot index non-array variable: {var_name}")
                self.stopped = True
                return None
        
        return value

    # ==========================
    #    PARAMETER HANDLING
    # ==========================
    
    def execute_parameters(self, node):
        self.log(f"Executing parameters: {node}")
        # This is handled during function declaration
        return None
        
    def execute_param_decl(self, node):
        self.log(f"Executing param_decl: {node}")
        # This is handled during function declaration
        return None
        
    def execute_arguments(self, node):
        self.log(f"Executing arguments: {node}")
        # This is handled during function call
        results = []
        if node.children:
            for child in node.children:
                result = self.execute_node(child)
                results.append(result)
        return results

    # Handle IDENT node directly if needed
    def execute_IDENT(self, node):
        self.log(f"Executing IDENT: {node}")
        return node.value
        
    def execute_FUNCTION_NAME(self, node):
        self.log(f"Executing FUNCTION_NAME: {node}")
        return node.value
    
    # Handle statements block
    def execute_statements(self, node):
        self.log("Executing statements")
        if not node.children:
            return None
        
        results = []
        
        for i, statement in enumerate(node.children):
            if statement is None:
                continue
                
            # Store parent-child relationship for resuming from input
            if hasattr(self, 'parent_nodes'):
                self.parent_nodes.append(node)
                
            # Store additional information for input statements
            if hasattr(statement, 'type') and statement.type == "input_statement":
                # Keep track of this statement's position
                statement.stmt_index = i
                statement.parent_stmt = node
            
            result = self.execute_node(statement)
            
            # Pop parent node if we just added it and didn't pause
            if hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0 and not self.waiting_for_input:
                self.parent_nodes.pop()
            
            # If we're waiting for input, stop execution and return
            if self.waiting_for_input:
                return None
                
            if result is not None:
                results.append(result)
                
        return results[-1] if results else None
    
    # ==========================
    #    CONDITIONAL EXECUTION
    # ==========================
    
    
    def execute_conditional_statement(self, node):
        self.log("CONDITIONAL DEBUG: Starting execute_conditional_statement")
        
        if not node.children:
            self.log("CONDITIONAL DEBUG: Invalid conditional statement structure")
            return None
        
        # First child should be the condition
        # Execute the condition properly using execute_condition instead of execute_node
        if hasattr(node.children[0], 'type') and node.children[0].type == "condition":
            condition_result = self.execute_condition(node.children[0])
        else:
            condition_result = self.execute_node(node.children[0])
            
        self.log(f"CONDITIONAL DEBUG: Main condition result: {condition_result}")
        
        if condition_result:
            self.log("CONDITIONAL DEBUG: Main condition is TRUE, executing check block")
            return self.execute_node(node.children[1])
            
        # Check for otherwise blocks
        for i in range(2, len(node.children)):
            child = node.children[i]
            if child is None:
                continue
                
            if hasattr(child, 'type'):
                if child.type == "otherwise_check":
                    # Get the condition from otherwise_check and evaluate it properly
                    if child.children and hasattr(child.children[0], 'type') and child.children[0].type == "condition":
                        cond_result = self.execute_condition(child.children[0])
                    else:
                        cond_result = self.execute_node(child.children[0])
                        
                    self.log(f"CONDITIONAL DEBUG: Otherwise_check condition result: {cond_result}")
                    
                    if cond_result:
                        results = []
                        for j in range(1, len(child.children)):
                            result = self.execute_node(child.children[j])
                            results.append(result)
                        return results[-1] if results else None
                elif child.type == "otherwise_block":
                    self.log("CONDITIONAL DEBUG: Executing otherwise block")
                    return self.execute_otherwise_block(child)
        
        return None
    
    def execute_conditional_tail(self, node):
        """Execute else-if chains"""
        self.log("Executing conditional_tail")
        
        if not node.children:
            return None
        
        for child in node.children:
            if child is not None and hasattr(child, 'type') and child.type == "otherwise_check":
          
                condition = None
                block = None
     
                for subchild in child.children:
                    if hasattr(subchild, 'type'):
                        if subchild.type == "condition":
                            condition = subchild
                        elif subchild.type == "statements":
                            block = subchild
                
                if condition and block:
                    condition_result = self.execute_node(condition)
                    if condition_result:
                        return self.execute_node(block)
        
        return None

    
    def execute_otherwise_check(self, node):
        """Execute an otherwise_check statement (else if)"""
        self.log("Executing otherwise_check")

        if not node.children:
            return None
            
        # Properly evaluate the condition using execute_condition
        if hasattr(node.children[0], 'type') and node.children[0].type == "condition":
            condition_result = self.execute_condition(node.children[0])
        else:
            condition_result = self.execute_node(node.children[0])
            
        self.log(f"CONDITIONAL DEBUG: Otherwise_check condition result: {condition_result}")
        
        if condition_result:
            results = []
            for i in range(1, len(node.children)):
                result = self.execute_node(node.children[i])
                results.append(result)
            return results[-1] if results else None
        
        return None
    
    def execute_check_block(self, node):
        """Execute a check block"""
        self.log("Executing check_block")
        
        results = []
        for child in node.children:
            if child is not None:
                result = self.execute_node(child)
                results.append(result)
        
        return results[-1] if results else None

    def execute_otherwise_block(self, node):
        """Execute an otherwise block"""
        self.log("Executing otherwise_block")
        
        results = []
        for child in node.children:
            if child is not None:
                result = self.execute_node(child)
                results.append(result)
        
        return results[-1] if results else None
    
    
    
    def execute_condition(self, node):
        """Execute a condition expression"""
        self.log("CONDITIONAL DEBUG: Starting execute_condition")
        
        if not node.children:
            self.log("CONDITIONAL DEBUG: Condition has no children, returning False")
            return False
   
        left_val = self.execute_node(node.children[0])
        self.log(f"CONDITIONAL DEBUG: Left value: {left_val}")
 
        if len(node.children) > 1 and hasattr(node.children[1], 'type') and node.children[1].type == "factor_tail_binop":
            binop = node.children[1]
            op_node = binop.children[0]
            operator = op_node.value
            right_val = self.execute_node(binop.children[1])
            
            self.log(f"CONDITIONAL DEBUG: Operator: {operator}, Right value: {right_val}")
            
            # Handle modulo operation with comparison
            if operator == "%":
                result = left_val % right_val
                self.log(f"CONDITIONAL DEBUG: Modulo operation: {left_val} % {right_val} = {result}")
                
                if len(binop.children) > 2 and binop.children[2] is not None:
                    next_binop = binop.children[2]
                    if hasattr(next_binop, 'type') and next_binop.type == "factor_tail_binop":
                        next_op = next_binop.children[0].value
                        next_val = self.execute_node(next_binop.children[1])
                        self.log(f"CONDITIONAL DEBUG: Next operation: {result} {next_op} {next_val}")
                        
                        if next_op == "==":
                            return result == next_val
                        elif next_op == "!=":
                            return result != next_val
                        elif next_op == ">":
                            return result > next_val
                        elif next_op == "<":
                            return result < next_val
                        elif next_op == ">=":
                            return result >= next_val
                        elif next_op == "<=":
                            return result <= next_val
                
                return bool(result)
            
            # Handle comparison operations
            elif operator == "==":
                result = left_val == right_val
            elif operator == "!=":
                result = left_val != right_val
            elif operator == ">":
                result = left_val > right_val
            elif operator == "<":
                result = left_val < right_val
            elif operator == ">=":
                result = left_val >= right_val
            elif operator == "<=":
                result = left_val <= right_val
            # Handle logical operations
            elif operator == "&&":
                result = bool(left_val) and bool(right_val)
            elif operator == "||":
                result = bool(left_val) or bool(right_val)
            else:
                # For other operators, use apply_operator method
                result = self.apply_operator(operator, left_val, right_val)
                
            self.log(f"CONDITIONAL DEBUG: Operation result: {left_val} {operator} {right_val} = {result}")
            
            # Check for additional operations in the chain (for complex conditions)
            if len(binop.children) > 2 and binop.children[2] is not None:
                next_binop = binop.children[2]
                if hasattr(next_binop, 'type') and next_binop.type == "factor_tail_binop":
                    next_op = next_binop.children[0].value
                    next_val = self.execute_node(next_binop.children[1])
                    self.log(f"CONDITIONAL DEBUG: Additional operation: {result} {next_op} {next_val}")
                    
                    # Recursively apply the next operation
                    return self.apply_operator(next_op, result, next_val)
            
            return result

        return bool(left_val)

    def execute_otherwise(self, node):
        """Execute an otherwise statement (else block)"""
        self.log("Executing otherwise")
        
        results = []
        for child in node.children:
            if child is not None:
                result = self.execute_node(child)
                results.append(result)
        
        return results[-1] if results else None

    
    def print_node_structure(self, node, indent=0):
        """Debug helper to print the structure of a node and its children"""
        if node is None:
            self.log(" " * indent + "None")
            return
            
        node_type = node.type if hasattr(node, 'type') else "NoType"
        node_value = node.value if hasattr(node, 'value') else "NoValue"
        self.log(" " * indent + f"Node: {node_type}, Value: {node_value}")
        
        if hasattr(node, 'children') and node.children:
            for i, child in enumerate(node.children):
                self.log(" " * indent + f"Child {i}:")
                self.print_node_structure(child, indent + 2)

    # ==========================
    #    SWITCH EXECUTION (SWAP)
    # ==========================

    def execute_switch_statement(self, node):
        """Execute a switch statement (swap)"""
        self.log(f"SWITCH DEBUG: Starting execute_switch_statement")

        if len(node.children) < 3:
            self.log("SWITCH DEBUG: Invalid switch statement structure")
            print("Error: Invalid switch statement structure")
            self.stopped = True
            return None

        ident_node = node.children[0]
        first_switch_condition_node = node.children[1]
        otherwise_statements_node = node.children[2]

        if not hasattr(ident_node, 'value'):
            self.log("SWITCH DEBUG: Switch variable identifier missing")
            print("Error: Switch variable identifier missing")
            self.stopped = True
            return None

        switch_var_name = ident_node.value.lstrip('$')
        switch_value = self.lookup_variable(switch_var_name)

        if switch_value is None:
            # Check if it's Day/Night literal directly (should ideally be handled earlier)
            if switch_var_name == "Day":
                switch_value = True
            elif switch_var_name == "Night":
                switch_value = False
            else:
                self.log(f"SWITCH DEBUG: Switch variable '{switch_var_name}' not found or is None")
                print(f"Error: Switch variable '{switch_var_name}' not found or is None")
                self.stopped = True
                return None

        self.log(f"SWITCH DEBUG: Switching on variable '{switch_var_name}' with value: {switch_value} (type: {type(switch_value).__name__})")

        case_matched = False
        current_case_node = first_switch_condition_node

        while current_case_node is not None and not self.stopped:
            if not hasattr(current_case_node, 'type') or current_case_node.type != "switch_condition":
                self.log("SWITCH DEBUG: Expected switch_condition node, skipping")
                break # Should not happen with correct parsing

            if len(current_case_node.children) < 3:
                self.log("SWITCH DEBUG: Invalid switch_condition structure")
                break # Should not happen

            case_value_node = current_case_node.children[0]
            case_statements_node = current_case_node.children[1]
            switchcond_tail = current_case_node.children[2]

            # Evaluate the case value
            case_value = self.execute_node(case_value_node)
            if self.stopped: # Stop if evaluation failed
                return None

            self.log(f"SWITCH DEBUG: Comparing {switch_value} == {case_value} (types: {type(switch_value).__name__}, {type(case_value).__name__})")

            # Comparison: Apply implicit conversion for comparison
            switch_val_cmp, case_val_cmp = self.apply_implicit_conversion(switch_value, case_value, operator="==")

            if switch_val_cmp == case_val_cmp:
                self.log(f"SWITCH DEBUG: Match found! Executing case block for value {case_value}")
                self.execute_node(case_statements_node) # Execute the statements for this case
                case_matched = True
                break # Exit switch statement after first match
            else:
                # Move to the next case in the tail
                if switchcond_tail and isinstance(switchcond_tail, list) and len(switchcond_tail) > 0:
                    # The tail contains the next switch_condition node
                    current_case_node = switchcond_tail[0]
                else:
                    # No more cases in the tail
                    current_case_node = None

        # Execute otherwise block if no case matched
        if not case_matched and not self.stopped:
            self.log("SWITCH DEBUG: No case matched, executing otherwise block")
            self.execute_node(otherwise_statements_node)

        return None # Switch statements don't return a value

    # ==========================
    #    ASSIGNMENT EXECUTION
    # ==========================

    def execute_assignment_statement(self, node):
        """Execute an assignment statement"""
        self.log("Executing assignment_statement")
        
        try:
            if len(node.children) < 2:
                self.log("ERROR: Assignment statement missing parts")
                print("Error: Invalid assignment statement - missing parts")
                self.stopped = True
                return None
      
            var_node = node.children[0]
            if not hasattr(var_node, 'type') or var_node.type != "IDENT":
                self.log(f"ERROR: Expected IDENT, got {var_node.type if hasattr(var_node, 'type') else 'unknown'}")
                print("Error: Invalid assignment target")
                self.stopped = True
                return None
            
            var_name = var_node.value.lstrip('$')
            if not var_name:
                self.log("ERROR: Empty variable name in assignment")
                print("Error: Empty variable name in assignment")
                self.stopped = True
                return None

            assign_node = node.children[1]
            if not hasattr(assign_node, 'type'):
                self.log(f"ERROR: Invalid assign_node without type")
                print("Error: Invalid assignment operation")
                self.stopped = True
                return None

            # Check if we're tracking this as the current assignment target
            if var_name:
                self.current_assignment_target = var_name
                self.log(f"Setting current assignment target to: {var_name}")
                
                # Look up the variable to get its type
                var_type = None
                existing_value = self.lookup_variable(var_name)
                if existing_value is not None:
                    if isinstance(existing_value, int):
                        var_type = "int"
                    elif isinstance(existing_value, float):
                        var_type = "float"
                    elif isinstance(existing_value, bool):
                        var_type = "bool"
                    elif isinstance(existing_value, str):
                        var_type = "string"
                    
                if var_type:
                    self.expected_type = var_type
                    self.log(f"Setting expected input type to: {var_type}")

            # Execute the assign_tail_op to get the value (or value and operator for compound assignments)
            assign_result = self.execute_node(assign_node)
            if self.stopped:
                return None
                
            self.log(f"Assignment result: {assign_result}")
            
            # Handle compound operators (+=, -=, *=, /=, %=)
            if isinstance(assign_result, dict) and "value" in assign_result and "operator" in assign_result:
                # Get the current value of the variable
                current_value = self.lookup_variable(var_name)
                self.log(f"Current value of '{var_name}': {current_value}")
                
                if current_value is None:
                    self.log(f"ERROR: Variable '{var_name}' not found for compound assignment")
                    print(f"Error: Variable '{var_name}' not found for compound assignment")
                    self.stopped = True
                    return None
                    
                # Get the operator and the right-side value
                operator = assign_result["operator"]
                right_value = assign_result["value"]
                
                self.log(f"Compound assignment: {var_name} {operator} {right_value}, current value: {current_value}")
                
                # Apply the compound operation
                if operator == "+=":
                    value = current_value + right_value
                    self.log(f"Addition operation: {current_value} + {right_value} = {value}")
                elif operator == "-=":
                    value = current_value - right_value
                    self.log(f"Subtraction operation: {current_value} - {right_value} = {value}")
                elif operator == "*=":
                    value = current_value * right_value
                    self.log(f"Multiplication operation: {current_value} * {right_value} = {value}")
                elif operator == "/=":
                    if right_value == 0:
                        self.log("ERROR: Division by zero in compound assignment")
                        print(f"Error: Division by zero in assignment to {var_name}")
                        self.stopped = True
                        return None
                    value = current_value / right_value
                    self.log(f"Division operation: {current_value} / {right_value} = {value}")
                elif operator == "%=":
                    if right_value == 0:
                        self.log("ERROR: Modulo by zero in compound assignment")
                        print(f"Error: Modulo by zero in assignment to {var_name}")
                        self.stopped = True
                        return None
                    value = current_value % right_value
                    self.log(f"Modulo operation: {current_value} % {right_value} = {value}")
                else:
                    self.log(f"ERROR: Unknown compound operator: {operator}")
                    print(f"Error: Unknown compound operator: {operator}")
                    self.stopped = True
                    return None
                    
                # Maintain type consistency for integer operations
                if isinstance(current_value, int) and not isinstance(current_value, bool):
                    value = int(value)
                    self.log(f"Converted result to int: {value}")
                    
                self.log(f"Compound assignment result: {var_name} = {value}")
            else:
                # Regular assignment
                value = assign_result
                self.log(f"Regular assignment value for {var_name}: {value}")
            
            # Apply implicit type conversion based on the existing variable's type
            # Look up the existing variable to get its current type
            existing_value = self.lookup_variable(var_name)
            if existing_value is not None:
                # Only convert if the types differ
                if type(existing_value) != type(value) and value is not None:
                    try:
                        original_value = value
                        target_type = type(existing_value).__name__.lower()
                        value = self.convert_type(value, target_type)
                        self.log(f"Applied implicit conversion for assignment: {type(original_value).__name__} -> {target_type}: {original_value} -> {value}")
                    except Exception as e:
                        self.log(f"ERROR: Type conversion failed in assignment: {str(e)}")
                        print(f"Error: Type conversion failed in assignment to {var_name}")
                        self.stopped = True
                        return None

            self.assign_variable(var_name, value)
            self.log(f"Final value assigned to {var_name}: {value}")
            
            # If this was an input assignment, clear the current assignment target
            if 'contains_input' in locals() and contains_input:
                self.log(f"Keeping assignment target {var_name} for input tracking")
            else:
                self.log(f"Clearing current assignment target since no input detected")
                self.current_assignment_target = None
            
            return value
        except Exception as e:
            self.log(f"ERROR: Exception in assignment statement: {str(e)}")
            print(f"Error: Exception in assignment: {str(e)}")
            self.stopped = True
            return None

    def execute_assign_tail_op(self, node):
        """Execute an assign_tail_op node"""
        self.log("Executing assign_tail_op")
        
        # Check for compound assignment operators in the node
        compound_op = None
        
        # Get the operator node (first child)
        if node.children and len(node.children) > 0:
            op_node = node.children[0]
            
            # Check if this is a compound operator
            if hasattr(op_node, 'type'):
                if op_node.type == "operator" and hasattr(op_node, 'value'):
                    op_value = op_node.value
                    # Check if op_value is a compound operator
                    if op_value in ["+=", "-=", "*=", "/=", "%="]:
                        compound_op = op_value
                        self.log(f"Found compound operator: {compound_op}")
            
        # Get the value node (second child)
        value_node = None
        if len(node.children) > 1:
            value_node = node.children[1]
        
        if value_node:
            # Get the value from the right side of the assignment
            value = self.execute_node(value_node)
            
            # If this is a compound operator, return both the value and operator
            if compound_op:
                self.log(f"Returning compound op data: {compound_op}, value: {value}")
                return {"value": value, "operator": compound_op}
            
            return value
        else:
            self.log("No value node found in assign_tail_op")
            return None

    def execute_input_statement(self, node):
        # If input value is already available, return it immediately without showing prompt again
        if self.input_value is not None and not self.waiting_for_input:
            input_val = self.input_value
            
            # Clear input value to prevent reuse
            self.input_value = None
            self.paused_node = None
            
            # Handle basic conversions from string inputs
            if isinstance(input_val, str):
                # Handle Day/Night values exactly - case sensitive
                if input_val == "Day":
                    input_val = True  # Convert to boolean True (Day)
                elif input_val == "Night":
                    input_val = False  # Convert to boolean False (Night)
                # Try numeric conversion for numeric strings
                elif input_val.replace('.', '', 1).isdigit():
                    try:
                        if '.' in input_val:
                            input_val = float(input_val)
                        else:
                            input_val = int(input_val)
                    except ValueError:
                        pass
            
            # Convert input value based on expected type if available
            if self.expected_type:
                try:
                    # Store original value for logging
                    original_val = input_val
                    
                    # Apply specific conversion rules based on the type table in the image
                    if self.expected_type == "int":
                        # Allow float, bool, or numeric string inputs
                        if isinstance(input_val, float):
                            # flt → int: Truncate decimal
                            input_val = int(input_val)
                            self.log(f"Applied flt → int conversion (truncate decimal): {original_val} → {input_val}")
                        elif isinstance(input_val, bool):
                            # bln → int: Day → 1, Night → 0
                            input_val = 1 if input_val else 0
                            self.log(f"Applied bln → int conversion: {original_val} → {input_val}")
                        elif isinstance(input_val, str):
                            # Try to convert string input to appropriate numeric value
                            try:
                                input_val = float(input_val)
                                input_val = int(input_val)  # Truncate decimal part
                                self.log(f"Converted string to int (with truncation): {original_val} → {input_val}")
                            except ValueError:
                                self.log(f"Error: Cannot convert '{input_val}' to int")
                                self.stopped = True
                                self.completed = True
                                self.waiting_for_input = False
                                self.paused_node = None
                                print(f"Error: Input value must be a number. Received: '{input_val}'")
                                return None
                        elif not isinstance(input_val, int):
                            self.log(f"Error: Expected numeric input but got {type(input_val).__name__}")
                            self.stopped = True
                            self.completed = True
                            self.waiting_for_input = False
                            self.paused_node = None
                            print(f"Error: Input value must be a number. Received: '{input_val}'")
                            return None
                            
                    elif self.expected_type == "float" or self.expected_type == "flt":
                        # Allow int, bool, or numeric string inputs
                        if isinstance(input_val, int):
                            # int → flt: Add .0
                            input_val = float(input_val)
                            self.log(f"Applied int → flt conversion (add .0): {original_val} → {input_val}")
                        elif isinstance(input_val, bool):
                            # bln → flt: Day → 1.0, Night → 0.0
                            input_val = 1.0 if input_val else 0.0
                            self.log(f"Applied bln → flt conversion: {original_val} → {input_val}")
                        elif isinstance(input_val, str):
                            # Try to convert string input to float
                            try:
                                input_val = float(input_val)
                                self.log(f"Converted string to float: {original_val} → {input_val}")
                            except ValueError:
                                self.log(f"Error: Cannot convert '{input_val}' to float")
                                self.stopped = True
                                self.completed = True
                                self.waiting_for_input = False
                                self.paused_node = None
                                print(f"Error: Input value must be a number. Received: '{input_val}'")
                                return None
                        elif not isinstance(input_val, float):
                            self.log(f"Error: Expected float input but got {type(input_val).__name__}")
                            self.stopped = True
                            self.completed = True
                            self.waiting_for_input = False
                            self.paused_node = None
                            print(f"Error: Input value must be a number. Received: '{input_val}'")
                            return None
                            
                    elif self.expected_type == "bool" or self.expected_type == "bln":
                        # Allow int, float, or boolean string inputs
                        if isinstance(input_val, int):
                            # int → bln: 0 → Night, else Day
                            input_val = False if input_val == 0 else True
                            self.log(f"Applied int → bln conversion: {original_val} → {input_val}")
                        elif isinstance(input_val, float):
                            # flt → bln: 0.0 → Night, else Day
                            input_val = False if input_val == 0.0 else True
                            self.log(f"Applied flt → bln conversion: {original_val} → {input_val}")
                        elif isinstance(input_val, str):
                            # Accept ONLY exact "Day" and "Night" strings
                            if input_val == "Day":
                                input_val = True
                            elif input_val == "Night":
                                input_val = False
                            else:
                                # Try to convert numeric strings to boolean
                                try:
                                    num_val = float(input_val)
                                    input_val = False if num_val == 0 else True
                                    self.log(f"Converted numeric string to boolean: {original_val} → {input_val}")
                                except ValueError:
                                    self.log(f"Error: Cannot convert '{input_val}' to boolean")
                                    self.stopped = True
                                    self.completed = True
                                    self.waiting_for_input = False
                                    self.paused_node = None
                                    print(f"Error: Input value must be a boolean (Day/Night) or a number (0 for Night, other numbers for Day). Received: '{input_val}'")
                                    return None
                        elif not isinstance(input_val, bool):
                            self.log(f"Error: Expected boolean input but got {type(input_val).__name__}")
                            self.stopped = True
                            self.completed = True
                            self.waiting_for_input = False
                            self.paused_node = None
                            print(f"Error: Input value must be a boolean. Received: '{input_val}'")
                            return None
                    
                    # Apply final implicit type casting for consistency
                    input_val = self.convert_type(input_val, self.expected_type)
                    self.log(f"Final input value after conversion: {input_val} (type: {type(input_val).__name__})")
                                
                except Exception as e:
                    self.log(f"Error during input validation: {str(e)}")
                    self.stopped = True
                    self.completed = True
                    self.waiting_for_input = False
                    self.paused_node = None
                    print(f"Error: Invalid input value: '{input_val}'. Expected type: {self.expected_type}")
                    return None
                
            # Reset expected type and assignment target after successful processing
            self.expected_type = None
            
            # If we have more targets in queue, move to the next one
            if self.input_target_queue:
                next_target = self.input_target_queue.pop(0)
                self.current_assignment_target = next_target.get('variable')
                self.expected_type = next_target.get('type')
                self.log(f"Moving to next input target: {self.current_assignment_target} of type {self.expected_type}")
            else:
                self.current_assignment_target = None
            
            # Return the value with appropriate type conversion
            return input_val
        
        # Always set waiting flag and store the current node
        self.paused_node = node
        self.waiting_for_input = True
        
        # Process prompt if available
        prompt = ""
        if len(node.children) > 0:
            # Use first child as prompt if available
            prompt_node = node.children[0]
            if prompt_node:
                prompt = self.execute_node(prompt_node)
                if prompt:
                    # Don't print the prompt here - it will be handled by the frontend
                    pass
        
        # Store the prompt for the frontend to display
        self.input_prompt = prompt
        
        # Make sure we're still paused even after executing the prompt
        self.waiting_for_input = True
        self.paused_node = node
        
        # Force stdout to flush so any previous display statements are visible
        import sys
        sys.stdout.flush()
        
        return None
    
    def provide_input(self, input_value):
        """Process user input and continue execution"""
        self.log(f"Received input: {input_value}")
        
        # Store the raw input value
        self.input_value = input_value
        
        # Mark that we're no longer waiting for input
        self.waiting_for_input = False
        
        # If we have a paused node, do not reprocess it here (we'll do it in execute_node)
        # Just return the input value
        self.log(f"Input processed: {self.input_value}")
        return self.input_value
    
    def is_waiting_for_input(self):
        """Check if the program is waiting for input"""
        print(f"is_waiting_for_input called, status: waiting={self.waiting_for_input}, stopped={self.stopped}, has_paused_node={self.paused_node is not None}")
        # Return False if program is stopped, regardless of waiting_for_input status
        if self.stopped:
            return False
        return self.waiting_for_input
    
    def get_input_prompt(self):
        """Get the current input prompt if waiting for input"""
        return self.input_prompt if self.waiting_for_input else ""

    # ==========================
    #    LOOP EXECUTION
    # ==========================
    
    def execute_for_loop(self, node):
        """Execute a for loop statement"""
        self.log("Executing for_loop")
        
        if len(node.children) < 4:
            self.log("for_loop has insufficient children")
            return None
            
        # The children should be [control_variable, condition, update, statements...]
        control_var_node = node.children[0]
        condition_node = node.children[1]
        update_node = node.children[2]
        
        # Get all statement nodes (everything from index 3 onwards)
        statement_nodes = node.children[3:]
        self.log(f"For loop has {len(statement_nodes)} statement nodes")
        
        # Create a new scope for the loop variables
        self.push_scope()
        
        # Execute the control variable initialization
        try:
            self.execute_control_variable(control_var_node)
        except Exception as e:
            self.log(f"ERROR: Failed to initialize loop control variable: {str(e)}")
            print(f"Error: Failed to initialize loop control variable: {str(e)}")
            self.stopped = True
            self.pop_scope()
            return None
        
        loop_count = 0
        # Loop execution
        while not self.stopped:
            # Safety limit to prevent infinite loops during debugging
            loop_count += 1
            if loop_count > 1000:  # Reasonable limit for most loops
                self.log("ERROR: Loop safety limit reached (1000 iterations)")
                print("Error: Infinite loop detected - exceeded 1000 iterations")
                self.stopped = True
                break
                
            # Check the loop condition - ensuring we handle it as a condition, not a regular expression
            try:
                if condition_node.type == "condition":
                    # If it's already a condition node, use execute_condition
                    condition_result = self.execute_condition(condition_node)
                elif condition_node.type == "for_expression":
                    # Convert for_expression to condition evaluation pattern
                    left_val = self.execute_node(condition_node.children[0])
                    if len(condition_node.children) > 1 and hasattr(condition_node.children[1], 'type') and condition_node.children[1].type == "factor_tail_binop":
                        binop = condition_node.children[1]
                        op_node = binop.children[0]
                        operator = op_node.value
                        right_val = self.execute_node(binop.children[1])
                        
                        # Use apply_comparison for comparison operators
                        if operator in ["==", "!=", ">", "<", ">=", "<="]:
                            condition_result = self.apply_operator(operator, left_val, right_val)
                        else:
                            condition_result = self.apply_operator(operator, left_val, right_val)
                    else:
                        condition_result = bool(left_val)
                else:
                    # Otherwise just try to execute and convert to boolean
                    condition_result = bool(self.execute_node(condition_node))
            except Exception as e:
                self.log(f"ERROR: Failed to evaluate loop condition: {str(e)}")
                print(f"Error: Failed to evaluate loop condition: {str(e)}")
                self.stopped = True
                break
                
            self.log(f"For loop condition result: {condition_result}")
            
            if not condition_result:
                break
                
            # Execute each statement in the loop body
            try:
                for stmt_node in statement_nodes:
                    if self.stopped:
                        break
                        
                    self.log(f"Executing statement of type: {stmt_node.type}")
                    self.execute_node(stmt_node)
                    
                    # Check if waiting for input, and if so, pause execution
                    if self.waiting_for_input:
                        self.log("For loop paused waiting for input")
                        # Save state so we can resume later
                        self.paused_node = node
                        # Exit the loop without popping scope
                        return None
            except Exception as e:
                self.log(f"ERROR: Exception in loop body: {str(e)}")
                print(f"Error: Exception in loop body: {str(e)}")
                self.stopped = True
                break
            
            # Execute the update statement
            try:
                if self.stopped:
                    break
                    
                self.execute_node(update_node)
            except Exception as e:
                self.log(f"ERROR: Failed to execute loop update statement: {str(e)}")
                print(f"Error: Failed to execute loop update statement: {str(e)}")
                self.stopped = True
                break
        
        # Clean up the loop scope
        self.pop_scope()
        return None
        
    def execute_control_variable(self, node):
        """Execute a control variable initialization"""
        self.log("Executing control_variable")
        
        if len(node.children) < 3:
            self.log("control_variable has insufficient children")
            return None
            
        # Get the variable name and data type
        data_type_node = node.children[0]
        ident_node = node.children[1]
        init_value_node = node.children[2]
        
        var_name = ident_node.value.lstrip('$')
        data_type = data_type_node.value
        
        # Execute the initial value
        initial_value = self.execute_node(init_value_node)
        
        # Apply type conversion based on the variable's declared data type
        if initial_value is not None and data_type:
            original_value = initial_value
            initial_value = self.convert_type(initial_value, data_type)
            self.log(f"Applied type conversion for control variable: {type(original_value).__name__} -> {data_type}: {original_value} -> {initial_value}")
        
        # Assign the variable to the current scope
        self.get_current_env()[var_name] = initial_value
        self.log(f"Initialized loop control variable '{var_name}' = {initial_value}")
        
        return initial_value
        
    def execute_update(self, node):
        """Execute an update statement"""
        self.log("Executing update")
        
        if len(node.children) < 2:
            self.log("update has insufficient children")
            return None
            
        var_call_node = node.children[0]
        update_tail_node = node.children[1]
        
        # Get the variable name from var_call
        var_name = None
        if hasattr(var_call_node, 'children') and var_call_node.children:
            ident_node = var_call_node.children[0]
            if hasattr(ident_node, 'value'):
                var_name = ident_node.value.lstrip('$')
        
        if not var_name:
            self.log("Could not find variable name in update")
            return None
            
        # Get the current value of the variable
        current_value = self.lookup_variable(var_name)
        if current_value is None:
            self.log(f"Variable '{var_name}' not found or None value")
            return None
        
        self.log(f"Current value of '{var_name}' is {current_value}")
        
        if hasattr(update_tail_node, 'type'):
            if update_tail_node.type == "update_tail_postfix":
                # Handle ++ or -- operations
                postfix_op = update_tail_node.value
                
                if postfix_op == "++":
                    new_value = current_value + 1
                    self.log(f"Incrementing '{var_name}' from {current_value} to {new_value}")
                elif postfix_op == "--":
                    new_value = current_value - 1
                    self.log(f"Decrementing '{var_name}' from {current_value} to {new_value}")
                else:
                    self.log(f"Unknown postfix operator: {postfix_op}")
                    return None
                    
                # Ensure the value is an integer to avoid type issues
                if isinstance(current_value, int):
                    new_value = int(new_value)
                
                self.log(f"Updating variable '{var_name}' from {current_value} to {new_value} with {postfix_op}")
                self.assign_variable(var_name, new_value)
                return new_value
                
            elif update_tail_node.type == "update_tail_compound":
                # Handle compound operators like +=, -=, etc.
                if len(update_tail_node.children) < 2:
                    self.log("Invalid update_tail_compound structure")
                    return None
                    
                compound_op = update_tail_node.children[0]
                value_node = update_tail_node.children[1]
                
                update_value = self.execute_node(value_node)
                
                if compound_op == "+=":
                    new_value = current_value + update_value
                elif compound_op == "-=":
                    new_value = current_value - update_value
                elif compound_op == "*=":
                    new_value = current_value * update_value
                elif compound_op == "/=":
                    if update_value == 0:
                        self.log("Error: Division by zero in update")
                        return None
                    new_value = current_value / update_value
                elif compound_op == "%=":
                    if update_value == 0:
                        self.log("Error: Modulo by zero in update")
                        return None
                    new_value = current_value % update_value
                else:
                    self.log(f"Unknown compound operator: {compound_op}")
                    return None
                
                # Ensure consistent type
                if isinstance(current_value, int):
                    new_value = int(new_value)
                    
                self.log(f"Updating variable '{var_name}' from {current_value} to {new_value} with {compound_op}")
                self.assign_variable(var_name, new_value)
                return new_value
        
        self.log("Unknown update tail type")
        return None

    def stop_execution(self):
        """Stop the execution of the program"""
        self.stopped = True

    def print_ast_structure(self, node, level=0):
        """Debug helper to print AST structure"""
        if node is None:
            return
            
        if isinstance(node, list):
            for item in node:
                self.print_ast_structure(item, level+2)
            return
            
        # Print node type and value if available
        node_str = f"{node.type}" if hasattr(node, 'type') else str(node)
        if hasattr(node, 'value') and node.value is not None:
            node_str += f" (value={node.value})"
        
        # Print children recursively
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                self.print_ast_structure(child, level+2)
                
    def print_parent_nodes(self):
        """Debug helper to print parent nodes stack"""
        print("PARENT NODES STACK:")
        for i, node in enumerate(self.parent_nodes):
            node_type = node.type if hasattr(node, 'type') else str(node)
            print(f"  {i}: {node_type}")

    def evaluate_logical_expression(self, left_value, binop_node):
        """Special handler for logical expressions with AND/OR to ensure correct precedence"""
        self.log(f"LOGICAL DEBUG: Evaluating logical expression with left value: {left_value}")
        
        if not binop_node or not binop_node.children:
            return bool(left_value)
        
        operator_node = binop_node.children[0]
        right_node = binop_node.children[1]
        tail_node = binop_node.children[2] if len(binop_node.children) > 2 else None
        
        # Get the operator value
        operator = operator_node.value if hasattr(operator_node, 'value') else operator_node
        
        # Evaluate the right side 
        right_value = self.execute_node(right_node)
        
        self.log(f"LOGICAL DEBUG: Operator: {operator}, Right value: {right_value}")
        
        # Apply the operator with proper type conversions
        if operator == "&&":
            result = bool(left_value) and bool(right_value)
        elif operator == "||":
            result = bool(left_value) or bool(right_value)
        else:
            # For other operators, use regular apply_operator
            result = self.apply_operator(operator, left_value, right_value)
        
        self.log(f"LOGICAL DEBUG: Operation result: {left_value} {operator} {right_value} = {result}")
        
        # If there's a tail with more operations, evaluate it with the current result as the left value
        if tail_node is not None:
            result = self.evaluate_logical_expression(result, tail_node)
        
        return result

def run_code_generation(ast):
    """Create a CodeGenerator and run code generation on the given AST."""
    
    generator = CodeGenerator()
    generator.debug = True
    
    # Create global scope
    generator.global_vars = {}
    generator.env_stack = [generator.global_vars]
    
    try:
        generator.generate(ast)
    except Exception as e:
        import traceback
        traceback.print_exc()
    
    return generator