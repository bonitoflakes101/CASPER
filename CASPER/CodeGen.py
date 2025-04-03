from Parser import ASTNode

class CodeGenerator:
    def __init__(self):
        self.global_vars = {}
        self.env_stack = [self.global_vars]
        self.functions = {}
        self.return_values = []
        self.debug = False

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
        
    
        if node.children:
            node.children = self.flatten_nodes(node.children)

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
        func_return_type = "void" 
        
        for child in node.children:
            if hasattr(child, 'type'):
                if child.type == "FUNCTION_NAME":
                    func_name = child.value
                elif child.type == "return_type":
                    func_return_type = child.value
                
        if not func_name:
            print("Error: Function declaration missing name")
            return None
            
        self.log(f"Defining function: {func_name} with return type: {func_return_type}")
        
        self.functions[func_name] = {
            'node': node,
            'params': [],
            'return_type': func_return_type
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
        result = None
        
        for child in func_node.children:
            if hasattr(child, 'type') and child.type == "statements":
                for statement in child.children:
                    self.execute_node(statement)
                    if self.return_values:
                        break
            else:
                self.execute_node(child)

        return_value = None
        if self.functions[func_name]['return_type'] != "void":
            if self.return_values:
                return_value = self.return_values.pop()
                self.log(f"Function returned: {return_value}")
            else:
                print(f"Warning: Function '{func_name}' expected to return a value but didn't")
        else:
            if self.return_values:
                self.return_values.pop()  
                self.log("Void function had a return value that was discarded")

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
        
    def execute_void_statement(self, node):
        self.log("Executing void_statement")
        
        self.return_values.append(None)
        
        return None

    def execute_return_type(self, node):
        self.log(f"Executing return_type: {node}")
        return node.value
        
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
        
        if len(valid_children) < 2:  
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
        
        assign_node = None
        for child in valid_children:
            if hasattr(child, 'type') and (child.type == "local_var_assign" or child.type == "expression" or child.type == "function_call"):
                assign_node = child
                break
        
        if not assign_node:
            print("Error: Could not find assignment expression in var_statement.")
            return None
        
        value = self.execute_node(assign_node)
        self.log(f"Evaluated expression value: {value}")
        
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
        return node.value

    def execute_data_type(self, node):
        self.log(f"Executing data_type: {node}")
        return node.value

    # ==========================
    #    VARIABLE CALLS
    # ==========================

    def execute_var_postfix(self, node):
        self.log(f"Executing var_postfix: {node}")
     
        if not node.children:
            self.log("var_postfix has no children")
            return None
            
   
        valid_children = [child for child in node.children if child is not None]
        if not valid_children:
            self.log("var_postfix has no valid children")
            return None
            
   
        result = self.execute_node(valid_children[0])
        self.log(f"var_postfix result: {result}")
        return result

    def execute_var_call(self, node):
        self.log(f"Executing var_call: {node}")
     
        if not node.children:
            self.log("var_call has no children")
            return None
            
        var_name = node.children[0].value
   
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
    
        return None
        
    def execute_param_decl(self, node):
        self.log(f"Executing param_decl: {node}")
   
        return None
        
    def execute_arguments(self, node):
        self.log(f"Executing arguments: {node}")
  
        results = []
        if node.children:
            for child in node.children:
                result = self.execute_node(child)
                results.append(result)
        return results

    def execute_IDENT(self, node):
        self.log(f"Executing IDENT: {node}")
        return node.value
        
    def execute_FUNCTION_NAME(self, node):
        self.log(f"Executing FUNCTION_NAME: {node}")
        return node.value
    
    def execute_statements(self, node):
        self.log(f"Executing statements block: {node}")
        results = []
        if node.children:
            for child in node.children:
                result = self.execute_node(child)

                if self.return_values:
                    break
                results.append(result)
        return results[-1] if results else None

def run_code_generation(ast):
    generator = CodeGenerator()
    generator.generate(ast)