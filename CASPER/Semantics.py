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
        self.declared_functions = set()

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

        node_type = getattr(node, "type", None)

        if node_type == "value":
            if node.children:
                return self.get_expression_type(node.children[0], symtable)

        if node_type == "factor":
            if node.children:
                return self.get_expression_type(node.children[0], symtable)

        if node_type == "literal":
            val = node.value
            print(val)
            if isinstance(val, int):
                return "int"
            if val in ("Day", "Night"):
                return "bln"
            if isinstance(val, str) and len(val) == 1:
                return "chr"
            return "str"

        if node_type == "var_call":
            var_name = node.value
            try:
                return symtable.lookup(var_name)
            except SemanticError:
                return None

        self.generic_visit(node, symtable)
        return None

    def visit_var_call(self, node, symtable):
        var_name = node.value
        try:
            symtable.lookup(var_name)
        except SemanticError as e:
            if var_name not in self.reported_undeclared_vars:
                self.errors.append(str(e))
                self.reported_undeclared_vars.add(var_name)

    def visit_FUNCTION_NAME(self, node, symtable):
        func_name = node.value
        if func_name in self.declared_functions:
            self.errors.append(
                f"Semantic Error: Function '{func_name}' is already declared."
            )
        else:
            self.declared_functions.add(func_name)


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
