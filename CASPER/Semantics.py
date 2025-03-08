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

        # If we see 'str $num' but no assignment error, add a debug note.
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

    ######################################################
    # Function Name Checking (No Overloading Allowed)
    ######################################################
    def visit_FUNCTION_NAME(self, node, symtable):
        """
        Whenever the AST has a node of type FUNCTION_NAME (e.g., '@myFunction'),
        we ensure that name hasn't been declared before.
        Casper does not allow function overloading:
          - same name, same signature => error
          - same name, different signature => also error
        """
        func_name = node.value  # e.g. "@compute"
        if func_name in self.declared_functions:
            self.errors.append(
                f"Semantic Error: Function '{func_name}' is already declared."
            )
        else:
            self.declared_functions.add(func_name)

    ######################################################
    # KEY POINT: Type-checking var_statement + var_tail
    ######################################################
    def visit_var_statement(self, node, symtable):
        """
        Example node structure from your debug:
          var_statement
            data_type (value=str)
            IDENT (value=$num)
            var_tail (value=)
              value
                factor
                  literal (value=3)
        """
        if len(node.children) < 3:
            self.generic_visit(node, symtable)
            return

        data_type_node = node.children[0]  # data_type(value=str)
        ident_node = node.children[1]      # IDENT(value=$num)
        var_tail_node = node.children[2]   # var_tail(value=)

        declared_type = getattr(data_type_node, "value", None)
        var_name = getattr(ident_node, "value", None)

        # Insert symbol
        try:
            if var_name and declared_type:
                symtable.add(var_name, declared_type)
        except SemanticError as e:
            self.errors.append(str(e))

        # Now check if var_tail contains a literal or expression
        self.check_var_tail(var_tail_node, symtable, declared_type, var_name)

    def check_var_tail(self, var_tail_node, symtable, declared_type, var_name):
        """Looks for 'value -> factor -> literal(...)' in var_tail."""
        if var_tail_node is None:
            return

        # If var_tail_node has children, the first child might be "value"
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

    ######################################################
    # Expression Type Inference
    ######################################################
    def get_expression_type(self, node, symtable):
        """
        We see from debug: value -> factor -> literal(3)
        We'll recursively check 'value', 'factor', 'literal'.
        """
        if node is None:
            return None

        node_type = getattr(node, "type", None)

        # If "value", check its children (often "factor")
        if node_type == "value":
            if node.children:
                return self.get_expression_type(node.children[0], symtable)

        # If "factor", check its children (often "literal" or var_call)
        if node_type == "factor":
            if node.children:
                return self.get_expression_type(node.children[0], symtable)

        # If "literal", figure out if it's int, str, etc.
        if node_type == "literal":
            val = node.value  # e.g., "Day", "Night", 5, "hello", or "'a'"
            print(val)
            # 1) If it's a Python int => "int"
            if isinstance(val, int):
                return "int"

            # 2) Day or Night => "bln"
            if val in ("Day", "Night"):
                return "bln"

            # 3) If it's exactly one character => "chr"
            if isinstance(val, str) and len(val) == 1:
                return "chr"

            # 4) Otherwise => "str"
            return "str"

        # If "var_call", look up in the symbol table
        if node_type == "var_call":
            var_name = node.value
            try:
                return symtable.lookup(var_name)
            except SemanticError:
                return None

        # Otherwise, do a generic visit
        self.generic_visit(node, symtable)
        return None

    ######################################################
    # Catch undeclared usage
    ######################################################
    def visit_var_call(self, node, symtable):
        var_name = node.value
        try:
            symtable.lookup(var_name)
        except SemanticError as e:
            if var_name not in self.reported_undeclared_vars:
                self.errors.append(str(e))
                self.reported_undeclared_vars.add(var_name)

######################################################
# Debug printing
######################################################
def debug_print_ast(node, indent=0):
    """Recursively print the AST structure for debugging."""
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
