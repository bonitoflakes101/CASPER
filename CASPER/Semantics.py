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

    def analyze(self, ast: ASTNode):
        self.visit(ast, self.global_symbols)
        return self.errors

    def visit(self, node, symtable: SymbolTable):
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

    def generic_visit(self, node: ASTNode, symtable: SymbolTable):
        if node.children:
            for child in node.children:
                self.visit(child, symtable)

    def visit_program(self, node: ASTNode, symtable: SymbolTable):
     
        if len(node.children) > 0 and node.children[0]:
            self.visit(node.children[0], symtable)
        if len(node.children) > 1 and node.children[1]:
            self.visit(node.children[1], symtable)
        if len(node.children) > 2 and node.children[2]:

            main_scope = SymbolTable(parent=symtable)
            self.visit(node.children[2], main_scope)

    def visit_global_dec(self, node: ASTNode, symtable: SymbolTable):
        if node.children:
            for child in node.children:
                self.visit(child, symtable)

    def visit_global_statement(self, node: ASTNode, symtable: SymbolTable):

        data_type_node = node.children[0]
        ident_node = node.children[1]
        var_name = ident_node.value
        var_type = data_type_node.value

        try:
            symtable.add(var_name, var_type)
        except SemanticError as e:
            self.errors.append(str(e))

        if len(node.children) > 2 and node.children[2]:
            self.visit(node.children[2], symtable)

    def visit_var_statement(self, node: ASTNode, symtable: SymbolTable):
 
        data_type_node = node.children[0]
        ident_node = node.children[1]
        var_name = ident_node.value
        var_type = data_type_node.value

        try:
            symtable.add(var_name, var_type)
        except SemanticError as e:
            self.errors.append(str(e))

        if len(node.children) > 2 and node.children[2]:
            self.visit(node.children[2], symtable)

    def visit_var_call(self, node: ASTNode, symtable: SymbolTable):

        var_name = node.value
        try:
            symtable.lookup(var_name)
        except SemanticError as e:
   
            if var_name not in self.reported_undeclared_vars:
                self.errors.append(str(e))
                self.reported_undeclared_vars.add(var_name)

    def visit_function_statements(self, node: ASTNode, symtable: SymbolTable):
        if node.children:
            for child in node.children:
                self.visit(child, symtable)

    def visit_main_function(self, node: ASTNode, symtable: SymbolTable):
        if node.children:
            for child in node.children:
                self.visit(child, symtable)

    def visit_expression(self, node: ASTNode, symtable: SymbolTable):
        self.generic_visit(node, symtable)

def run_semantic_analysis(ast: ASTNode):
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)
    return errors
