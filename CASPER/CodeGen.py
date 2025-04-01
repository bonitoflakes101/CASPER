from Parser import ASTNode

class CodeGenerator:
    def __init__(self):
        # Global variables dictionary
        self.global_vars = {}
        # Environment stack, where the first element is the global scope
        self.env_stack = [self.global_vars]
        # Set debug mode
        self.debug = True

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
        # Search from the innermost (local) scope outward
        for env in reversed(self.env_stack):
            self.log(f"Checking env: {env}")
            if var_name in env:
                self.log(f"Found '{var_name}' with value: {env[var_name]}")
                return env[var_name]
        self.log(f"Variable '{var_name}' not found in any environment")
        return None

    def assign_variable(self, var_name, value):
        self.log(f"Assigning '{var_name}' = {value}")
        # Try to assign in the innermost scope where it exists
        for env in reversed(self.env_stack):
            if var_name in env:
                env[var_name] = value
                return
        # If not found, store globally
        self.global_vars[var_name] = value

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
        
        # Flatten children first
        if node.children:
            node.children = self.flatten_nodes(node.children)

        method_name = f"execute_{node.type}"
        executor = getattr(self, method_name, self.generic_execute)
        result = executor(node)
        self.log(f"Result of execute_{node.type}: {result}")
        return result

    def generic_execute(self, node):
        self.log(f"Using generic_execute for node type: {node.type}")
        # Default: execute children
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
        
        # Process all nodes in the program
        for child in node.children:
            if hasattr(child, 'type'):
                if child.type == "global_statement":
                    result = self.execute_global_statement(child)
                    results.append(result)
                elif child.type == "main_function":
                    result = self.execute_main_function(child)
                    results.append(result)
                else:
                    result = self.execute_node(child)
                    results.append(result)
        
        return results[-1] if results else None

    def execute_main_function(self, node):
        self.log("Executing main_function")
        # We push a scope for the main
        self.push_scope()
        results = []
        # The main_function node typically has child statements
        if node.children:
            for child in node.children:
                result = self.execute_node(child)
                results.append(result)
        else:
            print("Warning: main_function node has no statements.")
        self.pop_scope()
        return results[-1] if results else None

    # ==========================
    #    STATEMENTS
    # ==========================
    
    def execute_global_statement(self, node):
        self.log("Executing global_statement")
        self.log(f"Global statement children: {node.children}")
        
        # Get necessary information from children
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
                    var_name = child.value
                elif child.type == "expression":
                    var_value = self.execute_node(child)
                elif child.type == "literal":
                    var_value = child.value
        
        self.log(f"Parsed global: name={var_name}, type={data_type}, value={var_value}")
        
        # If we have a value, use it, otherwise set default value based on type
        if var_value is None:
            if data_type == "int":
                var_value = 0
            elif data_type == "string":
                var_value = ""
            elif data_type == "float":
                var_value = 0.0
            elif data_type == "bool":
                var_value = False
        
        # Store the variable in global scope
        if var_name:
            self.global_vars[var_name] = var_value
            self.log(f"Set global variable '{var_name}' to {var_value}")
        
        return var_value

    def execute_var_statement(self, node):
        self.log("Executing var_statement")
        self.log(f"var_statement children: {node.children}")
        
        # Filter out None nodes
        valid_children = [child for child in node.children if child is not None]
        self.log(f"Valid children after filtering None: {valid_children}")
        
        if len(valid_children) < 3:
            print("Error: Not enough valid children in var_statement.")
            return None

        # Get variable name from the first IDENT node
        var_name = None
        for child in valid_children:
            if hasattr(child, 'type') and child.type == "IDENT":
                var_name = child.value
                break
        
        if not var_name:
            print("Error: Could not find variable name in var_statement.")
            return None
        
        # Find the local_var_assign node
        assign_node = None
        for child in valid_children:
            if hasattr(child, 'type') and child.type == "local_var_assign":
                assign_node = child
                break
        
        if not assign_node:
            print("Error: Could not find local_var_assign node in var_statement.")
            return None
        
        # Now traverse from local_var_assign to the literal
        self.log(f"Found assign_node: {assign_node}")
        
        # Manually traverse the AST to get the literal value
        if assign_node.children:
            value_node = assign_node.children[0]  # 'value' node
            if value_node and value_node.children:
                expr_node = value_node.children[0]  # 'expression' node
                if expr_node and expr_node.children:
                    literal_node = expr_node.children[0]  # 'literal' node
                    if literal_node and hasattr(literal_node, 'value'):
                        value = literal_node.value
                        self.log(f"Found literal value: {value}")
                        self.get_current_env()[var_name] = value
                        self.log(f"Environment after assignment: {self.get_current_env()}")
                        return value
        
        # Fallback to regular execution if direct traversal fails
        value = self.execute_node(assign_node)
        self.log(f"Fallback: Assigning variable: '{var_name}' = {value}")
        
        self.get_current_env()[var_name] = value
        self.log(f"Environment after assignment: {self.get_current_env()}")
        return value
        
    def execute_local_var_assign(self, node):
        self.log(f"Executing local_var_assign: {node}")
        # local_var_assign -> child: value -> child: expression
        if not node.children:
            self.log("local_var_assign has no children")
            return None
        
        # Execute the value node (which will execute the expression, which will execute the literal)
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
        print(result)  # This is the actual output to the console
        return result

    # ==========================
    #    EXPRESSIONS
    # ==========================

    def execute_value(self, node):
        self.log(f"Executing value: {node}")
        # value -> child: expression, or literal, etc.
        if node.children:
            result = self.execute_node(node.children[0])
            self.log(f"Value result: {result}")
            return result
        self.log("Value has no children")
        return None

    def execute_expression(self, node):
        self.log(f"Executing expression: {node}")
        # expression can have multiple forms
        # from your AST, we see expression -> literal or expression -> var_postfix
        if node.children:
            result = self.execute_node(node.children[0])
            self.log(f"Expression result: {result}")
            return result
        self.log("Expression has no children")
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
        self.log(f"var_call looking up: '{var_name}'")
        result = self.lookup_variable(var_name)
        self.log(f"var_call result: {result}")
        return result

    # Handle IDENT node directly if needed
    def execute_IDENT(self, node):
        self.log(f"Executing IDENT: {node}")
        return node.value

def run_code_generation(ast):
    generator = CodeGenerator()
    generator.generate(ast)