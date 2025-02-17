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
    ('right', 'NOT', 'MINUS'),  # 3 - Logical NOT, Negative Indicator
    ('left', 'MULTIPLY', 'DIVISION', 'MODULO'),  # 4 - Multiplication, Division, Modulus
    ('left', 'PLUS', 'MINUS'),  # 5 - Addition, Subtraction
    ('left', 'PLUS_PLUS', 'MINUS_MINUS'),  # 6 - Postfix Increment, Decrement
    ('left', 'EQ_EQ', 'NOT_EQ', 'LT', 'GT', 'LT_EQ', 'GT_EQ'),  # 7 - Relational Operators
    ('left', 'AND'),  # 8 - Boolean AND
    ('left', 'OR'),  # 9 - Boolean OR
    ('right', 'EQ', 'PLUS_EQ', 'MINUS_EQ', 'MUL_EQ', 'DIV_EQ', 'MOD_EQ')  # 10 - Assignment Operators
)



# Parsing Rules

def p_program(p):
    """program : BIRTH global_declarations statements GHOST"""
    p[0] = ASTNode("program", [p[2], p[3]])

def p_statements(p):
    """statements : conditional_statement statements_tail
                   | loop_statement statements_tail
                   | function_statement statements_tail
                   | switch_statement statements_tail
                   | output_statement statements_tail
                   | assignment_statement statements_tail
                   | expression
                   | declarations
                   | empty"""
    if len(p) == 3:
        p[0] = ASTNode("statements", [p[1], p[2]])
    elif len(p) == 2:
        p[0] = ASTNode("statements", [p[1]])

def p_statements_tail(p):
    """statements_tail : statements
                        | empty"""
    p[0] = ASTNode("statements_tail", [p[1]]) if p[1] else ASTNode("statements_tail", [])

def p_global_declarations(p):
    """global_declarations : declarations"""
    p[0] = ASTNode("global_declarations", [p[1]])

def p_declarations(p):
    """declarations : GLOBAL var_call
                     | var_dec
                     | var_initialization
                     | list_dec
                     | list_init
                     | empty"""
    if len(p) == 3:
        p[0] = ASTNode("declarations", [p[2]], p[1])
    else:
        p[0] = ASTNode("declarations", [p[1]])

def p_var_dec(p):
    """var_dec : data_type IDENT vardec_tail"""
    p[0] = ASTNode("var_dec", [p[1], p[3]], p[2])

def p_vardec_tail(p):
    """vardec_tail : COMMA IDENT vardec_tail
                    | empty"""
    if len(p) == 4:
        p[0] = ASTNode("vardec_tail", [p[2], p[3]])
    else:
        p[0] = ASTNode("vardec_tail", [])

def p_var_initialization(p):
    """var_initialization : data_type IDENT EQ value varinit_tail"""
    p[0] = ASTNode("var_initialization", [p[1], p[2], p[4], p[5]])

def p_varinit_tail(p):
    """varinit_tail : COMMA IDENT EQ value varinit_tail
                     | empty"""
    if len(p) == 6:
        p[0] = ASTNode("varinit_tail", [p[2], p[4], p[5]])
    else:
        p[0] = ASTNode("varinit_tail", [])

def p_data_type(p):
    """data_type : INT
                  | FLT
                  | BLN
                  | CHR
                  | STR"""
    p[0] = ASTNode("data_type", value=p[1])

def p_value(p):
    """value : literal
              | expression
              | var_call
              | function_call
              | type_cast
              | not_op
              | negative_val"""
    p[0] = ASTNode("value", [p[1]])


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
