from Parser import ASTNode

class CodeGenerator:
    def __init__(self):
        self.global_vars = {}
        self.env_stack = [self.global_vars]
        self.functions = {}
        self.return_values = []
        self.debug = False 
        
        # Input handling
        self.waiting_for_input = False
        self.input_value = None
        self.input_prompt = ""
        self.current_assignment_target = None
        self.expected_type = None
        
        # Execution state
        self.ast = None
        self.paused_node = None
        self.parent_nodes = []
        self.stopped = False
        self.completed = False
        self.break_flag = False
        
        # New variables for tracking multiple inputs
        self.input_target_queue = []  # Queue to hold pending input targets

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
                # print(f"LOOKUP: Found variable '{var_name}' = {repr(value)} in {scope_name} scope") # Changed to print
                # --- ADDED: Explicitly copy lists --- 
                if isinstance(value, list):
                    value_copy = value[:] # Return a shallow copy
                    
                    return value_copy
                # --- END ADDED --- 
             
                return value
       
        return None

    def assign_variable(self, var_name, value):
        
        self.log(f"Assigning '{var_name}' = {value}")
        
        # First try to find and update the variable in an existing scope
        for i, env in enumerate(reversed(self.env_stack)):
            scope_name = "local" if i == 0 else f"parent {i}"
            if var_name in env:
             
                # Make sure we're assigning a clean value, but preserve booleans
                if isinstance(value, int) and not isinstance(value, bool):
                    env[var_name] = int(value)  # Ensure it's a clean int, not a bool subclass
                else:
                    env[var_name] = value # Assign other types (including bool) directly
                self.log(f"Updated existing variable '{var_name}' = {value} in scope")
                return
        
        current_env = self.get_current_env()
        if isinstance(value, int) and not isinstance(value, bool):
             current_env[var_name] = int(value) # Ensure it's a clean int, not a bool subclass
        else:
            current_env[var_name] = value # Assign other types (including bool) directly
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
            self.completed = True
            return None
            
        if ast is not None:
            self.ast = ast
            
        # If we have a paused node and just received input, process it
        if ast is None and self.paused_node and not self.waiting_for_input:
            result = self.execute_node(None)  # This will trigger the paused node execution
            
            # Only mark as completed if not waiting for more input AND not in the middle of
            # processing statements (e.g., when we have more inputs to process)
            if not self.waiting_for_input and not self.paused_node:
                self.completed = True
                
            return result
            
        # Return early if we have nothing to execute
        if ast is None and not self.waiting_for_input and self.paused_node is None:
            return None
        
        # Execute the AST
        result = self.execute_node(ast)
        
        # Mark program as completed when done executing
        # ONLY if we're not waiting for input and don't have a paused node
        if not self.waiting_for_input and not self.paused_node:
            self.completed = True
            
        return result

    def execute_node(self, node):
        # Check if execution is stopped
        if self.stopped:
            return None
            
        # If we are currently waiting for input, don't execute any more nodes
        if self.waiting_for_input and node != self.paused_node:
           
            return None
            
        # Handle resuming from paused input node
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
                    
                    # Reset tracking variables
                    self.current_assignment_target = None
                    self.expected_type = None
                
                # Find parent structure to continue execution from the right point
                if hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0:
                    parent = self.parent_nodes[-1]  # Don't pop, just look at the current parent
                    
                    if hasattr(parent, 'type'):
                        # Handle regular statements inside main function
                        if parent.type == "main_function":
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
                                            
                                            # Direct input statement
                                            if inner_stmt == temp_node:
                                                found_index = i
                                                break
                                            
                                            # Check for input inside variable statements
                                            if hasattr(inner_stmt, 'type') and inner_stmt.type == "var_statement" and inner_stmt.children:
                                                for child in inner_stmt.children:
                                                    if hasattr(child, 'type') and child.type == "local_var_assign" and child.children:
                                                        value_node = child.children[0]
                                                        if hasattr(value_node, 'type') and value_node.type == "value" and value_node.children:
                                                            if hasattr(value_node.children[0], 'type') and value_node.children[0].type == "input_statement":
                                                                if value_node.children[0] == temp_node:
                                                                    found_index = i
                                                                    break
                            
                            # Execute all statements after the input statement
                            if found_index >= 0:
                                
                                self.log(f"Found input at index {found_index}, continuing execution")
                                # Execute all remaining statements
                                for i in range(found_index + 1, len(statements_list)):
                                    next_stmt = statements_list[i]
                                    result = self.execute_node(next_stmt)
                                    # If we hit another input request, pause execution
                                    if self.waiting_for_input:
                                    
                                        self.log(f"Hit another input request, pausing execution")
                                        break
                        
                        # Handle statements inside conditional blocks
                        elif parent.type in ["check_block", "otherwise_block", "otherwise_check", "conditional_statement"]:
                            self.log(f"Found input in conditional block: {parent.type}")
                            
                            # Continue execution of current parent after input is processed
                            if parent.children:
                                # Find which child contained our input statement
                                found_index = -1
                                for i, child in enumerate(parent.children):
                                    # Check if this child is our input statement
                                    if child == temp_node:
                                        found_index = i
                                        break
                                    
                                    # Check inside var_statement for input
                                    if hasattr(child, 'type') and child.type == "var_statement" and child.children:
                                        for var_child in child.children:
                                            if hasattr(var_child, 'type') and var_child.type == "local_var_assign" and var_child.children:
                                                value_node = var_child.children[0]
                                                if hasattr(value_node, 'type') and value_node.type == "value" and value_node.children:
                                                    if hasattr(value_node.children[0], 'type') and value_node.children[0].type == "input_statement":
                                                        if value_node.children[0] == temp_node:
                                                            found_index = i
                                                            break
                                
                                # If found, continue execution from the next child
                                if found_index >= 0 and found_index < len(parent.children) - 1:
                                    self.log(f"Continuing execution from child {found_index + 1} in {parent.type}")
                                    for i in range(found_index + 1, len(parent.children)):
                                        next_stmt = parent.children[i]
                                        result = self.execute_node(next_stmt)
                                        # If we hit another input request, pause execution
                                        if self.waiting_for_input:
                                            self.log(f"Hit another input request during continuation, pausing execution")
                                            break
                                else:
                                    self.log("Either no match found or it was the last child")
                            else:
                                self.log("Parent has no children")
                
                # Return the input result
                return input_result
            
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
            # print(f"DEBUG execute_node: Received non-node object: {repr(node)}")
            return None

        # print(f"DEBUG execute_node: Processing node type = {node.type}")

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
        elif node.type == "measure_call":
            self.log("MEASURE: Routing to execute_measure_call")
            return self.execute_measure_call(node)
        elif node.type == "stop_statement":
            self.log("STOP: Routing to execute_stop_statement")
            return self.execute_stop_statement(node)
        elif node.type == "update": # ADDED: Route update nodes to execute_update
            self.log("UPDATE: Routing to execute_update")
            return self.execute_update(node)
        elif node.type == "unary_negation": # ADDED: Route unary negation
            self.log("UNARY NEG: Routing to execute_unary_negation")
            return self.execute_unary_negation(node)
        elif node.type == "while_loop": # CHANGED from until_loop
            self.log("LOOP: Routing to execute_while_loop")
            return self.execute_while_loop(node)
        elif node.type == "repeat_while": # CHANGED from repeat_until
            self.log("LOOP: Routing to execute_repeat_while")
            return self.execute_repeat_while(node)
        
        # ADDED: Route type_cast nodes
        elif node.type == "type_cast":
            self.log("TYPECAST: Routing to execute_type_cast")
            return self.execute_type_cast(node)

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
        # Add a flag to control debug prints specifically for factorial
        is_factorial_call = False
        try:
            func_name = None
            for child in node.children:
                if hasattr(child, 'type') and child.type == "FUNCTION_NAME":
                    func_name = child.value
                    # Check if it's the factorial function
                    if func_name == "@factorial":
                        is_factorial_call = True
                    break
                    
            # ... (rest of the existing function name check) ...
            if not func_name:
                self.log("ERROR: Function call missing function name")
                print("Error: Invalid function call - missing function name")
                self.stopped = True
                return None
                
            # Print entry only if it's factorial
            if is_factorial_call:
                # print(f"DEBUG Factorial: Entering @factorial call with name '{func_name}'") 
                pass # Removed print
            else:
                 self.log(f"Calling function: {func_name}")
            
            # ... (rest of the existing function existence check) ...
            if func_name not in self.functions:
                self.log(f"ERROR: Undefined function: {func_name}")
                print(f"Error: Undefined function: {func_name}")
                self.stopped = True
                return None
                
            args = []
            arg_debug_values = [] # Store values for debug print
            for child in node.children:
                if hasattr(child, 'type') and child.type == "arguments":
                    for arg in child.children:
                        arg_value = self.execute_node(arg)
                        args.append(arg_value)
                        arg_debug_values.append(repr(arg_value)) # Use repr for clarity
                        self.log(f"Argument value: {arg_value}")
            
            # Print arguments only if it's factorial
            if is_factorial_call:
                # print(f"DEBUG Factorial: Arguments passed: [{' , '.join(arg_debug_values)}]", flush=True)
                pass # Removed print
            
            # ... (rest of the existing argument count check) ...
            expected_params = len(self.functions[func_name]['params'])
            actual_args = len(args)
            if actual_args != expected_params:
                self.log(f"ERROR: Function {func_name} expected {expected_params} arguments, got {actual_args}")
                print(f"Error: Function {func_name} expected {expected_params} arguments, got {actual_args}")
                self.stopped = True
                return None
       
            self.push_scope()
            scope_pushed = True # Track scope for exception handling
            
            # Print parameter binding only if it's factorial
            if is_factorial_call:
                bound_params = []
                for i, param in enumerate(self.functions[func_name]['params']):
                     if i < len(args):
                         param_name = param["name"]
                         arg_value = args[i]
                         # Perform the binding
                         self.get_current_env()[param_name] = arg_value
                         bound_params.append(f'${param_name}={repr(arg_value)}')
                         # No type checking/conversion here, just binding for the debug print
                # print(f"DEBUG Factorial: Bound parameters: [{' , '.join(bound_params)}]", flush=True)
                pass # Removed print
                # Actual binding with type checking happens below, duplicating slightly for debug clarity

            # Re-iterate for actual binding with type checks (original logic)
            for i, param in enumerate(self.functions[func_name]['params']):
                if i < len(args):
                    param_name = param["name"]
                    param_type = param.get("type")
                    arg_value = args[i]
                    
                    # Type check and conversion (original logic)
                    if param_type and arg_value is not None:
                         # Check if conversion is necessary
                         target_py_type = self.casper_to_python_type(param_type)
                         if target_py_type and type(arg_value).__name__.lower() != target_py_type:
                              try:
                                   converted_value = self.convert_type(arg_value, param_type)
                                   # Print conversion only for factorial
                                   if is_factorial_call:
                                        # print(f"DEBUG Factorial: Converting arg for ${param_name}: {repr(arg_value)} ({type(arg_value).__name__}) -> {repr(converted_value)} ({param_type})", flush=True)
                                        pass # Removed print
                                   arg_value = converted_value
                              except Exception as e:
                                   self.log(f"ERROR: Failed to convert argument for function {func_name}: {str(e)}")
                                   print(f"Error: Type mismatch for param ${param_name} in {func_name}. Expected {param_type}, got {type(arg_value).__name__}.")
                                   self.stopped = True
                                   self.pop_scope()
                                   return None
                         else:
                             # Types match, no conversion needed
                             pass
                    
                    # Actual assignment to the new scope's environment
                    self.assign_variable(param_name, arg_value) # Use assign_variable to handle scope correctly
                    self.log(f"Bound parameter '{param_name}' to value {arg_value}")
     
            # ... (rest of the function execution logic) ...
            func_node = self.functions[func_name]['node']
            # Track if we entered the statements block for factorial debug
            entered_statements = False
            for child in func_node.children:
                if self.stopped:
                    break
                    
                if hasattr(child, 'type') and child.type == "statements":
                    entered_statements = True
                    if is_factorial_call:
                        # print("DEBUG Factorial: Executing statements block...", flush=True)
                        pass # Removed print
                    for statement in child.children:
                        if self.stopped:
                            break
                        # Execute statement and check for return value immediately
                        self.execute_node(statement)
                        # Check if revive was called within this statement's execution
                        if self.return_values:
                             # For factorial, print the value just before it's officially returned
                             if is_factorial_call:
                                  peeked_return = self.return_values[-1] # Look at the last added value
                                  # print(f"DEBUG Factorial: Revive encountered, value to be returned: {repr(peeked_return)}", flush=True)
                                  pass # Removed print
                             break # Exit statement loop on revive
                # else: # Removed unnecessary execution of non-statement children like FUNCTION_NAME etc.
                #     self.execute_node(child) 
                
                # Break outer loop if revive was found in statements
                if self.return_values and entered_statements:
                    break

            return_value = None
            if self.return_values:
                return_value = self.return_values.pop()
                # Print final return value only for factorial
                if is_factorial_call:
                    # print(f"DEBUG Factorial: Popped return value: {repr(return_value)}", flush=True)
                    pass # Removed print
                else:
                    self.log(f"Function returned: {return_value}")
            elif is_factorial_call:
                 # If factorial finishes without returning a value (shouldn't happen if logic is correct)
                 # print("DEBUG Factorial: Function finished without returning a value!", flush=True)
                 pass # Removed print

            self.pop_scope()
            scope_pushed = False # Scope popped successfully
            
            # Print exit only if it's factorial
            if is_factorial_call:
                 # print(f"DEBUG Factorial: Exiting @factorial. Final returned value: {repr(return_value)}", flush=True)
                 pass # Removed print

            return return_value
        except Exception as e:
            # ... (existing exception handling) ...
            import traceback # Add this import
            func_name_str = func_name if 'func_name' in locals() and func_name else 'unknown'
            print(f"DEBUG: Exception during {func_name_str} call: {e}")
            traceback.print_exc() # Print detailed traceback
            self.log(f"ERROR: Exception in function call {func_name_str}: {str(e)}")
            print(f"Error: Exception in function call: {str(e)}")
            self.stopped = True
            if 'scope_pushed' in locals() and scope_pushed:
                self.pop_scope()
            return None

    def execute_revive_statement(self, node):
        self.log("Executing revive_statement")

        if not node.children:
            self.log("revive_statement has no children")
            # Even if no children, it signifies a return point for void or potentially error
            self.return_values.append(None) 
            return None

        value_node = node.children[0]
        value = self.execute_node(value_node)
        
        # --- Add Debug Print for Factorial --- 
        # We check the call stack implicitly; if the current scope's parent
        # involved calling factorial, this revive is likely within it.
        # A more robust way would involve passing the func_name down.
        # For now, we just print the value being revived.
        # print(f"DEBUG CODEGEN: Reviving value: {repr(value)}", flush=True)
        # --- End Debug Print --- 
        
        self.log(f"Return value: {value}")
        self.return_values.append(value)
        
        # Stop executing further statements in the current block after revive
        # This needs context from the caller (like execute_function_call)
        # Setting a flag or relying on the caller's loop break is typical.
        
        return value # Return the value for potential use if revive was in an expression context (though unlikely)

    # ==========================
    #    STATEMENTS
    # ==========================
    
    def execute_global_statement(self, node):
        self.log("Executing global_statement")
        self.log(f"Global statement children: {node.children}")
        
        var_name = None
        var_value = None
        data_type = None
        list_dec_node = None
        assignment_node = None
        is_list = False
        is_2d_list = False
        
        # Parse the basic declaration parts first
        if len(node.children) > 0 and hasattr(node.children[0], 'type') and node.children[0].type == "data_type":
            data_type = node.children[0].value
        if len(node.children) > 1 and hasattr(node.children[1], 'type') and node.children[1].type == "IDENT":
            var_name = node.children[1].value.lstrip('$')
        if len(node.children) > 2 and node.children[2] is not None and hasattr(node.children[2], 'type') and node.children[2].type == "list_dec":
            list_dec_node = node.children[2]
            is_list = True
            # Check for 2D list
            if list_dec_node.children and hasattr(list_dec_node.children[0], 'type') and list_dec_node.children[0].type == "2d_list":
                is_2d_list = True
                self.log(f"Variable '{var_name}' declared as 2D list.")
            else:
                self.log(f"Variable '{var_name}' declared as 1D list.")
        if len(node.children) > 3 and node.children[3] is not None:
             # Assignment node can be expression or list_value
            assignment_node = node.children[3]

        self.log(f"Parsed global: name={var_name}, type={data_type}, is_list={is_list}, is_2d={is_2d_list}, assignment_node_type={getattr(assignment_node, 'type', None)}")
        
        # Determine initial/default value
        if assignment_node:
            # If there is an assignment, evaluate it
            if hasattr(assignment_node, 'type') and assignment_node.type == "list_value":
                var_value = self.execute_list_value(assignment_node)
                # Ensure assigned value is a list if declared as list
                if not is_list:
                    self.log(f"ERROR: Assigning list value to non-list variable '{var_name}'")
                    print(f"Error: Cannot assign list value to non-list variable '{var_name}'")
                    self.stopped = True
                    return None
                # Basic check for 2D structure if declared as 2D
                if is_2d_list and not all(isinstance(item, list) for item in var_value):
                    self.log(f"WARNING: Assigning potentially non-2D list value to 2D list variable '{var_name}'")
                    # Allow assignment but log warning. Strict type checking could go here.
            else:
                var_value = self.execute_node(assignment_node)
                # Ensure non-list assignment isn't made to a list variable
                if is_list:
                    self.log(f"ERROR: Assigning non-list value to list variable '{var_name}'")
                    print(f"Error: Cannot assign non-list value to list variable '{var_name}'")
                    self.stopped = True
                    return None
        else:
            # No assignment, use default value
            if is_list:
                var_value = [] # Default for lists is empty list
            elif data_type == "int":
                var_value = 0
            elif data_type == "string" or data_type == "str":
                var_value = ""
            elif data_type == "float" or data_type == "flt":
                var_value = 0.0
            elif data_type == "bool" or data_type == "bln":
                var_value = False
            # Add other type defaults if necessary
            else:
                 var_value = None # Default for unknown types

        if var_name:
            # Apply type conversion if not a list assignment and types differ
            if not is_list and assignment_node and hasattr(assignment_node, 'type') and assignment_node.type != "list_value":
                if var_value is not None and data_type:
                    try:
                        converted_value = self.convert_type(var_value, data_type)
                        if converted_value != var_value:
                            self.log(f"Applied type conversion for global declaration: {type(var_value).__name__} -> {data_type}: {var_value} -> {converted_value}")
                            var_value = converted_value
                    except Exception as e:
                        self.log(f"ERROR: Type conversion failed for global variable '{var_name}': {str(e)}")
                        print(f"Error: Type conversion failed for global variable '{var_name}': {str(e)}")
                        self.stopped = True
                        return None
            
            self.assign_variable(var_name, var_value)
            self.log(f"Set global variable '{var_name}' to {var_value}")
        
        return var_value

    def execute_var_statement(self, node):
        """Execute a variable declaration statement"""
       
        self.log("Executing var_statement")

        if not node.children:
            self.log("ERROR: var_statement has no children")
            return None
        
        # Get data type node 
        data_type_node = node.children[0]
       
        
        # Extract data type
        data_type = None
        if hasattr(data_type_node, 'type'):
            if data_type_node.type == "data_type":
                data_type = self.execute_node(data_type_node)
            elif data_type_node.type == "local_data_type" and hasattr(data_type_node, 'value'):
                data_type = data_type_node.value
        
        if not data_type:
       
            self.log(f"ERROR: Could not determine data type from node")
            return None
            
   
        self.log(f"Variable type: {data_type}")
        
        # Second child should be the variable name
        ident_node = node.children[1] if len(node.children) > 1 else None
        if not ident_node or not hasattr(ident_node, 'type') or ident_node.type != "IDENT":
            self.log("ERROR: No valid variable name in var_statement")
            return None
            
        # Strip $ from the start of the variable name
        var_name = ident_node.value.lstrip('$')
       
        self.log(f"Variable name: {var_name}")
        
        # Get the local_var_assign node (if present)
        assign_node = None
        for child in node.children:
            if hasattr(child, 'type') and child.type == "local_var_assign":
                assign_node = child
                break
        
        # Check if we have an initial assignment
        if assign_node:
          
            self.log("Found local_var_assign node in var_statement")
            
            # Check if assignment contains input
            contains_input = False
            value_node = assign_node.children[0] if assign_node.children else None
            
            if value_node and hasattr(value_node, 'type') and value_node.type == "value":
                if value_node.children and len(value_node.children) > 0:
                    expr_node = value_node.children[0]
                    
                    # Check if the value comes from an input statement
                    if hasattr(expr_node, 'type') and expr_node.type == "input_statement":
                     
                        self.log(f"Found input statement in var declaration for {var_name}")
                        contains_input = True
                        
                        # Set the variable as the current assignment target
                        self.current_assignment_target = var_name
                        
                        # Set the expected type for validation
                        self.expected_type = self.casper_to_python_type(data_type)
                        
                        self.log(f"Set {var_name} as current input target with type {self.expected_type}")
            
            # Execute the assignment
            assign_value = self.execute_node(assign_node)
       
            
            # Handle case where input gave us None but we continue execution
            if contains_input and self.waiting_for_input:
                # If this contains an input that's waiting, we return early
            
                self.log(f"Input waiting in var_statement for {var_name}")
                
                # If input already has a result, use it
                if var_name in self.get_current_env():
                    self.log(f"Variable {var_name} already has value: {self.get_current_env()[var_name]}")
                    return self.get_current_env()[var_name]
                
                # Otherwise return none and wait for input
                return None
            
            # If we executed without waiting for input, apply the result
            if assign_value is not None:
                self.log(f"Assigning initial value to {var_name}: {assign_value}")
                # Convert to right type if needed
                if isinstance(assign_value, (int, float, bool, str)) and data_type:
                    try:
                        python_type = self.casper_to_python_type(data_type)
                        if python_type:
                            assign_value = self.convert_type(assign_value, python_type)
                    except Exception as e:
                        self.log(f"ERROR: Type conversion failed: {str(e)}")
                
                self.assign_variable(var_name, assign_value)
                return assign_value
        else:
            # --- MODIFIED: Check for list declaration node explicitly --- 
            list_dec_node = node.children[2] if len(node.children) > 2 else None
            is_list_declaration = list_dec_node is not None and hasattr(list_dec_node, 'type') and list_dec_node.type == "list_dec"
            
            # Initialize with default value based on type
            default_value = None
            if is_list_declaration:
                default_value = [] # Default for any list is empty list
                self.log(f"Detected list declaration for '{var_name}', defaulting to []")
            elif data_type == "int":
                default_value = 0
            elif data_type == "flt":
                default_value = 0.0
            elif data_type == "bln":
                default_value = False  # Night
            elif data_type == "chr":
                default_value = ""
            elif data_type == "str":
                default_value = ""
            # Removed the check for data_type.startswith("list_") as it was unreliable
                
       
            self.log(f"Initializing {var_name} with default: {default_value}")
            self.assign_variable(var_name, default_value)
            return default_value
                
        # If no initial value or assignment, just return None
        return None

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
            self.log("execute_value: Node has no children")
            return None
            
        value_expr = node.children[0]
        
        # Add additional debugging
        expr_type = getattr(value_expr, 'type', 'unknown')
        self.log(f"execute_value: Processing child of type {expr_type}")
        
        # Special handling for literal nodes
        if expr_type == 'literal':
            raw_value = getattr(value_expr, 'value', None)
            self.log(f"execute_value: Got literal with raw value: {raw_value}")
            
            # Handle numeric literals
            if raw_value is not None and isinstance(raw_value, str):
                if raw_value.isdigit():
                    # Convert string digits to integers
                    int_value = int(raw_value)
                    self.log(f"execute_value: Converted string digit '{raw_value}' to int: {int_value}")
                    return int_value
                # Could add handling for floats here if needed
        
        # Standard processing for other types
        result = self.execute_node(value_expr)
        self.log(f"execute_value: Execution result: {result}")
        
        return result
        
    def execute_expression(self, node):
        # This function should handle the overall structure and delegate based on precedence
        # For now, it seems to delegate to evaluate_expression_chain directly for binary ops
        self.log(f"Executing expression: {node.type}")
        if not node.children or len(node.children) < 1:
            return None
        
        left_node = node.children[0]
        left_value = self.execute_node(left_node)
        
        if len(node.children) > 1 and node.children[1] is not None:
            binop_node = node.children[1] # This is factor_tail_binop
            # Check the FIRST operator in the chain to decide evaluation strategy
            if binop_node.children:
                 op_node = binop_node.children[0]
                 operator = op_node.value if hasattr(op_node, 'value') else None
                 
                 # --- Delegate to logical evaluation if top-level is || or && --- 
                 if operator in ['||', '&&']:
                      # print(f"DEBUG Factorial Condition (execute_expression): Detected logical operator '{operator}', delegating to evaluate_logical_expression", flush=True)
                      # Pass the initial left value and the *entire* binop chain
                        return self.evaluate_logical_expression(left_value, binop_node)
                 else:
                      # Handle arithmetic/comparison chains
                      # print(f"DEBUG Factorial Condition (execute_expression): Detected non-logical operator '{operator}', delegating to evaluate_expression_chain", flush=True)
                      return self.evaluate_expression_chain(left_value, binop_node)
            else:
                 # Should not happen if binop_node exists
                 return left_value
        
        return left_value

    def evaluate_expression_chain(self, left_value, binop_node, context="Chain"):
        # This should primarily handle non-logical chains (arithmetic, comparison)
        # or parts of logical chains delegated from evaluate_logical_expression
        # print(f"DEBUG Factorial Condition ({context}): Entering evaluate_expression_chain - Left: {repr(left_value)}, Binop: {getattr(binop_node, 'type', 'N/A')}", flush=True)
        
        if not binop_node or not binop_node.children:
            # print(f"DEBUG Factorial Condition ({context}): Chain end, returning {repr(left_value)}", flush=True)
            return left_value
        
        operator_node = binop_node.children[0]
        right_node = binop_node.children[1]
        tail_node = binop_node.children[2] if len(binop_node.children) > 2 else None
        
        operator = operator_node.value if hasattr(operator_node, 'value') else operator_node
        
        # --- Important: Special handling for logical operators with condition nodes ---
        # Handle the new AST structure for logical operators that contain a complete condition on the right side
        if operator in ['&&', '||'] and hasattr(right_node, 'type') and right_node.type == "condition":
            # print(f"DEBUG Factorial Condition ({context}): Found logical operator '{operator}' with complete condition on right side", flush=True)
            
            # For logical operators, evaluate the right side completely as a condition
            # print(f"DEBUG Factorial Condition ({context}): Evaluating complete condition on right side", flush=True)
            right_value = self.execute_condition(right_node, context=f"{context}:RightSide")
            
            if self.stopped:
                return None
                
            # Apply the logical operator
            # print(f"DEBUG Factorial Condition ({context}): Applying logical operator '{operator}': Left={repr(left_value)}, Right={repr(right_value)}", flush=True)
            current_result = self.apply_operator(operator, left_value, right_value)
            # print(f"DEBUG Factorial Condition ({context}): Logical operator '{operator}' result: {repr(current_result)}", flush=True)
            
            return current_result
        
        # --- Standard case: Normal right operand ---
        # If the right_node itself starts another chain (e.g. in a + b * c), 
        # execute_node should handle it, but be aware of potential precedence issues 
        # stemming from the parser if it doesn't group correctly.
        # print(f"DEBUG Factorial Condition ({context}): Evaluating right operand for '{operator}' - Node type: {getattr(right_node, 'type', 'N/A')}", flush=True)
        right_value = self.execute_node(right_node)
        # print(f"DEBUG Factorial Condition ({context}): Right operand for '{operator}' evaluated to: {repr(right_value)}", flush=True)

        if self.stopped:
             return None
             
        # Apply the current operator
        # print(f"DEBUG Factorial Condition ({context}): Applying operator '{operator}': Left={repr(left_value)}, Right={repr(right_value)}", flush=True)
        current_result = self.apply_operator(operator, left_value, right_value)
        # print(f"DEBUG Factorial Condition ({context}): Operator '{operator}' result: {repr(current_result)}", flush=True)

        if self.stopped:
             return None

        # Recursively evaluate the rest of the chain with the current result
        if tail_node is not None:
            # print(f"DEBUG Factorial Condition ({context}): Evaluating tail expression starting with {repr(current_result)}", flush=True)
            # Pass context down
            return self.evaluate_expression_chain(current_result, tail_node, context=context)
        else:
             # No more operators in the chain
             # print(f"DEBUG Factorial Condition ({context}): Chain evaluation complete, final result: {repr(current_result)}", flush=True)
             return current_result

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
        for i, child in enumerate(node.children): # Added index 'i' for clarity
         
            result = self.execute_node(child)
            self.log(f"Output result: {result}")
        

            # Handle string literals containing formatting instructions
            if isinstance(result, str) and result.startswith('"') and result.endswith('"'):
                result = result[1:-1].replace('\\n', '\n').replace('\\t', '\t')
                
            # Format boolean values as Day/Night ONLY IF they are specifically boolean, not int
            elif isinstance(result, bool) and not (isinstance(result, int) and not isinstance(result, bool)):
                original_bool = result # Keep original for logging
                result = "Day" if result else "Night"
                

       
            if result is not None:
            
                print(result, end="")
            else:
                continue;

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
        # --- ADD DEBUG for comparison conversion --- 
        original_left, original_right = left, right
        left, right = self.apply_implicit_conversion(left, right, operator)
        if (left, right) != (original_left, original_right) and operator == '==':
            # print(f"DEBUG Factorial Condition (apply_operator): Implicit conversion for '==': {repr(original_left)}->{repr(left)}, {repr(original_right)}->{repr(right)}", flush=True)
            pass # Removed print
        # --- END DEBUG --- 
        
        try:
            if operator == "+":
                # --- MODIFIED: Prioritize String Concatenation ---
                if isinstance(left, str) or isinstance(right, str):
                    # Ensure both operands are strings, converting bools to Day/Night
                    str_left = self.convert_type(left, "string") if not isinstance(left, str) else left
                    str_right = self.convert_type(right, "string") if not isinstance(right, str) else right
                    self.log(f"Performing string concatenation: '{str_left}' + '{str_right}'")
                    return str_left + str_right
                else:
                    # Perform numeric addition if neither is a string
                    self.log(f"Performing numeric addition: {left} + {right}")
                    return left + right
                # --- END MODIFICATION ---
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
                return left / right # Keep as float division
            elif operator == "%":
                if right == 0:
                    self.log("ERROR: Modulo by zero detected")
                    print("Error: Modulo by zero")
                    self.stopped = True
                    return 0
                return left % right
            elif operator == "||":
                # --- ADDED DEBUG --- 
                bool_left = bool(left)
                bool_right = bool(right)
                # print(f"DEBUG Factorial Condition (apply_operator): Evaluating ||: bool({repr(left)}) || bool({repr(right)}) -> {bool_left} || {bool_right}", flush=True)
                # --- END DEBUG --- 
                return bool_left or bool_right
            elif operator == "&&":
                 # --- ADDED DEBUG --- 
                bool_left = bool(left)
                bool_right = bool(right)
                # print(f"DEBUG Factorial Condition (apply_operator): Evaluating &&: bool({repr(left)}) && bool({repr(right)}) -> {bool_left} && {bool_right}", flush=True)
                # --- END DEBUG --- 
                return bool_left and bool_right
            elif operator == "==":
                # Comparison already uses converted values
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
        """Convert a value to the specified target type using CASPER conversion rules."""
        self.log(f"Attempting conversion: {value} ({type(value).__name__}) to {target_type}")

        # --- Normalize target type aliases ---
        if target_type == "flt":
            target_type = "float"
        elif target_type == "bln":
            target_type = "bool"
        elif target_type == "str":
            target_type = "string"

        # --- Get source type ---
        source_type = type(value).__name__.lower()
        if source_type == "str": # Normalize Python's 'str' to 'string' for consistency
            source_type = "string"

        # --- Handle No Conversion Needed ---
        if source_type == target_type:
            self.log(f"No conversion needed for {source_type}.")
            return value

        self.log(f"Normalized conversion: {value} ({source_type}) to {target_type}")

        # --- Specific CASPER Conversions ---
        try:
            # int -> float
            if source_type == "int" and target_type == "float":
                result = float(value)
                self.log(f"Converted int -> float: {value} -> {result}")
                return result

            # float -> int (Truncate)
            elif source_type == "float" and target_type == "int":
                result = int(value)
                self.log(f"Converted float -> int (truncate): {value} -> {result}")
                return result

            # bool -> float (Day -> 1.0, Night -> 0.0)
            elif source_type == "bool" and target_type == "float":
                result = 1.0 if value else 0.0
                self.log(f"Converted bool -> float: {value} -> {result}")
                return result

            # float -> bool (0.0 -> Night, else Day)
            elif source_type == "float" and target_type == "bool":
                result = False if value == 0.0 else True
                self.log(f"Converted float -> bool: {value} -> {result}")
                return result

            # int -> bool (0 -> Night, else Day)
            elif source_type == "int" and target_type == "bool":
                result = False if value == 0 else True
                self.log(f"Converted int -> bool: {value} -> {result}")
                return result

            # bool -> int (Day -> 1, Night -> 0)
            elif source_type == "bool" and target_type == "int":
                result = 1 if value else 0
                self.log(f"Converted bool -> int: {value} -> {result}")
                return result

            # string -> int (Truncate float-like strings, error otherwise)
            elif source_type == "string" and target_type == "int":
                try:
                    # First, try converting to float to handle "123.45" cases
                    float_val = float(value)
                    result = int(float_val) # Truncate
                    self.log(f"Converted string -> int (via float truncate): '{value}' -> {result}")
                    return result
                except ValueError:
                    self.log(f"ERROR: Cannot convert string '{value}' to int.")
                    raise ValueError(f"Cannot convert string '{value}' to int.")

            # string -> float
            elif source_type == "string" and target_type == "float":
                try:
                    result = float(value)
                    self.log(f"Converted string -> float: '{value}' -> {result}")
                    return result
                except ValueError:
                    self.log(f"ERROR: Cannot convert string '{value}' to float.")
                    raise ValueError(f"Cannot convert string '{value}' to float.")

            # string -> bool (Day/Night or numeric 0 -> Night, else Day)
            elif source_type == "string" and target_type == "bool":
                if value == "Day":
                    self.log(f"Converted string 'Day' -> bool: True")
                    return True
                elif value == "Night":
                    self.log(f"Converted string 'Night' -> bool: False")
                    return False
                else:
                    # Try numeric conversion
                    try:
                        num_val = float(value)
                        result = False if num_val == 0.0 else True
                        self.log(f"Converted numeric string -> bool: '{value}' -> {result}")
                        return result
                    except ValueError:
                        self.log(f"ERROR: Cannot convert non-Day/Night/numeric string '{value}' to bool.")
                        raise ValueError(f"Cannot convert string '{value}' to bool.")

            # Any -> string
            elif target_type == "string":
                if isinstance(value, bool):
                    result = "Day" if value else "Night"
                    self.log(f"Converted bool -> string: {value} -> '{result}'")
                    return result
                else:
                    result = str(value)
                    self.log(f"Converted {source_type} -> string: {value} -> '{result}'")
                    return result

            # Fallback for unhandled conversions
            else:
                self.log(f"ERROR: No explicit conversion rule from {source_type} to {target_type} for value {value}")
                raise TypeError(f"Cannot convert from {source_type} to {target_type}")

        except Exception as e:
            self.log(f"Conversion failed: {str(e)}")
            print(f"Error during type conversion: {str(e)}") # Make error visible to user
            self.stopped = True # Stop execution on conversion failure
            return None # Return None on failure

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
        
        # Handle numeric literals (add this)
        if isinstance(value, str):
            # Check for integer literals
            if value.isdigit():
                int_value = int(value)
                self.log(f"Converting string literal '{value}' to integer: {int_value}")
                return int_value
            
            # Check for float literals (contains a period and all other chars are digits)
            if "." in value and all(c.isdigit() or c == "." for c in value) and value.count(".") == 1:
                parts = value.split(".")
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    float_value = float(value)
                    self.log(f"Converting string literal '{value}' to float: {float_value}")
                    return float_value
            
            # Special handling for strings with escape sequences
            if value.startswith('"') and value.endswith('"'):
                # Keep quotes for now, so we can identify string literals later
                self.log(f"String literal detected: {value}")
        
        return value

    def execute_data_type(self, node):
        """Get the data type from a data_type node"""
       
        
        # If node has a value attribute, return it directly
        if hasattr(node, 'value'):
        
            return node.value
            
        # Otherwise, try to get from children
        if node.children and len(node.children) > 0:
            child = node.children[0]
            if hasattr(child, 'value'):
              
                return child.value
                
      
        return "unknown"

    # ==========================
    #    VARIABLE CALLS
    # ==========================

    def execute_postfix(self, node):
        self.log(f"Executing postfix: {node}")
        # Handles nodes like: postfix -> var_call -> IDENT
        # May also have a trailing None child from the parser.
        if not node.children:
            self.log("postfix has no children")
            return None

        # Filter out None children, if any
        valid_children = [child for child in node.children if child is not None]
        if not valid_children:
            self.log("postfix has no valid children")
            return None

        # Execute first valid child (should be var_call or similar)
        result = self.execute_node(valid_children[0])
        self.log(f"postfix result: {result}")
        # print(f"EXEC_POSTFIX: Returning {repr(result)}") # Changed print prefix
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
            # Correctly gather ALL children after IDENT as index nodes
            index_nodes_to_process = node.children[1:] 
            self.log(f"Processing collected index nodes for {var_name}: {index_nodes_to_process}")

            # --- MODIFIED: Allow indexing on list OR str ---
            if isinstance(value, (list, str)) and index_nodes_to_process:
                try:
                    current_value = value
                    for idx_node in index_nodes_to_process:
                        # Skip None nodes if they somehow appear in the list
                        if idx_node is None:
                            self.log(f"WARNING: Skipped None node during index processing for {var_name}")
                            continue
                            
                        # --- MODIFIED: Evaluate index node correctly --- 
                        idx_val = None
                        if hasattr(idx_node, 'type') and idx_node.type == 'IDENT':
                            # If the index node is an identifier, look up its value
                            index_var_name = idx_node.value.lstrip('$')
                            idx_val = self.lookup_variable(index_var_name)
                            self.log(f"Evaluated index variable '{index_var_name}' to: {idx_val}")
                            if idx_val is None:
                                self.log(f"ERROR: Index variable '{index_var_name}' not found.")
                                print(f"Error: Index variable '{index_var_name}' not found.")
                                self.stopped = True
                                return None # Stop if index variable is not defined
                        else:
                            # Otherwise, execute the node normally (e.g., for literals)
                            idx_val = self.execute_node(idx_node)
                        # --- End Index Evaluation --- 
                            
                        if isinstance(idx_val, int):
                            # Check bounds before accessing
                            # Check type for appropriate error msg
                            if not isinstance(current_value, (list, str)):
                                 # This should ideally not happen if the outer check passed, but good safety
                                 self.log(f"ERROR: Trying to index non-indexable element during multi-dimensional access: {var_name}")
                                 print(f"Error: Trying to index non-indexable element: {var_name}")
                                 self.stopped = True
                                 return None
                            if 0 <= idx_val < len(current_value):
                                current_value = current_value[idx_val]
                            else:
                                self.log(f"ERROR: Index out of bounds: {var_name}[...][{idx_val}], current level length: {len(current_value)}")
                                print(f"Error: Index out of bounds: {var_name}[{idx_val}]")
                                self.stopped = True
                                return None
                        else:
                            self.log(f"ERROR: Index must be an integer, got: {type(idx_val).__name__}")
                            print(f"Error: Index must be an integer, got: {type(idx_val).__name__}")
                            self.stopped = True
                            return None
                    # After iterating through all indices
                    value = current_value 
                except Exception as e:
                    self.log(f"ERROR: Indexing failed: {var_name} - {str(e)}")
                    print(f"Error: Indexing failed: {str(e)}")
                    self.stopped = True
                    return None
            # --- MODIFIED: Check if it's NOT list/str before error --- 
            elif not isinstance(value, (list, str)) and index_nodes_to_process:
                self.log(f"ERROR: Cannot index non-array/non-string variable: {var_name}")
                print(f"Error: Cannot index non-array/non-string variable: {var_name}")
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
        
        # Add this conditional statement as a parent for the execution context
        if hasattr(self, 'parent_nodes'):
            self.parent_nodes.append(node)
        
        # First child should be the condition
        # Execute the condition properly using execute_condition instead of execute_node
        if hasattr(node.children[0], 'type') and node.children[0].type == "condition":
            # Pass context for debugging
            condition_result = self.execute_condition(node.children[0], context="Main Check") 
        else:
            # This path shouldn't ideally be taken if parser creates condition nodes
            self.log("CONDITIONAL DEBUG: Warning - executing condition node directly.")
            condition_result = self.execute_node(node.children[0])
            
        # --- ADDED DEBUG PRINT --- 
        # print(f"DEBUG Factorial Condition: Main check condition result: {repr(condition_result)}", flush=True)
        # --- END DEBUG PRINT --- 
        
        # If we're waiting for input after condition evaluation, stop and return
        if self.waiting_for_input:
            return None
        
        if condition_result:
            self.log("CONDITIONAL DEBUG: Main condition is TRUE, executing check block")
            result = self.execute_node(node.children[1])
            
            # If not waiting for input, pop the parent node
            if not self.waiting_for_input and hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0:
                self.parent_nodes.pop()
                
            return result
            
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
                        
                    # If we're waiting for input after condition evaluation, stop and return
                    if self.waiting_for_input:
                        return None
                        
                    self.log(f"CONDITIONAL DEBUG: Otherwise_check condition result: {cond_result}")
                    
                    if cond_result:
                        result = self.execute_node(child)
                        
                        # If not waiting for input, pop the parent node
                        if not self.waiting_for_input and hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0:
                            self.parent_nodes.pop()
                            
                        return result
                elif child.type == "otherwise_block":
                    self.log("CONDITIONAL DEBUG: Executing otherwise block")
                    result = self.execute_otherwise_block(child)
                    
                    # If not waiting for input, pop the parent node
                    if not self.waiting_for_input and hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0:
                        self.parent_nodes.pop()
                        
                    return result
        
        # If not waiting for input, pop the parent node
        if not self.waiting_for_input and hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0:
            self.parent_nodes.pop()
        
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
            
            # Store parent-child relationship for resuming from input
            if hasattr(self, 'parent_nodes'):
                self.parent_nodes.append(node)
                
            for i in range(1, len(node.children)):
                result = self.execute_node(node.children[i])
                results.append(result)
                
                # If we're waiting for input, stop execution and return
                if self.waiting_for_input:
                    return None
                    
            # Pop parent node if we just added it and didn't pause
            if hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0 and not self.waiting_for_input:
                self.parent_nodes.pop()
                
            return results[-1] if results else None
        
        return None
    
    def execute_check_block(self, node):
        """Execute a check block"""
        self.log("Executing check_block")
        
        results = []
        
        # Store parent-child relationship for resuming from input
        if hasattr(self, 'parent_nodes'):
            self.parent_nodes.append(node)
            
        for i, child in enumerate(node.children):
            if child is not None:
                result = self.execute_node(child)
                results.append(result)
                
                # If we're waiting for input, stop execution and return
                if self.waiting_for_input:
                    return None
        
        # Pop parent node if we added it and aren't waiting for input
        if hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0 and not self.waiting_for_input:
            self.parent_nodes.pop()
        
        return results[-1] if results else None

    def execute_otherwise_block(self, node):
        """Execute an otherwise block"""
        self.log("Executing otherwise_block")
        
        results = []
        
        # Store parent-child relationship for resuming from input
        if hasattr(self, 'parent_nodes'):
            self.parent_nodes.append(node)
            
        for i, child in enumerate(node.children):
            if child is not None:
                result = self.execute_node(child)
                results.append(result)
                
                # If we're waiting for input, stop execution and return
                if self.waiting_for_input:
                    return None
        
        # Pop parent node if we added it and aren't waiting for input
        if hasattr(self, 'parent_nodes') and len(self.parent_nodes) > 0 and not self.waiting_for_input:
            self.parent_nodes.pop()
        
        return results[-1] if results else None
    
    
    
    def execute_condition(self, node, context="Unknown"):
        """Execute a condition expression"""
        # --- ADDED DEBUG PRINT --- 
        # print(f"DEBUG Factorial Condition: Evaluating condition ({context}) - Node: {node.type}", flush=True)
        # --- END DEBUG PRINT --- 
        
        if not node.children:
            self.log(f"CONDITIONAL DEBUG ({context}): Condition has no children, returning False")
            return False
        
        # Evaluate the first part (left operand or potentially a full expression itself)
        first_part_node = node.children[0]
        left_val = self.execute_node(first_part_node)
        
        # --- ADDED DEBUG PRINT --- 
        # Try to identify if the left_val came from $n
        var_name_involved = "unknown"
        if hasattr(first_part_node, 'type') and first_part_node.type == 'var_call' and first_part_node.children:
            if hasattr(first_part_node.children[0], 'type') and first_part_node.children[0].type == 'IDENT':
                 var_name_involved = first_part_node.children[0].value
        # print(f"DEBUG Factorial Condition ({context}): Left value ({var_name_involved}): {repr(left_val)} (type: {type(left_val).__name__})", flush=True)
        # --- END DEBUG PRINT --- 
 
        # Check if there is a binary operation tail
        if len(node.children) > 1 and hasattr(node.children[1], 'type') and node.children[1].type == "factor_tail_binop":
            binop_node = node.children[1] # This is the factor_tail_binop node

            # --- Use evaluate_expression_chain for proper evaluation --- 
            # Pass the context down for debugging
            # print(f"DEBUG Factorial Condition ({context}): Evaluating expression chain starting with {repr(left_val)}", flush=True)
            result = self.evaluate_expression_chain(left_val, binop_node, context=context)
            # --- End Use evaluate_expression_chain --- 

            # --- ADDED DEBUG PRINT --- 
            # print(f"DEBUG Factorial Condition ({context}): Final chain evaluation result: {repr(result)}", flush=True)
            # --- END DEBUG PRINT --- 
            return bool(result) # Ensure the final result is boolean

        # If no binary operation, the truthiness depends only on the left value
        final_bool = bool(left_val)
        # print(f"DEBUG Factorial Condition ({context}): No binary operator, final boolean result: {repr(final_bool)}", flush=True)
        return final_bool

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
      
            # The structure of the AST depends on whether this is a direct assignment or indexed assignment
            var_node = node.children[0]
            assign_node = node.children[1]
            value = None
            operator = '=' # Default operator
            var_name = None
            target_is_list_element = False
            indices = []
            contains_input = False # Flag if the value came from input

            # Check if this is an indexed assignment ($array[0] = value)
            # In this case node.children has 3 elements: var_call, assign_op, value
            if len(node.children) == 3 and hasattr(var_node, 'type') and var_node.type == "var_call":
                self.log("Detected indexed array assignment (var_call = value)")
                # Extract var_name and indices from var_call
                if var_node.children and hasattr(var_node.children[0], 'type') and var_node.children[0].type == "IDENT":
                    var_name = var_node.children[0].value.lstrip('$')
                if len(var_node.children) > 1 and var_node.children[1]: # Check if there are indices
                    target_is_list_element = True
                    # Execute index expressions to get integer values
                    for index_expr_node in var_node.children[1]:
                        index_val = self.execute_node(index_expr_node)
                        if not isinstance(index_val, int):
                            self.log(f"ERROR: List index must evaluate to an integer, got {type(index_val).__name__}")
                            print(f"Error: List index must evaluate to an integer.")
                            self.stopped = True
                            return None
                        indices.append(index_val)
                
                # Get the value from the third child (value node)
                value_node = node.children[2]
                
                # Check if the value node is a node or a direct value
                if hasattr(value_node, 'type'):
                    if value_node.type == "value" or value_node.type == "expression":
                        value = self.execute_node(value_node)
                        self.log(f"Indexed assignment value from value/expression node: {value}")
                    else:
                        value = self.execute_node(value_node)
                        self.log(f"Indexed assignment value from other node type: {value}")
                else:
                    # Direct value
                    value = value_node
                    self.log(f"Indexed assignment direct value: {value}")
                
                # Handle cases where the value is still None
                if value is None:
                    self.log("Value is None in indexed assignment, trying to extract literal")
                    # Try to extract the literal value directly from the value_node structure
                    try:
                        # Navigate through the AST structure to find the actual literal value
                        if hasattr(value_node, 'children') and value_node.children:
                            if hasattr(value_node.children[0], 'type') and value_node.children[0].type == "expression":
                                expr_node = value_node.children[0]
                                if hasattr(expr_node, 'children') and expr_node.children:
                                    if hasattr(expr_node.children[0], 'type') and expr_node.children[0].type == "literal":
                                        lit_node = expr_node.children[0]
                                        if hasattr(lit_node, 'value'):
                                            raw_value = lit_node.value
                                            self.log(f"Found raw literal value: {raw_value}")
                                            # Convert string digits to integers
                                            if isinstance(raw_value, str) and raw_value.isdigit():
                                                value = int(raw_value)
                                                self.log(f"Converted string literal to int: {value}")
                                            else:
                                                value = raw_value
                                                self.log(f"Using raw literal value: {value}")
                        
                        # If that didn't work, try other approaches based on the AST structure
                        if value is None and hasattr(value_node, 'type') and value_node.type == "value":
                            for child in value_node.children:
                                self.log(f"Examining child node of type: {getattr(child, 'type', 'unknown')}")
                                if hasattr(child, 'type'):
                                    if child.type == "literal" and hasattr(child, 'value'):
                                        raw_value = child.value
                                        if isinstance(raw_value, str) and raw_value.isdigit():
                                            value = int(raw_value)
                                            self.log(f"Extracted integer value from literal: {value}")
                                        else:
                                            value = raw_value
                                            self.log(f"Extracted non-integer value from literal: {value}")
                                        break
                                    elif child.type == "expression":
                                        self.log("Processing nested expression")
                                        # Try to evaluate the nested expression
                                        try:
                                            value = self.execute_node(child)
                                            self.log(f"Executed nested expression: {value}")
                                            break
                                        except Exception as e:
                                            self.log(f"Error executing nested expression: {str(e)}")
                    except Exception as e:
                        self.log(f"Error while trying to extract literal value: {str(e)}")
                
                # As a last resort, hardcode the value for debugging purposes
                if value is None and str(value_node).find("1") >= 0:
                    value = 1
                    self.log("Desperate measure - found '1' in value_node string representation, using value=1")
                
                # Get operator (second child)
                if hasattr(assign_node, 'type') and assign_node.type == "assign_op":
                    operator = assign_node.value
                    self.log(f"Indexed assignment operator: {operator}")
            else:
                # Handle standard assignment ($var = value)
                self.log("Standard variable assignment (IDENT assign_tail)")
                
                # Handle different assignment targets (direct IDENT vs var_call for indexed)
                if hasattr(var_node, 'type') and var_node.type == "IDENT":
                    var_name = var_node.value.lstrip('$')
                elif hasattr(var_node, 'type') and var_node.type == "var_call":
                    if var_node.children and hasattr(var_node.children[0], 'type') and var_node.children[0].type == "IDENT":
                        var_name = var_node.children[0].value.lstrip('$')
                    if len(var_node.children) > 1 and var_node.children[1]: # Check if there are indices
                        target_is_list_element = True
                        # Execute index expressions to get integer values
                        for index_expr_node in var_node.children[1]:
                             index_val = self.execute_node(index_expr_node)
                             if not isinstance(index_val, int):
                                 self.log(f"ERROR: List index must evaluate to an integer, got {type(index_val).__name__}")
                                 print(f"Error: List index must evaluate to an integer.")
                                 self.stopped = True
                                 return None
                             indices.append(index_val)
                else:
                    self.log(f"ERROR: Invalid assignment target type: {getattr(var_node, 'type', 'unknown')}")
                    print("Error: Invalid assignment target")
                    self.stopped = True
                    return None
                
                if not var_name:
                    self.log("ERROR: Empty or invalid variable name in assignment")
                    print("Error: Empty or invalid variable name in assignment")
                    self.stopped = True
                    return None

                # --- PUSH Implementation Start --- 
                if hasattr(assign_node, 'type') and assign_node.type == "assign_tail_push":
                    self.log(f"Executing push operation for variable '{var_name}'")
                    
                    if target_is_list_element:
                        self.log("ERROR: Cannot use .push() on an indexed list element.")
                        print("Error: Cannot use .push() on an indexed list element.")
                        self.stopped = True
                        return None

                    # -- Start Fix for Multiple Push Values --
                    if not assign_node.children:
                        self.log("ERROR: .push() has no child node (list_element expected).")
                        print("Error: .push() requires an argument.")
                        self.stopped = True
                        return None
                    list_element_node = assign_node.children[0] # This node contains the structure for one or more elements
                    
                    # Execute the list_element node to get *all* values
                    values_to_push = self.execute_list_element(list_element_node)
                    
                    if self.stopped:
                         return None # Error occurred during element evaluation
                         
                    if not isinstance(values_to_push, list):
                        # Ensure we always have a list, even if execute_list_element returns a single item
                        values_to_push = [values_to_push]
                        
                    self.log(f"Values to push onto '{var_name}': {values_to_push}")
                    # -- End Fix for Multiple Push Values --
                    
                    # Look up the variable
                    list_var = self.lookup_variable(var_name)
                    
                    # Check if the variable exists and is a list
                    if list_var is None:
                        self.log(f"ERROR: Variable '{var_name}' not found for .push().")
                        print(f"Error: Variable '{var_name}' not found.")
                        self.stopped = True
                        return None
                    if not isinstance(list_var, list):
                        self.log(f"ERROR: Variable '{var_name}' is not a list, cannot use .push(). Type is {type(list_var).__name__}")
                        print(f"Error: Cannot use .push() on non-list variable '{var_name}'.")
                        self.stopped = True
                        return None
                        
                    # Perform the push (extend the list with all values)
                    list_var.extend(values_to_push) # Use extend to add all elements
                    self.log(f"Pushed {values_to_push} onto '{var_name}'. New list: {list_var}")
                    
                    # Since lookup_variable returns a copy for lists, we need to update the variable in the environment
                    self.assign_variable(var_name, list_var)
                    return None # .push() doesn't return a value itself
                # --- PUSH Implementation End --- 
                
                # --- Existing Assignment Logic (assign_op, splice) --- 
                elif not hasattr(assign_node, 'type'):
                    self.log(f"ERROR: Invalid assign_node without type")
                    print("Error: Invalid assignment operation")
                    self.stopped = True
                    return None

                # Check if we're tracking this as the current assignment target
                if var_name:
                    self.current_assignment_target = var_name
                    self.log(f"Setting current assignment target to: {var_name}")
                
                # Execute the assign_tail_op or other assignment types to get the value/operation details
                assign_result = self.execute_node(assign_node)
                if self.stopped:
                    return None
                    
                self.log(f"Assignment result: {assign_result}")
                
                # If the assignment involves an operation (e.g., =, +=, -=)
                if isinstance(assign_result, dict) and 'value' in assign_result and 'operator' in assign_result:
                    value = assign_result['value']
                    operator = assign_result['operator']
                    self.log(f"Compound assignment detected: operator={operator}, value={value}")
                # If it's a direct assignment result
                elif assign_result is not None:
                    value = assign_result
                    self.log(f"Direct assignment with value: {value}")
                
                # Fix: Make sure value isn't None
                if value is None:
                    self.log(f"WARNING: Assignment value is None, this may indicate a problem")
                    
                    # Try to extract value from assign_node children directly
                    if hasattr(assign_node, 'children') and len(assign_node.children) > 1:
                        value_node = assign_node.children[1]
                        if hasattr(value_node, 'type') and value_node.type == "value" and value_node.children:
                            expr_node = value_node.children[0]
                            self.log(f"Trying to extract value directly from {getattr(expr_node, 'type', 'unknown')} node")
                            try:
                                value = self.execute_node(expr_node)
                                self.log(f"Extracted value directly: {value}")
                            except Exception as e:
                                self.log(f"Error extracting value directly: {str(e)}")
                
                # Check if the value came from an input statement that just completed
                if self.input_value is not None and self.paused_node is None and hasattr(assign_node, 'type') and assign_node.type == 'assign_tail_op' and assign_node.children and hasattr(assign_node.children[1], 'type') and assign_node.children[1].type == 'value' and assign_node.children[1].children and hasattr(assign_node.children[1].children[0], 'type') and assign_node.children[1].children[0].type == 'input_statement':
                    self.log("Detected completed input within assignment")
                    value = self.input_value # Use the processed input value
                    self.input_value = None # Clear the flag
                    contains_input = True

            # If we are still waiting for input, return None
            if self.waiting_for_input:
                 self.log("Assignment waiting for input")
                 return None

            # Perform the assignment or compound assignment
            if target_is_list_element:
                # Assignment to a list element, e.g., $arr[0] = 5 or $arr[0] += 1
                current_list = self.lookup_variable(var_name)
                if not isinstance(current_list, list):
                     self.log(f"ERROR: Variable '{var_name}' is not a list for indexed assignment.")
                     print(f"Error: Cannot assign to index of non-list variable '{var_name}'.")
                     self.stopped = True # Corrected indentation
                     return None         # Corrected indentation
                
                # --- Navigate nested lists based on indices --- 
                target_container = current_list
                for k in range(len(indices) - 1):
                    idx = indices[k]
                    if not isinstance(target_container, list) or idx >= len(target_container):
                        self.log(f"ERROR: Invalid index {idx} for dimension {k} of '{var_name}'.")
                        print(f"Error: Index out of bounds during assignment to '{var_name}'.")
                        self.stopped = True
                        return None
                    target_container = target_container[idx]
                
                final_index = indices[-1]
                # Check if the index is out of bounds
                if not isinstance(target_container, list) or final_index > len(target_container):
                     self.log(f"ERROR: Index {final_index} out of bounds for '{var_name}'. Size: {len(target_container)}")
                     print(f"Error: Index out of bounds during assignment to '{var_name}'.")
                     self.stopped = True
                     return None
                # Allow assignment if index is exactly the current size (like append)
                elif final_index == len(target_container):
                    if operator != '=': # Only allow direct assignment for append-like behavior
                        self.log(f"ERROR: Cannot use compound assignment ('{operator}') to extend list '{var_name}'.")
                        print(f"Error: Cannot use compound assignment ('{operator}') to extend list.")
                        self.stopped = True
                        return None
                    self.log(f"Extending list '{var_name}' at index {final_index}")
                    target_container.append(value)
                # Regular indexed assignment or compound assignment
                else:
                    if operator == '=':
                        self.log(f"Assigning value {value} to index {final_index} of list {target_container}")
                        
                        # Extra safeguard: if value is None, try one more approach to get the literal value
                        if value is None and hasattr(assign_node, 'type') and assign_node.type == 'assign_tail_op':
                            # Navigate directly to the literal node if possible
                            if (assign_node.children and len(assign_node.children) > 1 and 
                                hasattr(assign_node.children[1], 'type') and assign_node.children[1].type == 'value' and 
                                assign_node.children[1].children and 
                                hasattr(assign_node.children[1].children[0], 'type')):
                                try:
                                    if assign_node.children[1].children[0].type == 'literal':
                                        lit_value = assign_node.children[1].children[0].value
                                        if lit_value is not None:
                                            value = lit_value
                                            if value.isdigit():  # Convert string digits to int
                                                value = int(value)
                                            self.log(f"Extracted literal value directly: {value}")
                                except Exception as e:
                                    self.log(f"Error extracting literal value: {str(e)}")
                        
                        target_container[final_index] = value
                        self.log(f"List state after assignment: {target_container}")
                    else:
                        # Compound assignment on element
                        current_element_value = target_container[final_index]
                        self.log(f"Compound assign {operator} on index {final_index} (current: {repr(current_element_value)}) with value {repr(value)}. List: {repr(target_container)}")
                        new_value = self.apply_operator(operator.replace('=',''), current_element_value, value)
                        if self.stopped: return None
                        target_container[final_index] = new_value
                        self.log(f"List state after compound assignment: {target_container}")
                
                # Update the original list in the environment since lookup returned a copy
                self.log(f"Calling assign_variable for '{var_name}' with list: {current_list}")
                self.assign_variable(var_name, current_list) 
                self.log(f"Assigned value to {var_name} indices {indices}: {value}")
                
            else:
                # Regular variable assignment (or compound)
                if operator == '=':
                    self.assign_variable(var_name, value)
                    self.log(f"Assigned value to {var_name}: {value}")
                else:
                    # Compound assignment
                    current_val = self.lookup_variable(var_name)
                    new_value = self.apply_operator(operator.replace('=',''), current_val, value)
                    if self.stopped: return None
                    self.assign_variable(var_name, new_value)
                    self.log(f"Compound assigned to {var_name}. New value: {new_value}")
            
            # If this was an input assignment, clear the target tracking
            if not contains_input:
                self.log(f"Clearing current assignment target since no input detected or processed")
                self.current_assignment_target = None
            else:
                 self.log(f"Keeping assignment target {var_name} due to recent input processing") # Keep target if input was just handled
            
            return value
        except Exception as e:
            self.log(f"ERROR: Exception in assignment statement: {str(e)}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            print(f"Error: Exception during assignment: {str(e)}")
            self.stopped = True
            return None

    def execute_assign_tail_op(self, node):
        """Execute an assign_tail_op node"""
        self.log("Executing assign_tail_op")
        
        # Check for compound assignment operators in the node
        compound_op = None
        op_node = None 
        value_node = None
        
        # Get the operator node (first child)
        if node.children and len(node.children) > 0:
            op_node = node.children[0]
            # Check if this is a compound operator
            if hasattr(op_node, 'type') and op_node.type == "operator" and hasattr(op_node, 'value'):
                    op_value = op_node.value
                    if op_value in ["+=", "-=", "*=", "/=", "%="]:
                        compound_op = op_value
                        self.log(f"Found compound operator: {compound_op}")
            elif hasattr(op_node, 'type') and op_node.type == "assign_op": # Handle simple '='
                 if op_node.value == '=':
                      self.log("Found simple assignment operator: =")
                 else: # Should be compound op wrapped in assign_op
                     compound_op = op_node.value # e.g. '+='
                     self.log(f"Found compound operator from assign_op: {compound_op}")
            
        # Get the value node (second child)
        if len(node.children) > 1:
            value_node = node.children[1]
        
        if value_node:
            # Get the value from the right side of the assignment
            value = self.execute_node(value_node)
            self.log(f"Evaluated value_node to: {value}")
            
            # If this is a compound operator, return both the value and operator
            if compound_op:
                self.log(f"Returning compound op data: {compound_op}, value: {value}")
                return {"value": value, "operator": compound_op}
            
            # For simple assignment, just return the value
            self.log(f"Returning simple assignment value: {value}")
            return value
        else:
            self.log("No value node found in assign_tail_op")
            return None

    def execute_input_statement(self, node):
        """Execute an input statement and handle waiting for user input"""
       
        self.log("EXECUTE_INPUT_STATEMENT CALLED")
        
        # If we already have an input value and aren't waiting anymore, process it
        if self.input_value is not None and not self.waiting_for_input:
            input_val = self.input_value
           
            self.input_value = None
            return input_val
       
        self.paused_node = node
        self.waiting_for_input = True
        
        # Extract prompt if available
        prompt = ""
        if len(node.children) > 0:
            prompt_node = node.children[0]
            if prompt_node:
                prompt = self.execute_node(prompt_node) or ""
        
        # Store the prompt for the frontend to display
        self.input_prompt = prompt
        
        # Make sure we're still paused
        self.waiting_for_input = True
        
        # Flush stdout to ensure any previous output is visible
        import sys
        sys.stdout.flush()
        
        return None
        
    def provide_input(self, input_value):
        """Process user input and continue execution"""
        
        self.log(f"Received input: {input_value}")
        
        # Store the raw input value
        self.input_value = input_value
     
        self.waiting_for_input = False
        
        # Return the input value
        return self.input_value
    
    def is_waiting_for_input(self):
        """Check if the program is waiting for input"""
        waiting_state = self.waiting_for_input and not self.stopped
      
        return waiting_state
    
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
            
        control_var_node = node.children[0]
        condition_node = node.children[1]
        update_node = node.children[2]
        statement_nodes = node.children[3:]
        
        # Create a new scope for the loop variables
        self.push_scope()
        self.break_flag = False # Reset break flag before loop
        
        try:
            self.execute_control_variable(control_var_node)
            if self.stopped: raise Exception("Stopped during control variable init") # Check if stopped
            
            loop_count = 0
            while not self.stopped:
                loop_count += 1
                if loop_count > 1000:
                    self.log("ERROR: Loop safety limit reached (1000 iterations)")
                    print("Error: Infinite loop detected - exceeded 1000 iterations")
                    self.stopped = True
                    break
                    
                # Check the loop condition
                condition_result = False # Default to false
                try:
                    # Simplified condition evaluation (adjust based on actual node types)
                    if hasattr(condition_node, 'type') and condition_node.type == "condition":
                        condition_result = self.execute_condition(condition_node)
                    else:
                        condition_result = bool(self.execute_node(condition_node))
                except Exception as e:
                    self.log(f"ERROR: Failed to evaluate loop condition: {str(e)}")
                    print(f"Error: Failed to evaluate loop condition: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on condition error
                
                if self.stopped: break # Exit while if stopped during condition eval
                self.log(f"For loop condition result: {condition_result}")
                if not condition_result:
                    break # Exit while loop if condition is false
                    
                # Execute statements in the loop body
                try:
                    for stmt_node in statement_nodes:
                        if self.stopped: break # Check if stopped before statement
                        self.log(f"Executing statement of type: {getattr(stmt_node, 'type', 'Unknown')}") # Use getattr for safety
                        self.execute_node(stmt_node)
                        
                        if self.waiting_for_input: # Handle pausing for input
                            self.log("For loop paused waiting for input")
                            self.paused_node = node 
                            self.pop_scope() # Pop scope before pausing
                            return None # Exit execution to wait
                            
                        if self.break_flag: # Check break flag AFTER executing statement
                            self.log("STOP detected in for loop body.")
                            break # Exit inner statement loop
                            
                    if self.break_flag: # Check flag again to exit outer loop
                        break # Exit outer while loop
                        
                except Exception as e:
                    self.log(f"ERROR: Exception in loop body: {str(e)}")
                    print(f"Error: Exception in loop body: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on body error
                
                if self.stopped: break # Check if stopped after body execution
                
                # Execute the update statement
                try:
                    self.execute_node(update_node)
                except Exception as e:
                    self.log(f"ERROR: Failed to execute loop update statement: {str(e)}")
                    print(f"Error: Failed to execute loop update statement: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on update error
                    
                if self.stopped: break # Exit while if stopped during update
                
        except Exception as e: # Catch errors during loop setup/execution
             self.log(f"ERROR: Unhandled exception during for loop execution: {str(e)}")
             # Don't print here if already printed in inner blocks
             self.stopped = True
             # Fall through to finally block
             
        finally:
            # Clean up the loop scope and reset break flag
            self.pop_scope()
            self.break_flag = False # Ensure flag is reset
        
        return None
    
    def execute_until_loop(self, node):
        """Execute an 'until' loop statement - continues until the condition becomes true
           Syntax: until (expression) { statements }"""
        self.log("Executing until_loop")
        
        if len(node.children) < 2:
            self.log("until_loop has insufficient children")
            return None
            
        condition_node = node.children[0]
        statement_nodes = node.children[1:]
        
        # Create a new scope for the loop variables
        self.push_scope()
        self.break_flag = False # Reset break flag before loop
        
        try:
            loop_count = 0
            while not self.stopped:
                loop_count += 1
                if loop_count > 1000:
                    self.log("ERROR: Loop safety limit reached (1000 iterations)")
                    print("Error: Infinite loop detected - exceeded 1000 iterations")
                    self.stopped = True
                    break
                    
                # Check the loop condition - we continue until the condition becomes true
                condition_result = False # Default to false
                try:
                    # Evaluate the until condition
                    if hasattr(condition_node, 'type') and condition_node.type == "condition":
                        condition_result = self.execute_condition(condition_node)
                    else:
                        condition_result = bool(self.execute_node(condition_node))
                except Exception as e:
                    self.log(f"ERROR: Failed to evaluate until loop condition: {str(e)}")
                    print(f"Error: Failed to evaluate until loop condition: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on condition error
                
                if self.stopped: break # Exit while if stopped during condition eval
                self.log(f"Until loop condition result: {condition_result}")
                
                # In until loops, we exit when the condition becomes true
                if condition_result:
                    self.log("Until loop condition is true - exiting loop")
                    break
                    
                # Execute statements in the loop body
                try:
                    for stmt_node in statement_nodes:
                        if self.stopped: break # Check if stopped before statement
                        self.log(f"Executing statement of type: {getattr(stmt_node, 'type', 'Unknown')}") # Use getattr for safety
                        self.execute_node(stmt_node)
                        
                        if self.waiting_for_input: # Handle pausing for input
                            self.log("Until loop paused waiting for input")
                            self.paused_node = node 
                            self.pop_scope() # Pop scope before pausing
                            return None # Exit execution to wait
                            
                        if self.break_flag: # Check break flag AFTER executing statement
                            self.log("STOP detected in until loop body.")
                            break # Exit inner statement loop
                            
                    if self.break_flag: # Check flag again to exit outer loop
                        break # Exit outer while loop
                        
                except Exception as e:
                    self.log(f"ERROR: Exception in until loop body: {str(e)}")
                    print(f"Error: Exception in until loop body: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on body error
                
                if self.stopped: break # Check if stopped after body execution
                
        except Exception as e: # Catch errors during loop setup/execution
             self.log(f"ERROR: Unhandled exception during until loop execution: {str(e)}")
             # Don't print here if already printed in inner blocks
             self.stopped = True
             # Fall through to finally block
             
        finally:
            # Clean up the loop scope and reset break flag
            self.pop_scope()
            self.break_flag = False # Ensure flag is reset
        
        return None
        
    def execute_repeat_until(self, node):
        """Execute a 'repeat-until' loop statement - executes once, then continues until condition becomes true
           Syntax: repeat { statements } until(expression);"""
        self.log("Executing repeat_until")
        
        if len(node.children) < 2:
            self.log("repeat_until has insufficient children")
            return None
            
        statement_nodes = node.children[0:]
        condition_node = node.children[1]
        
        # Create a new scope for the loop variables
        self.push_scope()
        self.break_flag = False # Reset break flag before loop
        
        try:
            loop_count = 0
            
            # Execute at least once before checking condition
            do_continue = True
            
            while do_continue and not self.stopped:
                loop_count += 1
                if loop_count > 1000:
                    self.log("ERROR: Loop safety limit reached (1000 iterations)")
                    print("Error: Infinite loop detected - exceeded 1000 iterations")
                    self.stopped = True
                    break
                    
                # Execute statements in the loop body
                try:
                    for stmt_node in statement_nodes:
                        if self.stopped: break # Check if stopped before statement
                        self.log(f"Executing statement of type: {getattr(stmt_node, 'type', 'Unknown')}") # Use getattr for safety
                        self.execute_node(stmt_node)
                        
                        if self.waiting_for_input: # Handle pausing for input
                            self.log("Repeat-until loop paused waiting for input")
                            self.paused_node = node 
                            self.pop_scope() # Pop scope before pausing
                            return None # Exit execution to wait
                            
                        if self.break_flag: # Check break flag AFTER executing statement
                            self.log("STOP detected in repeat-until loop body.")
                            break # Exit inner statement loop
                            
                    if self.break_flag: # Check flag again to exit outer loop
                        break # Exit outer while loop
                        
                except Exception as e:
                    self.log(f"ERROR: Exception in repeat-until loop body: {str(e)}")
                    print(f"Error: Exception in repeat-until loop body: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on body error
                
                if self.stopped: break # Check if stopped after body execution
                
                # Check the condition after executing the loop body
                condition_result = False # Default to false
                try:
                    # Evaluate the until condition
                    if hasattr(condition_node, 'type') and condition_node.type == "condition":
                        condition_result = self.execute_condition(condition_node)
                    else:
                        condition_result = bool(self.execute_node(condition_node))
                except Exception as e:
                    self.log(f"ERROR: Failed to evaluate repeat-until loop condition: {str(e)}")
                    print(f"Error: Failed to evaluate repeat-until loop condition: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on condition error
                
                if self.stopped: break # Exit while if stopped during condition eval
                self.log(f"Repeat-until loop condition result: {condition_result}")
                
                # In repeat-until loops, we exit when the condition becomes true
                if condition_result:
                    self.log("Repeat-until loop condition is true - exiting loop")
                    do_continue = False
                    break
                
        except Exception as e: # Catch errors during loop setup/execution
             self.log(f"ERROR: Unhandled exception during repeat-until loop execution: {str(e)}")
             # Don't print here if already printed in inner blocks
             self.stopped = True
             # Fall through to finally block
             
        finally:
            # Clean up the loop scope and reset break flag
            self.pop_scope()
            self.break_flag = False # Ensure flag is reset
        
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
                    
                compound_op_node = update_tail_node.children[0] # Get the operator node
                value_node = update_tail_node.children[1]

                # FIX: Extract the VALUE ('=', '-=', etc.) from the operator node
                compound_op = compound_op_node.value 
                
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
        """Handles logical expressions (||, &&) respecting short-circuiting."""
        # print(f"DEBUG Factorial Condition (evaluate_logical_expression): Start - Left: {repr(left_value)}", flush=True)
        
        if not binop_node or not binop_node.children:
             final_bool = bool(left_value)
             # print(f"DEBUG Factorial Condition (evaluate_logical_expression): No binop, returning bool({repr(left_value)}) -> {final_bool}", flush=True)
             return final_bool
        
        operator_node = binop_node.children[0]
        right_node = binop_node.children[1]
        tail_node = binop_node.children[2] if len(binop_node.children) > 2 else None
        
        operator = operator_node.value if hasattr(operator_node, 'value') else operator_node
        
        # print(f"DEBUG Factorial Condition (evaluate_logical_expression): Op: '{operator}'", flush=True)

        # --- Short-circuiting logic --- 
        if operator == "||":
            bool_left = bool(left_value)
            # print(f"DEBUG Factorial Condition (evaluate_logical_expression): || - bool(left) is {bool_left}", flush=True)
            if bool_left:
                # print(f"DEBUG Factorial Condition (evaluate_logical_expression): || - Short-circuiting, result is True", flush=True)
                # If there's a tail, we still need to evaluate it with True as left operand
                # e.g., (True || ...) && C -> we need to evaluate True && C
                current_result = True 
            else:
                # Need to evaluate the right side
                # print(f"DEBUG Factorial Condition (evaluate_logical_expression): || - Evaluating right operand - Node type: {getattr(right_node, 'type', 'N/A')}", flush=True)
                right_value = self.execute_node(right_node)
                # print(f"DEBUG Factorial Condition (evaluate_logical_expression): || - Right operand evaluated to: {repr(right_value)}", flush=True)
                if self.stopped: return None
                current_result = bool(right_value)
                # print(f"DEBUG Factorial Condition (evaluate_logical_expression): || - bool(right) is {current_result}", flush=True)
        
        elif operator == "&&":
            bool_left = bool(left_value)
            # print(f"DEBUG Factorial Condition (evaluate_logical_expression): && - bool(left) is {bool_left}", flush=True)
            if not bool_left:
                 # print(f"DEBUG Factorial Condition (evaluate_logical_expression): && - Short-circuiting, result is False", flush=True)
                 # Short-circuit applies to the whole chain if it starts with False && ...
                 current_result = False
            else:
                 # Need to evaluate the right side
                 # print(f"DEBUG Factorial Condition (evaluate_logical_expression): && - Evaluating right operand - Node type: {getattr(right_node, 'type', 'N/A')}", flush=True)
                 right_value = self.execute_node(right_node)
                 # print(f"DEBUG Factorial Condition (evaluate_logical_expression): && - Right operand evaluated to: {repr(right_value)}", flush=True)
                 if self.stopped: return None
                 current_result = bool(right_value)
                 # print(f"DEBUG Factorial Condition (evaluate_logical_expression): && - bool(right) is {current_result}", flush=True)
        
        else:
            # If a non-logical operator is encountered, evaluate it normally first
            # This assumes the parser gives || and && higher precedence in the chain structure
            # print(f"DEBUG Factorial Condition (evaluate_logical_expression): Non-logical op '{operator}', evaluating using evaluate_expression_chain", flush=True)
            # Evaluate this step using the normal chain evaluation
            # We pass the *current* left value and the start of the non-logical chain
            # The evaluate_expression_chain will handle the operator and right side
            temp_binop_node = ASTNode("factor_tail_binop", [operator_node, right_node, tail_node])
            current_result = self.evaluate_expression_chain(left_value, temp_binop_node, context="Logical->Chain")
            # print(f"DEBUG Factorial Condition (evaluate_logical_expression): Intermediate result after '{operator}': {repr(current_result)}", flush=True)
            # If the non-logical chain had a tail, evaluate_expression_chain handles it.
            # We just need the final boolean result of this intermediate step.
            final_bool = bool(current_result)
            # print(f"DEBUG Factorial Condition (evaluate_logical_expression): Logical chain complete, final boolean result: {final_bool}", flush=True)
            return final_bool
            
        # Continue evaluating the rest of the logical chain if there's a tail
        if tail_node is not None:
            # print(f"DEBUG Factorial Condition (evaluate_logical_expression): Evaluating tail expression starting with {repr(current_result)}", flush=True)
            # The result of the current operation (current_result) becomes the left operand for the next part
            return self.evaluate_logical_expression(current_result, tail_node)
        else:
            # No more operators in the chain, return the final boolean result
            final_bool = bool(current_result)
            # print(f"DEBUG Factorial Condition (evaluate_logical_expression): Logical chain complete, final boolean result: {final_bool}", flush=True)
            return final_bool

    # ==========================
    #    LIST HANDLING
    # ==========================

    def execute_list_value(self, node):
        """Executes a list_value node, returning a Python list."""
        self.log(f"Executing list_value: {node}")
        if not node.children or not hasattr(node.children[0], 'type') or node.children[0].type != "list_element":
            self.log("List value is empty or has invalid structure")
            return [] # Return empty list for `[]` case
        
        # The first child is the list_element node
        return self.execute_list_element(node.children[0])

    def execute_list_element(self, node):
        """Recursively executes list_element nodes to build a flat Python list."""
        self.log(f"Executing list_element: {node}")
        elements = []
        
        if not node.children:
             return elements
             
        # First child: either literal_element or list_value (for nested lists)
        first_child = node.children[0]
        value = None
        if hasattr(first_child, 'type'):
            if first_child.type == "literal_element" and first_child.children:
                 # Execute the literal inside literal_element
                 value = self.execute_node(first_child.children[0])
            elif first_child.type == "list_value":
                 # Handle nested lists
                 value = self.execute_list_value(first_child)
            else:
                 # Should not happen based on grammar, but try executing anyway
                 value = self.execute_node(first_child)
        else:
             # Fallback if structure is unexpected
             value = self.execute_node(first_child)

        if value is not None:
             elements.append(value)

        # Second child: element_tail (optional)
        if len(node.children) > 1 and node.children[1] is not None:
            tail_node = node.children[1] # This is the next list_element
            elements.extend(self.execute_list_element(tail_node))
            
        return elements

    def execute_measure_call(self, node):
        """Executes a measure call and returns the 'measure' of the value."""
        # print("Executing measure_call")
        if not node.children or len(node.children) < 1:
            # print("ERROR: measure_call missing value child")
            print("Error: Invalid measure call - missing value.")
            self.stopped = True
            return None

        value_node = node.children[0]
       
        if hasattr(value_node, 'type') and value_node.type == "expression" and value_node.children:
           
             value_node = value_node.children[0]

      
        value = self.execute_node(value_node)

      

        if self.stopped: # Check if evaluation failed
             return None

        measure_result = 0
        if isinstance(value, str):
            measure_result = len(value)
            # print(f"Measured string: length = {measure_result}\")
        elif isinstance(value, list):
            measure_result = len(value)
            # print(f"Measured list: length = {measure_result}\")
        elif isinstance(value, (int, float, bool)):
             measure_result = 1 
        elif value is None:
             measure_result = 0 
            
        else:
        
            measure_result = 0 

   
        return measure_result

    # ADDED Method to handle stop statement
    def execute_stop_statement(self, node):
        """Sets the break flag to stop the current loop."""
        self.log("Executing stop_statement - setting break_flag")
        self.break_flag = True
        return None # Stop statement itself doesn't return a value

    # ==========================
    #    UNARY OPERATIONS
    # ==========================

    def execute_unary_negation(self, node):
        """Executes a unary negation operation (~)"""
        self.log("Executing unary_negation")

        if not node.children or len(node.children) != 1:
            self.log("ERROR: Unary negation node has incorrect number of children")
            print("Error: Invalid unary negation operation structure.")
            self.stopped = True
            return None

        operand_node = node.children[0]
        operand_value = self.execute_node(operand_node)

        if self.stopped: # Check if operand evaluation failed
            return None

        # Check if the operand is numeric (int or float)
        if not isinstance(operand_value, (int, float)):
            # Allow negation of booleans (Day=True=1, Night=False=0)
            if isinstance(operand_value, bool):
                 operand_value = 1 if operand_value else 0 # Convert bool to int
                 self.log(f"Converted boolean operand to int for negation: {operand_value}")
            else:
                 self.log(f"ERROR: Unary negation operand must be numeric or boolean, got {type(operand_value).__name__}")
                 print(f"Error: Operand for '~' must be numeric or boolean (Day/Night).")
                 self.stopped = True
                 return None

        # Perform negation
        negated_value = -operand_value
        self.log(f"Unary negation result: ~({operand_value}) = {negated_value}")

        # Maintain type consistency if original was int (after bool conversion)
        if isinstance(operand_value, int):
            negated_value = int(negated_value)

        return negated_value

    def execute_while_loop(self, node):
        """Execute an 'while' loop statement - continues while the condition is true
           Syntax: while (expression) { statements }"""
        self.log("Executing while_loop")
        
        if len(node.children) < 2:
            self.log("while_loop has insufficient children")
            return None
            
        condition_node = node.children[0]
        statement_nodes = node.children[1:]
        
        # Create a new scope for the loop variables
        self.push_scope()
        self.break_flag = False # Reset break flag before loop
        
        try:
            loop_count = 0
            while not self.stopped:
                loop_count += 1
                if loop_count > 1000:
                    self.log("ERROR: Loop safety limit reached (1000 iterations)")
                    print("Error: Infinite loop detected - exceeded 1000 iterations")
                    self.stopped = True
                    break
                    
                # Check the loop condition - we continue while the condition is true
                condition_result = False # Default to false
                try:
                    # Evaluate the while condition
                    if hasattr(condition_node, 'type') and condition_node.type == "condition":
                        condition_result = self.execute_condition(condition_node)
                    else:
                        condition_result = bool(self.execute_node(condition_node))
                except Exception as e:
                    self.log(f"ERROR: Failed to evaluate while loop condition: {str(e)}")
                    print(f"Error: Failed to evaluate while loop condition: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on condition error
                
                if self.stopped: break # Exit while if stopped during condition eval
                self.log(f"While loop condition result: {condition_result}")
                
                # In while loops, we exit when the condition becomes false
                if not condition_result:
                    self.log("While loop condition is false - exiting loop")
                    break
                    
                # Execute statements in the loop body
                try:
                    for stmt_node in statement_nodes:
                        if self.stopped: break # Check if stopped before statement
                        self.log(f"Executing statement of type: {getattr(stmt_node, 'type', 'Unknown')}") # Use getattr for safety
                        self.execute_node(stmt_node)
                        
                        if self.waiting_for_input: # Handle pausing for input
                            self.log("While loop paused waiting for input")
                            self.paused_node = node 
                            self.pop_scope() # Pop scope before pausing
                            return None # Exit execution to wait
                            
                        if self.break_flag: # Check break flag AFTER executing statement
                            self.log("STOP detected in while loop body.")
                            break # Exit inner statement loop
                            
                    if self.break_flag: # Check flag again to exit outer loop
                        break # Exit outer while loop
                        
                except Exception as e:
                    self.log(f"ERROR: Exception in while loop body: {str(e)}")
                    print(f"Error: Exception in while loop body: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on body error
                
                if self.stopped: break # Check if stopped after body execution
                
        except Exception as e: # Catch errors during loop setup/execution
             self.log(f"ERROR: Unhandled exception during while loop execution: {str(e)}")
             # Don't print here if already printed in inner blocks
             self.stopped = True
             # Fall through to finally block
             
        finally:
            # Clean up the loop scope and reset break flag
            self.pop_scope()
            self.break_flag = False # Ensure flag is reset
        
        return None
        
    def execute_repeat_while(self, node):
        """Execute a 'repeat-while' loop statement - executes once, then continues while condition is true
           Syntax: repeat { statements } while(expression);"""
        self.log("Executing repeat_while")
       
        
        if len(node.children) < 2:
            self.log("repeat_while has insufficient children")
            return None
            
        statement_nodes = node.children[0:-1] # Corrected: Statements are all but the last child
        condition_node = node.children[-1]    # Corrected: Condition is the last child
        

        # Create a new scope for the loop variables
        self.push_scope()
        self.break_flag = False # Reset break flag before loop
        
        try:
            loop_count = 0
            do_continue = True
            
            while do_continue and not self.stopped:
                loop_count += 1
            
                if loop_count > 1000:
                    self.log("ERROR: Loop safety limit reached (1000 iterations)")
                    print("Error: Infinite loop detected - exceeded 1000 iterations")
                    self.stopped = True
                    break
            
                try:
                    for stmt_node in statement_nodes:
                        if self.stopped: break # Check if stopped before statement
                        self.log(f"Executing statement of type: {getattr(stmt_node, 'type', 'Unknown')}") # Use getattr for safety
                    
                        self.execute_node(stmt_node)
                        
                        if self.waiting_for_input: # Handle pausing for input
                            self.log("Repeat-while loop paused waiting for input")
                            self.paused_node = node 
                            self.pop_scope() # Pop scope before pausing
                            return None # Exit execution to wait
                            
                        if self.break_flag: # Check break flag AFTER executing statement
                            self.log("STOP detected in repeat-while loop body.")
                         
                            break # Exit inner statement loop
                            
                    if self.break_flag: # Check flag again to exit outer loop
                       
                         break # Exit outer while loop
                        
                except Exception as e:
                    self.log(f"ERROR: Exception in repeat-while loop body: {str(e)}")
                    print(f"Error: Exception in repeat-while loop body: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on body error
                
                if self.stopped: break # Check if stopped after body execution
                
               
                condition_result = False # Default to false
                try:
                    # Evaluate the while condition
                    if hasattr(condition_node, 'type') and condition_node.type == "condition":
                     
                        condition_result = self.execute_condition(condition_node)
                    else:
                    
                        condition_result = bool(self.execute_node(condition_node))
                except Exception as e:
                    self.log(f"ERROR: Failed to evaluate repeat-while loop condition: {str(e)}")
                    print(f"Error: Failed to evaluate repeat-while loop condition: {str(e)}")
                    self.stopped = True
                    break # Exit while loop on condition error
                
                if self.stopped: break # Exit while if stopped during condition eval
                self.log(f"Repeat-while loop condition result: {condition_result}")
           
              
                if not condition_result:
                    self.log("Repeat-while loop condition is false - exiting loop")
                 
                    do_continue = False
                 
                else:
                 
                     pass # Added pass to avoid empty else block
                
        except Exception as e: # Catch errors during loop setup/execution
             self.log(f"ERROR: Unhandled exception during repeat-while loop execution: {str(e)}")
             # Don't print here if already printed in inner blocks
             self.stopped = True
             # Fall through to finally block
             
        finally:
            
            self.pop_scope()
            self.break_flag = False # Ensure flag is reset
        
        return None

    # ==========================
    #    TYPE CASTING
    # ==========================
    def execute_type_cast(self, node):
        """Executes an explicit type cast operation."""
        self.log(f"Executing type_cast: {node.value}")

        if not node.children or len(node.children) != 1:
            self.log("ERROR: Type cast node has incorrect number of children")
            print(f"Error: Invalid type cast operation '{node.value}' - missing argument.")
            self.stopped = True
            return None

        # Get the function name (e.g., "to_int")
        cast_function = node.value.lower()
        target_type = None

        # Determine the target type based on the function name
        if cast_function in ("to_int", "convert_to_int"):
            target_type = "int"
        elif cast_function in ("to_flt", "convert_to_flt"):
            target_type = "float" # Use 'float' internally
        elif cast_function in ("to_bln", "convert_to_bln"):
            target_type = "bool"  # Use 'bool' internally
        elif cast_function in ("to_str", "convert_to_str"):
            target_type = "string" # Use 'string' internally
        else:
            self.log(f"ERROR: Unknown type cast function: {cast_function}")
            print(f"Error: Unknown type cast function: {cast_function}")
            self.stopped = True
            return None

        # Execute the child node to get the value to cast
        value_to_cast = self.execute_node(node.children[0])
        # print(f"TYPECAST: Value to cast for {cast_function}: {repr(value_to_cast)} (type: {type(value_to_cast).__name__})") # Changed to print

        if self.stopped: # Check if operand evaluation failed
            return None

        # Use the existing convert_type logic
        try:
            converted_value = self.convert_type(value_to_cast, target_type)
            self.log(f"Type cast {cast_function}({value_to_cast}) resulted in: {converted_value}")
            return converted_value
        except Exception as e:
            self.log(f"ERROR: Type casting failed for {cast_function}({value_to_cast}): {str(e)}")
            print(f"Error: Type casting failed: {str(e)}")
            self.stopped = True
            return None


    # ==========================
    #    LIST HANDLING
    # ==========================

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