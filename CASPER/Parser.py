import ply.yacc as yacc
from Lexer import tokens
from Token import TokenType

tokens = [token.name for token in TokenType]

# Define valid types
valid_types = {"int", "flt", "str", "chr", "bln"}  # Ensure tokens are strings

# Abstract Syntax Tree Nodes
class ASTNode:
    def __init__(self, type, children=None, value=None):
        self.type = type
        self.children = children or []
        self.value = value

    def __repr__(self):
        return f"ASTNode({self.type}, {self.value}, {self.children})"
    
precedence = (
    ('right', 'EXPONENT'),  # 2 - Exponentiation
    ('right', 'NOT', 'NEGATE'),  # 3 - Logical NOT, Negative Indicator
    ('left', 'MULTIPLY', 'DIVISION', 'MODULO'),  # 4 - Multiplication, Division, Modulus
    ('left', 'PLUS', 'MINUS'),  # 5 - Addition, Subtraction
    ('left', 'INCREMENT', 'DECREMENT'),  # 6 - Postfix Increment, Decrement
    ('left', 'EQ_EQ', 'NOT_EQ', 'LT', 'GT', 'LT_EQ', 'GT_EQ'),  # 7 - Relational Operators
    ('left', 'AND'),  # 8 - Boolean AND
    ('left', 'OR'),  # 9 - Boolean OR (Lower than AND)
    ('right', 'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'MULTIPLY_ASSIGN', 'DIVISION_ASSIGN', 'MODULO_ASSIGN')  # 10 - Assignment Operators
)


# Parsing Rules

def p_program(p):
    """program : BIRTH global_declarations statements GHOST"""
    p[0] = ASTNode("program", [p[2], p[3]])


def p_var_call(p):
    """var_call : IDENT"""
    p[0] = ASTNode("var_call", value=p[1])

def p_var_dec(p):
    """var_dec : INT IDENT
               | FLT IDENT
               | STR IDENT
               | CHR IDENT
               | BLN IDENT"""
    p[0] = ASTNode("var_dec", value=p[2])

def p_var_initialization(p):
    """var_initialization : var_dec EQ expression"""
    p[0] = ASTNode("var_initialization", [p[3]], p[1])

def p_list_dec(p):
    """list_dec : INT LBRACKET RBRACKET IDENT
                 | FLT LBRACKET RBRACKET IDENT
                 | STR LBRACKET RBRACKET IDENT
                 | CHR LBRACKET RBRACKET IDENT
                 | BLN LBRACKET RBRACKET IDENT"""
    p[0] = ASTNode("list_dec", value=p[4])

def p_global_declarations(p):
    """global_declarations : GLOBAL var_call
                            | var_dec
                            | var_initialization
                            | list_dec
                            | empty"""
    p[0] = ASTNode("global_declarations", [p[1]]) if len(p) > 1 else ASTNode("global_declarations", [])


def p_statements(p):
    """statements : statement
                   | statements statement
                   | statements NEWLINE
                   | empty"""
    if len(p) == 2:
        p[0] = ASTNode("statements", [p[1]]) if p[1] else ASTNode("statements", [])
    elif len(p) == 3:
        p[0] = ASTNode("statements", p[1].children + [p[2]])


def p_statement(p):
    """statement : variable_declaration
                 | assignment
                 | function_call
                 | function_declaration
                 | loop
                 | conditional
                 | io_statement
                 | switch_statement
                 | return_statement
                 | stop_statement
                 | skip_statement
                 | measure_statement"""
    p[0] = p[1]

def p_function_declaration(p):
    """function_declaration : FUNCTION FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements RBRACE
                              | FUNCTION_INT FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements RBRACE
                              | FUNCTION_FLT FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements RBRACE
                              | FUNCTION_STR FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements RBRACE
                              | FUNCTION_CHR FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements RBRACE
                              | FUNCTION_BLN FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements RBRACE"""
    p[0] = ASTNode("function_declaration", [p[1], p[2], p[4], p[7]])

def p_parameters(p):
    """parameters : INT IDENT COMMA parameters
                   | FLT IDENT COMMA parameters
                   | STR IDENT COMMA parameters
                   | CHR IDENT COMMA parameters
                   | BLN IDENT COMMA parameters
                   | INT IDENT
                   | FLT IDENT
                   | STR IDENT
                   | CHR IDENT
                   | BLN IDENT
                   | empty"""
    if len(p) == 2:
        p[0] = []
    elif len(p) == 4:
        p[0] = [(p[1], p[2])] + p[4]  # Ensure proper list concatenation
    else:
        p[0] = [(p[1], p[2])]


def p_variable_declaration(p):
    """variable_declaration : INT IDENT EQ expression
                            | FLT IDENT EQ expression
                            | STR IDENT EQ expression
                            | CHR IDENT EQ expression
                            | BLN IDENT EQ expression"""
    p[0] = ASTNode("variable_declaration", [p[4]], p[2])


def p_assignment(p):
    """assignment : IDENT EQ expression"""
    p[0] = ASTNode("assignment", [p[3]], p[1])


def p_function_call(p):
    """function_call : FUNCTION_NAME LPAREN arguments RPAREN""" # can change into function_name if needed
    p[0] = ASTNode("function_call", p[3], p[1])


def p_loop(p):
    """loop : REPEAT LPAREN expression RPAREN LBRACE statements RBRACE UNTIL LPAREN expression RPAREN"""
    p[0] = ASTNode("loop", [p[3], p[6], p[10]])


def p_conditional(p):
    """conditional : CHECK LPAREN expression RPAREN LBRACE statements RBRACE OTHERWISE LBRACE statements RBRACE OTHERWISE_CHECK LPAREN expression RPAREN"""
    p[0] = ASTNode("conditional", [p[3], p[6], p[10], p[13]])


def p_io_statement(p):
    """io_statement : DISPLAY LPAREN expression RPAREN
                    | INPUT LPAREN IDENT RPAREN"""
    p[0] = ASTNode("io_statement", [p[3]])
    """io_statement : DISPLAY LPAREN expression RPAREN"""
    p[0] = ASTNode("io_statement", [p[3]])




def p_switch_statement(p):
    """switch_statement : SWAP LPAREN expression RPAREN LBRACE case_list RBRACE"""
    p[0] = ASTNode("switch_statement", [p[3], p[6]])


def p_case_list(p):
    """case_list : case
                 | case_list case"""
    if len(p) == 2:
        p[0] = ASTNode("case_list", [p[1]])
    else:
        p[0] = ASTNode("case_list", p[1].children + [p[2]])


def p_case(p):
    """case : SHIFT expression COLON statements"""
    p[0] = ASTNode("case", [p[2], p[4]])


def p_return_statement(p):
    """return_statement : REVIVE expression"""
    p[0] = ASTNode("return_statement", [p[2]])

def p_stop_statement(p):
    """stop_statement : STOP"""
    p[0] = ASTNode("stop_statement")

def p_skip_statement(p):
    """skip_statement : SKIP"""
    p[0] = ASTNode("skip_statement")

def p_measure_statement(p):
    """measure_statement : MEASURE LPAREN expression RPAREN"""
    p[0] = ASTNode("measure_statement", [p[3]])
    """return_statement : REVIVE expression"""
    p[0] = ASTNode("return_statement", [p[2]])


def p_expression(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression MULTIPLY expression
                  | expression DIVISION expression
                  | expression MODULO expression
                  | expression EXPONENT expression
                  | expression EQ_EQ expression
                  | expression NOT_EQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LT_EQ expression
                  | expression GT_EQ expression
                  | expression AND expression
                  | expression OR expression
                  | NOT expression
                  | LPAREN expression RPAREN
                  | IDENT
                  | INT_LIT
                  | FLT_LIT
                  | STR_LIT
                  | BLN_LIT
                  | function_call"""
    if len(p) == 2:
        p[0] = ASTNode("expression", value=p[1])
    elif len(p) == 4:
        p[0] = ASTNode("binary_expression", [p[1], p[3]], p[2])
    elif len(p) == 3:
        p[0] = ASTNode("unary_expression", [p[2]], p[1])
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression MULTIPLY expression
                  | expression DIVISION expression
                  | expression MODULO expression
                  | expression EXPONENT expression
                  | expression EQ_EQ expression
                  | expression NOT_EQ expression
                  | expression LT expression
                  | expression GT expression
                  | expression LT_EQ expression
                  | expression GT_EQ expression
                  | expression AND expression
                  | expression OR expression
                  | NOT expression
                  | LPAREN expression RPAREN
                  | IDENT
                  | INT_LIT
                  | FLT_LIT
                  | STR_LIT
                  | BLN_LIT
                  | function_call"""
    if len(p) == 2:
        p[0] = ASTNode("expression", value=p[1])
    elif len(p) == 3:
        p[0] = ASTNode("unary_expression", [p[2]], p[1])
    else:
        p[0] = ASTNode("binary_expression", [p[1], p[3]], p[2])

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
    else:
        print("Syntax error at EOF")


# Build Parser
def build_parser():
    return yacc.yacc()
