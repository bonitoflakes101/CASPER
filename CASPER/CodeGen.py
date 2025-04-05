from Parser import ASTNode

class CodeGenerator:
    def __init__(self):
        # Global variables dictionary
        self.global_vars = {}
        # Environment stack, where the first element is the global scope
        self.env_stack = [self.global_vars]
        # Function definitions dictionary
        self.functions = {}
        # Return value stack for functions
        self.return_values = []
        # Set debug mode
        self.debug = False # Set to True by default to enable debugging

    def log(self, message):
        if self.debug:
            print(f"DEBUG: {message}")

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
        self.log(f"Current environment stack: {self.env_stack}")
      
        for env in reversed(self.env_stack):
            self.log(f"Checking env: {env}")
            if var_name in env:
                self.log(f"Found '{var_name}' with value: {env[var_name]}")
                return env[var_name]
        self.log(f"Variable '{var_name}' not found in any environment")
        return None

    def assign_variable(self, var_name, value):
        self.log(f"Assigning '{var_name}' = {value}")
       
        for env in reversed(self.env_stack):
            if var_name in env:
                env[var_name] = value
                return
 
        self.get_current_env()[var_name] = value

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
        self.execute_node(ast)

    def execute_node(self, node):
        
        if node is None:
            self.log("execute_node received None")
            return None
                
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
        
        # Enhanced debug for conditional structures
        if node.type in ["conditional_statement", "condition", "otherwise_check", "otherwise"]:
            self.log(f"DEBUG: Found conditional structure node of type: {node.type}")
            self.log(f"DEBUG: Node details - ID: {id(node)}, Children count: {len(node.children) if node.children else 0}")
            self.print_node_structure(node)
        
        if node.children:
            node.children = self.flatten_nodes(node.children)

        # Add explicit handling for all conditional types with extra logging
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
        
        # Existing method dispatch
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
        
        if not var_name:
            print("Error: Could not find variable name in var_statement.")
            return None
        
        # Initialize with default value based on data type
        default_value = None
        if data_type == "int":
            default_value = 0
        elif data_type == "string":
            default_value = ""
        elif data_type == "float":
            default_value = 0.0
        elif data_type == "bool":
            default_value = False
        
        # Find assignment if it exists
        assign_node = None
        for child in valid_children:
            if hasattr(child, 'type') and (child.type == "local_var_assign" or child.type == "expression" or child.type == "function_call"):
                assign_node = child
                break
        
        # If there's an assignment, use its value; otherwise use default
        if assign_node:
            value = self.execute_node(assign_node)
            self.log(f"Evaluated expression value: {value}")
        else:
            value = default_value
            self.log(f"No assignment found, using default value: {value}")
        
        # Assign the variable
        self.get_current_env()[var_name] = value
        self.log(f"Assigned variable '{var_name}' = {value}")
        self.log(f"Environment after assignment: {self.get_current_env()}")
        
        return value
        
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
        # output_statement -> child: value
        if len(node.children) < 1:
            print("Warning: output_statement has no children.")
            return None
        
        result = self.execute_node(node.children[0])
        self.log(f"Output result: {result}")
        print(result)  
        return result
        
    def execute_display_statement(self, node):
        self.log("Executing display_statement")
        if len(node.children) < 1:
            print("Warning: display_statement has no children.")
            return None
        
        result = self.execute_node(node.children[0])
        self.log(f"Display result: {result}")
        print(result)  
        return result

    # ==========================
    #    EXPRESSIONS
    # ==========================

    def execute_value(self, node):
        self.log(f"Executing value: {node}")
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
        else:
            print(f"Unsupported operator: {operator}")
            return None

    def execute_literal(self, node):
        self.log(f"Executing literal: {node}, value={node.value}")
        # literal (value=3)
        return node.value

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
        """Execute a check statement (if statement)"""
        self.log("CONDITIONAL DEBUG: Starting execute_conditional_statement")
        self.log(f"Node children count: {len(node.children) if node.children else 0}")
        
        if node.children:
            for i, child in enumerate(node.children):
                if child is None:
                    self.log(f"Child {i}: None")
                    continue
                if hasattr(child, 'type'):
                    self.log(f"Child {i}: Type={child.type}")
                else:
                    self.log(f"Child {i}: No type attribute")
        

        condition_node = None
        statements_node = None
        
        for child in node.children:
            if child is None:
                continue
            if hasattr(child, 'type'):
                if child.type == "condition":
                    condition_node = child
                    self.log(f"CONDITIONAL DEBUG: Found condition node: {child.type}")
                elif child.type == "statements" or not statements_node:
                    if child.type != "condition" and child.type != "otherwise_check" and child.type != "otherwise":
                        statements_node = child
                        self.log(f"CONDITIONAL DEBUG: Found statements node: {child.type}")
        
        if not condition_node and node.children and hasattr(node.children[0], 'type'):
            if node.children[0].type != "statements":
                condition_node = node.children[0]
                self.log(f"CONDITIONAL DEBUG: Using first child as condition: {condition_node.type}")
        
        condition_result = False
        if condition_node:
            self.log("CONDITIONAL DEBUG: Evaluating condition")
            condition_result = self.execute_node(condition_node)
            self.log(f"CONDITIONAL DEBUG: Condition result: {condition_result}")
            
            if condition_result:
                self.log("CONDITIONAL DEBUG: Condition is TRUE, executing statements")
                results = []
                for child in node.children:
                    if child is not condition_node and child is not None:
                        if not hasattr(child, 'type') or (child.type != "otherwise_check" and child.type != "otherwise"):
                            self.log(f"CONDITIONAL DEBUG: Executing statement child of type: {child.type if hasattr(child, 'type') else 'unknown'}")
                            result = self.execute_node(child)
                            results.append(result)
                self.log("CONDITIONAL DEBUG: Finished executing statements")
                return results[-1] if results else None
        else:
            self.log("CONDITIONAL DEBUG: No condition node found!")
        
        self.log("CONDITIONAL DEBUG: Condition is FALSE, looking for otherwise blocks")
        for child in node.children:
            if child is None:
                continue
            if hasattr(child, 'type'):
                if child.type == "otherwise_check":
                    self.log("CONDITIONAL DEBUG: Found otherwise_check block")
                    result = self.execute_node(child)
                    if result is not None:
                        self.log(f"CONDITIONAL DEBUG: otherwise_check returned: {result}")
                        return result
                elif child.type == "otherwise":
                    self.log("CONDITIONAL DEBUG: Found otherwise block")
                    result = self.execute_node(child)
                    if result is not None:
                        self.log(f"CONDITIONAL DEBUG: otherwise returned: {result}")
                        return result
        
        self.log("CONDITIONAL DEBUG: No matching condition, returning None")
        return None

    def execute_condition(self, node):
        """Execute a condition expression"""
        self.log("CONDITIONAL DEBUG: Starting execute_condition")
        
        if not node.children:
            self.log("CONDITIONAL DEBUG: Condition has no children, returning False")
            return False
        
        for i, child in enumerate(node.children):
            if child is None:
                self.log(f"CONDITIONAL DEBUG: Condition child {i}: None")
                continue
            if hasattr(child, 'type'):
                self.log(f"CONDITIONAL DEBUG: Condition child {i}: Type={child.type}, Value={child.value if hasattr(child, 'value') else 'no value'}")
            else:
                self.log(f"CONDITIONAL DEBUG: Condition child {i}: No type attribute")
        
        if len(node.children) == 1:
            result = self.execute_node(node.children[0])
            self.log(f"CONDITIONAL DEBUG: Simple condition result: {result}")
            if isinstance(result, bool):
                return result
            return bool(result) 

        if len(node.children) >= 3 and hasattr(node.children[1], 'type') and node.children[1].type == "operator":
            left = self.execute_node(node.children[0])
            op = node.children[1].value
            right = self.execute_node(node.children[2])
            self.log(f"CONDITIONAL DEBUG: Comparing {left} {op} {right}")
            result = self.apply_comparison(op, left, right)
            self.log(f"CONDITIONAL DEBUG: Comparison result: {result}")
            return result
        
 
        result = self.execute_node(node.children[0])
        self.log(f"CONDITIONAL DEBUG: Initial expression result: {result}")

        if len(node.children) > 1:
            for i in range(1, len(node.children)):
                child = node.children[i]
                if hasattr(child, 'type') and child.type == "factor_tail_binop" and child.children:
                    op_node = child.children[0]
                    if hasattr(op_node, 'type') and op_node.type == "operator":
                        op = op_node.value
                        right = self.execute_node(child.children[1]) if len(child.children) > 1 else None
                        self.log(f"CONDITIONAL DEBUG: Comparing with op {op}: {result} {op} {right}")
                        result = self.apply_comparison(op, result, right)
                        self.log(f"CONDITIONAL DEBUG: Comparison result: {result}")
        

        if not isinstance(result, bool):
            self.log(f"CONDITIONAL DEBUG: Converting {result} to boolean: {bool(result)}")
            return bool(result)
        
        return result

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

    def execute_otherwise_check(self, node):
        """Execute an otherwise_check statement (else if)"""
        self.log("Executing otherwise_check")
        
    
        condition_node = None
        
        for child in node.children:
            if child is None:
                continue
            if hasattr(child, 'type') and child.type == "condition":
                condition_node = child
                break
        
    
        if not condition_node and node.children and node.children[0] is not None:
            condition_node = node.children[0]
        
  
        if condition_node:
            condition_result = self.execute_node(condition_node)
            self.log(f"Otherwise check condition result: {condition_result}")
            
          
            if condition_result:
                results = []
                for child in node.children:
                    if child is not condition_node and child is not None:
                        result = self.execute_node(child)
                        results.append(result)
                
                return results[-1] if results else None
        
        return None

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
def run_code_generation(ast):
    generator = CodeGenerator()
    generator.generate(ast)