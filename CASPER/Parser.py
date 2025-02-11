import ply.yacc as yacc
from Lexer import tokens
from Token import TokenType


tokens = [token.name for token in TokenType]  # Ensure tokens are strings


# Abstract Syntax Tree Nodes
class ASTNode:
    def __init__(self, type, children=None, value=None):
        self.type = type
        self.children = children or []
        self.value = value

    def __repr__(self):
        return f"ASTNode({self.type}, {self.value}, {self.children})"

# Parsing Rules

def p_program(p):
    """program : BIRTH statement_list GHOST"""
    p[0] = ASTNode("program", [p[2]])

def p_statement_list(p):
    """statement_list : statement
                      | statement_list statement
                      | statement_list NEWLINE
                      | empty"""
    if len(p) == 2:  # Single statement or empty
        if p[1] is None or p[1] == []:  # ✅ Ignore empty productions
            p[0] = ASTNode("statement_list", [])  
        else:
            p[0] = ASTNode("statement_list", [p[1]])
    elif len(p) == 3:
        if isinstance(p[2], ASTNode):  # ✅ Ignore NEWLINE tokens and flatten
            p[0] = ASTNode("statement_list", p[1].children + [p[2]])
        else:
            p[0] = p[1]  # ✅ Ignore newlines in AST


def p_statement(p):
    """statement : variable_declaration
                 | assignment
                 | function_call
                 | loop
                 | conditional
                 | io_statement"""
    p[0] = p[1]



def p_variable_declaration(p):
    """variable_declaration : TYPE IDENT EQ expression"""
    p[0] = ASTNode("variable_declaration", [p[4]], p[2])

def p_assignment(p):
    """assignment : IDENT EQ expression"""
    p[0] = ASTNode("assignment", [p[3]], p[1])

def p_function_call(p):
    """function_call : FUNCTION_NAME LPAREN arguments RPAREN """
    p[0] = ASTNode("function_call", p[3], p[1])

def p_loop(p):
    """loop : REPEAT LPAREN expression RPAREN statement_list UNTIL LPAREN expression RPAREN"""
    p[0] = ASTNode("loop", [p[3], p[5], p[8]])

def p_conditional(p):
    """conditional : CHECK LPAREN expression RPAREN statement_list OTHERWISE statement_list OTHERWISE_CHECK LPAREN expression RPAREN"""
    p[0] = ASTNode("conditional", [p[3], p[5], p[7], p[10]])

def p_io_statement(p):
    """io_statement : DISPLAY LPAREN expression RPAREN"""
    p[0] = ASTNode("io_statement", [p[3]])

def p_expression(p):
    """expression : IDENT
                  | INT_LIT
                  | FLT_LIT
                  | STR_LIT
                  | function_call"""
    p[0] = ASTNode("expression", value=p[1])

def p_arguments(p):
    """arguments : expression COMMA arguments
                 | expression
                 | empty"""
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = []

def p_empty(p):
    """empty :"""
    p[0] = None

# Error Handling
def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}', line {p.lineno} (Token Type: {p.type})")
        print(f"Expected one of: TYPE, IDENT, FUNCTION_NAME, CHECK, REPEAT, DISPLAY")
    else:
        print("Syntax error at EOF")



# Build Parser
def build_parser():
    return yacc.yacc()
