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

    def log(self, message):
        if self.debug:
            pass  # Remove debug print statement

    def get_current_env(self):
        return self.env_stack[-1]

    def push_scope(self):
        self.env_stack.append({})

    def pop_scope(self):
        if len(self.env_stack) > 1:
            self.env_stack.pop()
        else:
            print("Warning: Attempted to pop global environment.")

    def lookup_variable(self, var_name):
        self.log(f"Looking up variable: '{var_name}'")
        
        # Search through the environment stack, starting with the most local scope
        for env in reversed(self.env_stack):
            if var_name in env:
                self.log(f"Found '{var_name}' with value: {env[var_name]}")
                return env[var_name]
        
        self.log(f"Variable '{var_name}' not found in any environment")
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
            self.log("Program execution stopped, cannot generate code")
            return None
            
        if ast is not None:
       
            self.ast = ast
            
        if ast is None and not self.waiting_for_input:       
            self.log("Resuming execution after input")
            return
            
        result = self.execute_node(ast)
        # Mark program as completed when done executing
        if not self.waiting_for_input:
            self.completed = True
        return result

    def execute_node(self, node):
        # Check if execution is stopped
        if self.stopped:
            self.log("Execution is stopped, skipping node execution")
            return None
            
        if node is None and self.paused_node and not self.waiting_for_input:
            self.log("Resuming execution with paused node after input")
            temp_node = self.paused_node
            self.paused_node = None
            return self.execute_node(temp_node)

        if self.waiting_for_input:
            self.log("Waiting for input, pausing execution")
            return None
            
        if node is None:
            self.log("execute_node received None")
            return None

        # Handle Day/Night literals at the node level
        if hasattr(node, 'value') and node.value == "Day":
            self.log(f"Found Day literal in node of type {node.type}")
            return True
        if hasattr(node, 'value') and node.value == "Night":
            self.log(f"Found Night literal in node of type {node.type}")
            return False

        if isinstance(node, list):
            self.log(f"execute_node processing list of length {len(node)}")
            results = []
            for subnode in self.flatten_nodes(node):
                res = self.execute_node(subnode)
                if res is not None:
                    results.append(res)
            return results if results else None

        if not hasattr(node, 'type'):
            self.log(f"Node has no type attribute: {node}")
            return None

        self.log(f"execute_node processing node of type: {node.type}")
        
        if node.type == "input_statement" and self.input_value is not None and not self.waiting_for_input:
            input_val = self.input_value
            self.log(f"Returning input value from input statement: {input_val}")
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
    
        self.push_scope()
        results = []
    
        if node.children:
            for child in node.children:
                result = self.execute_node(child)
                results.append(result)
        else:
            print("Warning: main_function node has no statements.")
        self.pop_scope()
        return results[-1] if results else None

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
            print("Error: Function declaration missing name")
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
        
      
        func_name = None
        for child in node.children:
            if hasattr(child, 'type') and child.type == "FUNCTION_NAME":
                func_name = child.value
                break
                
        if not func_name:
            print("Error: Function call missing name")
            return None
            
        self.log(f"Calling function: {func_name}")
        
   
        if func_name not in self.functions:
            print(f"Error: Undefined function '{func_name}'")
            return None
            
    
        args = []
        for child in node.children:
            if hasattr(child, 'type') and child.type == "arguments":
                for arg in child.children:
                    arg_value = self.execute_node(arg)
                    args.append(arg_value)
                    self.log(f"Argument value: {arg_value}")
   
        self.push_scope()
        
  
        for i, param in enumerate(self.functions[func_name]['params']):
            if i < len(args):
                param_name = param["name"]
                self.get_current_env()[param_name] = args[i]
                self.log(f"Bound parameter '{param_name}' to value {args[i]}")
 
        func_node = self.functions[func_name]['node']
        for child in func_node.children:
            if hasattr(child, 'type') and child.type == "statements":
                for statement in child.children:
                    self.execute_node(statement)
            else:
                self.execute_node(child)

        return_value = None
        if self.return_values:
            return_value = self.return_values.pop()
            self.log(f"Function returned: {return_value}")

        self.pop_scope()
        
        return return_value
        
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
        self.log("Executing var_statement")
        self.log(f"var_statement children: {node.children}")
        
        valid_children = [child for child in node.children if child is not None]
        self.log(f"Valid children after filtering None: {valid_children}")
        
        # Fix: Allow variable declaration without initialization
        if len(valid_children) < 1:  
            print("Error: Not enough valid children in var_statement.")
            return None

        var_name = None
        data_type = None
        for child in valid_children:
            if hasattr(child, 'type'):
                if child.type == "IDENT":
                    var_name = child.value.lstrip('$')
                elif child.type == "data_type":
                    data_type = child.value
        
        # Look for the data_type in the first child if not found
        if data_type is None and len(valid_children) > 0 and hasattr(valid_children[0], 'value'):
            # Sometimes the data_type is directly in the first child
            if valid_children[0].value in ["int", "flt", "bln", "str", "chr"]:
                data_type = valid_children[0].value
        
        if not var_name:
            print("Error: Could not find variable name in var_statement.")
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
        for child in valid_children:
            if hasattr(child, 'type') and (child.type == "local_var_assign" or child.type == "expression" or child.type == "function_call" or child.type == "input_statement"):
                assign_node = child
                break
        
        # If there's an assignment, use its value; otherwise use default
        if assign_node:
            value = self.execute_node(assign_node)
            
            # Special handling for input_statement results
            if assign_node.type == "input_statement" and value is None and self.input_value is not None:
                value = self.input_value
                self.input_value = None  # Clear to prevent reuse
            
            self.log(f"Evaluated expression value: {value}")
            
            # Apply type conversion based on declaration
            # Boolean to Integer conversion
            if data_type == "int" and isinstance(value, bool):
                value = 1 if value else 0
            # Boolean to Float conversion
            elif (data_type == "float" or data_type == "flt") and isinstance(value, bool):
                value = 1.0 if value else 0.0
            # Apply other conversions using the standard method
            elif data_type and value is not None:
                python_type = self.casper_to_python_type(data_type)
                if python_type:
                    original_value = value
                    value = self.convert_type(value, python_type)
                    self.log(f"Applied implicit conversion from {type(original_value).__name__} to {data_type}: {original_value} -> {value}")
        else:
            value = default_value
            self.log(f"No assignment found, using default value: {value}")
        
        # Assign the variable
        self.get_current_env()[var_name] = value
        self.log(f"Assigned variable '{var_name}' = {value}")
        self.log(f"Environment after assignment: {self.get_current_env()}")
        
        return value
        
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
        self.log(f"Executing local_var_assign: {node}")

        if not node.children:
            self.log("local_var_assign has no children")
            return None
        
       
        value_node = node.children[0]
        self.log(f"local_var_assign value node: {value_node}")
        result = self.execute_node(value_node)
        self.log(f"local_var_assign result: {result}")
        return result

    def execute_output_statement(self, node):
        self.log("Executing output_statement")
        
        if not node.children:
            print("Warning: output_statement has no children.")
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
        if len(node.children) < 1:
            print("Warning: display_statement has no children.")
            return None
        
        child = node.children[0]
        
        # Special handling for variable display
        if hasattr(child, 'type'):
            # Check for var_call nodes (variables)
            if child.type == "var_call" and child.children and hasattr(child.children[0], 'value'):
                var_name = child.children[0].value.lstrip('$')
                value = self.lookup_variable(var_name)
                self.log(f"Display variable: {var_name} = {value}")
                
                # Ensure we never display numeric values as Day/Night
                if value is not None:
                    if isinstance(value, bool) and not (isinstance(value, int) and not isinstance(value, bool)):
                        # Only format as Day/Night if it's SPECIFICALLY a boolean (not an int)
                        formatted_value = "Day" if value else "Night"
                        print(formatted_value, end="")
                    else:
                        # Never format integers or other types as Day/Night
                        print(value, end="")
                return value
        
        # Process other types of display children
        result = self.execute_node(child)
        self.log(f"Display result: {result}")
        
        # Ensure we never display numeric values as Day/Night
        # Handle string literals
        if isinstance(result, str) and result.startswith('"') and result.endswith('"'):
            # Remove quotes for display
            result = result[1:-1].replace('\\n', '\n').replace('\\t', '\t')
        # Format boolean values as Day/Night ONLY IF they are specifically boolean, not int
        elif isinstance(result, bool) and not (isinstance(result, int) and not isinstance(result, bool)):
            result = "Day" if result else "Night"
        
        # Display the result without adding a newline
        if result is not None:
            print(f"{result}", end="")
        
        return result

    # ==========================
    #    EXPRESSIONS
    # ==========================

    def execute_value(self, node):
        self.log(f"Executing value: {node}")
        
        # Special handling for direct Day/Night values
        if hasattr(node, 'value'):
            if node.value == "Day":
                return True
            elif node.value == "Night": 
                return False
                
        if node.children:
            result = self.execute_node(node.children[0])
            self.log(f"Value result: {result}")
            return result
        self.log("Value has no children")
        return None

    def execute_expression(self, node):
        self.log(f"Executing expression: {node}")
        
        if not node.children:
            self.log("Expression has no children")
            return None
        
   
        if len(node.children) == 1:
            return self.execute_node(node.children[0])

        result = self.execute_node(node.children[0])
        self.log(f"Initial term: {result}")
   
        operations = []
        
  
        i = 1
        while i < len(node.children):
            if hasattr(node.children[i], 'type') and node.children[i].type == "factor_tail_binop":
                self.log(f"Processing factor_tail_binop at index {i}")
                binop_node = node.children[i]
             
                result = self.evaluate_expression_chain(result, binop_node)
                self.log(f"Expression result after chain evaluation: {result}")
                break
            i += 1
            
        self.log(f"Final expression result: {result}")
        return result
        
    def evaluate_expression_chain(self, left_value, binop_node):
        self.log(f"Evaluating expression chain starting with {left_value}")
        
        if not binop_node or not hasattr(binop_node, 'type') or binop_node.type != "factor_tail_binop":
            return left_value
            
        
        if len(binop_node.children) < 2:
            self.log("Invalid binop node structure")
            return left_value
            
        op_node = binop_node.children[0]
        if not hasattr(op_node, 'type') or op_node.type != "operator":
            self.log("Expected operator node")
            return left_value
            
        operator = op_node.value
        self.log(f"Operator: {operator}")
        
    
        right_value = self.execute_node(binop_node.children[1])
        self.log(f"Right operand: {right_value}")
        
       
        next_binop = None
        if len(binop_node.children) > 2 and binop_node.children[2] is not None:
            next_binop = binop_node.children[2]
            
        if next_binop is not None and hasattr(next_binop, 'type') and next_binop.type == "factor_tail_binop":
            next_op_node = next_binop.children[0]
            if hasattr(next_op_node, 'type') and next_op_node.type == "operator":
                next_operator = next_op_node.value
                
             
                if self.has_higher_precedence(next_operator, operator):
                    self.log(f"Evaluating higher precedence operation first: {next_operator}")
              
                    right_value = self.evaluate_expression_chain(right_value, next_binop)
                    self.log(f"Result of higher precedence chain: {right_value}")
             
                    result = self.apply_operator(operator, left_value, right_value)
                    self.log(f"Result of current operation: {result}")
                    return result

        result = self.apply_operator(operator, left_value, right_value)
        self.log(f"Operation result: {left_value} {operator} {right_value} = {result}")
        
        if next_binop is not None and hasattr(next_binop, 'type') and next_binop.type == "factor_tail_binop":
            result = self.evaluate_expression_chain(result, next_binop)
            
        return result
    
    def has_higher_precedence(self, op1, op2):
        precedence = {
            '*': 2, '/': 2, '%': 2,  #
            '+': 1, '-': 1            
        }
        return precedence.get(op1, 0) > precedence.get(op2, 0)

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
        
        if operator == "+":
            return left + right
        elif operator == "-":
            return left - right
        elif operator == "*":
            return left * right
        elif operator == "/":
            if right == 0:
                print("Error: Division by zero")
                return 0
            return left / right
        elif operator == "%":
            if right == 0:
                print("Error: Modulo by zero")
                return 0
            return left % right
        # Add comparison operators as fallback
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
            print(f"Unsupported operator: {operator}")
            return None

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
                    right = 1 if right else 0
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
        self.log(f"Executing var_call: {node}")
        # var_call -> IDENT (value=$hello)
        if not node.children:
            self.log("var_call has no children")
            return None
            
        var_name = node.children[0].value
        # Remove $ prefix if present for variable lookups
        clean_var_name = var_name.lstrip('$')
        self.log(f"var_call looking up: '{clean_var_name}'")
        
        result = self.lookup_variable(clean_var_name)
        self.log(f"var_call result: {result}")
        return result

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
        self.log(f"Executing statements block: {node}")
        results = []
        if node.children:
            for child in node.children:
                result = self.execute_node(child)
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
        
        condition_result = self.execute_node(node.children[0])
        self.log(f"CONDITIONAL DEBUG: Condition result: {condition_result}")
        
        if condition_result:
            self.log("CONDITIONAL DEBUG: Main condition is TRUE, executing check block")
            return self.execute_node(node.children[1])
        for i in range(2, len(node.children)):
            child = node.children[i]
            if child is None:
                continue
                
            if hasattr(child, 'type'):
                if child.type == "otherwise_check":
                    
                    cond_result = self.execute_condition(child.children[0])
                    if cond_result:
                        results = []
                        for j in range(1, len(child.children)):
                            result = self.execute_node(child.children[j])
                            results.append(result)
                        return results[-1] if results else None
                elif child.type == "otherwise_block":
            
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
            
        condition_result = self.execute_condition(node.children[0])
        
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
                

            elif operator == "==":
                return left_val == right_val
            elif operator == "!=":
                return left_val != right_val
            elif operator == ">":
                return left_val > right_val
            elif operator == "<":
                return left_val < right_val
            elif operator == ">=":
                return left_val >= right_val
            elif operator == "<=":
                return left_val <= right_val

        return bool(left_val)

    def evaluate_condition_chain(self, left_value, binop_node):
        """Helper function to evaluate condition chains with operators"""
        self.log(f"Evaluating condition chain starting with {left_value}")
        
        if not binop_node or not hasattr(binop_node, 'type') or binop_node.type != "factor_tail_binop":
            return left_value
            
        op_node = binop_node.children[0]
        if not hasattr(op_node, 'type') or op_node.type != "operator":
            self.log("Expected operator node")
            return left_value
            
        operator = op_node.value
        self.log(f"Condition operator: {operator}")
        
        right_value = self.execute_node(binop_node.children[1])
        self.log(f"Condition right operand: {right_value}")
        
        next_binop = None
        if len(binop_node.children) > 2 and binop_node.children[2] is not None:
            next_binop = binop_node.children[2]
            
        if operator in ["==", "!=", ">", "<", ">=", "<="]:
            temp_result = self.apply_comparison(operator, left_value, right_value)
        else:
            temp_result = self.apply_operator(operator, left_value, right_value)
        
        self.log(f"Intermediate result: {left_value} {operator} {right_value} = {temp_result}")

        if next_binop is not None and hasattr(next_binop, 'type') and next_binop.type == "factor_tail_binop":
            return self.evaluate_condition_chain(temp_result, next_binop)
        
        return temp_result

    def apply_comparison(self, operator, left, right):
        """Apply comparison operators"""
        self.log(f"Applying comparison: {left} {operator} {right}")
        if operator == "==":
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
            return self.apply_operator(operator, left, right)
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

    
    def execute_assignment_statement(self, node):
        """Execute an assignment statement"""
        self.log("Executing assignment_statement")
        
        if len(node.children) < 2:
            self.log("Assignment statement missing parts")
            return None
  
        var_node = node.children[0]
        if not hasattr(var_node, 'type') or var_node.type != "IDENT":
            self.log(f"Expected IDENT, got {var_node.type if hasattr(var_node, 'type') else 'unknown'}")
            return None
        
        var_name = var_node.value.lstrip('$')

        assign_node = node.children[1]
        if not hasattr(assign_node, 'type') or assign_node.type != "assign_tail_op":
            self.log(f"Expected assign_tail_op, got {assign_node.type if hasattr(assign_node, 'type') else 'unknown'}")
            return None

        value_node = None
        for child in assign_node.children:
            if child is not None and hasattr(child, 'type') and child.type == "value":
                value_node = child
                break
        
        if not value_node:
            self.log("No value node found in assign_tail_op")
            return None

        value = self.execute_node(value_node)
        self.log(f"Assignment value for {var_name}: {value}")
        
        # Apply implicit type conversion based on the existing variable's type
        # Look up the existing variable to get its current type
        existing_value = self.lookup_variable(var_name)
        if existing_value is not None:
            # Only convert if the types differ
            if type(existing_value) != type(value) and value is not None:
                original_value = value
                target_type = type(existing_value).__name__.lower()
                value = self.convert_type(value, target_type)
                self.log(f"Applied implicit conversion for assignment: {type(original_value).__name__} -> {target_type}: {original_value} -> {value}")

        self.assign_variable(var_name, value)
        
        return value

    def execute_assign_tail_op(self, node):
        """Execute an assign_tail_op node"""
        self.log("Executing assign_tail_op")
        
        value_node = None
        for child in node.children:
            if child is not None and hasattr(child, 'type') and child.type == "value":
                value_node = child
                break
        
        if value_node:
            return self.execute_node(value_node)
        else:
            self.log("No value node found in assign_tail_op")
            return None

    def execute_input_statement(self, node):
        self.log("Executing input_statement")
        
        # If input value is already available, return it immediately without showing prompt again
        if self.input_value is not None and not self.waiting_for_input:
            input_val = self.input_value
            self.log(f"Using provided input value: {input_val}")
            
            # Clear input value to prevent reuse
            self.input_value = None
            self.paused_node = None
            
            # Return the value with appropriate type conversion
            if isinstance(input_val, str) and input_val.isdigit():
                return int(input_val)
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
                    # Print the prompt without newline to match typical input behavior
                    print(prompt, end="")
        
        # Set prompt in object state
        self.input_prompt = prompt
        self.log("Waiting for input...")
        
        # This will pause execution until input is provided
        return None
    
    def provide_input(self, input_value):
        """Process user input and continue execution"""
        self.log(f"Received input: {input_value}")
        
        # Try to convert to integer if it looks like one
        try:
            converted_value = int(input_value)
            self.log(f"Converted input to integer: {converted_value}")
            self.input_value = converted_value
        except ValueError:
            self.log(f"Keeping input as string: {input_value}")
            self.input_value = input_value
        
        # Mark that we're no longer waiting for input
        self.waiting_for_input = False
        
        # If we have a paused node, do not reprocess it here (we'll do it in execute_node)
        # Just return the input value
        self.log(f"Input processed: {self.input_value}")
        return self.input_value
    
    def is_waiting_for_input(self):
        """Check if the program is waiting for input"""
        self.log(f"is_waiting_for_input called, returning: {self.waiting_for_input}")
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
        self.execute_control_variable(control_var_node)
        
        loop_count = 0
        # Loop execution
        while True:
            # Safety limit to prevent infinite loops during debugging
            loop_count += 1
            if loop_count > 1000:  # Reasonable limit for most loops
                self.log("Loop safety limit reached (1000 iterations)")
                break
                
            # Check the loop condition - ensuring we handle it as a condition, not a regular expression
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
                        condition_result = self.apply_comparison(operator, left_val, right_val)
                    else:
                        condition_result = self.apply_operator(operator, left_val, right_val)
                else:
                    condition_result = bool(left_val)
            else:
                # Otherwise just try to execute and convert to boolean
                condition_result = bool(self.execute_node(condition_node))
                
            self.log(f"For loop condition result: {condition_result}")
            
            if not condition_result:
                break
                
            # Execute each statement in the loop body
            for stmt_node in statement_nodes:
                self.log(f"Executing statement of type: {stmt_node.type}")
                self.execute_node(stmt_node)
                
                # Check if waiting for input, and if so, pause execution
                if self.waiting_for_input:
                    self.log("For loop paused waiting for input")
                    # Save state so we can resume later
                    self.paused_node = node
                    # Exit the loop without popping scope
                    return None
            
            # Execute the update statement
            self.execute_node(update_node)
        
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
        print("Program execution stopped")

def run_code_generation(ast):
    """Create a CodeGenerator and run code generation on the given AST."""
    generator = CodeGenerator()
    generator.debug = True
    
    # Create global scope
    generator.global_vars = {}
    generator.env_stack = [generator.global_vars]
    
    generator.generate(ast)
    
    return generator