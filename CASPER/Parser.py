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

def p_negative_val(p):
    """negative_val : TILDE INT_LIT
                     | TILDE FLT_LIT"""
    p[0] = ASTNode("negative_val", [p[2]])

def p_literal(p):
    """literal : INT_LIT
                | FLT_LIT
                | BLN_LIT
                | CHR_LIT
                | STR_LIT"""
    p[0] = ASTNode("literal", value=p[1])

def p_expression(p):
    """expression : arithmetic_expression
                   | relational_expression
                   | logical_expression
                   | string_concat"""
    p[0] = ASTNode("expression", [p[1]])

def p_arithmetic_expression(p):
    """arithmetic_expression : ae_term"""
    p[0] = ASTNode("arithmetic_expression", [p[1]])

def p_ae_term(p):
    """ae_term : ae_factor ae_tail2
                | LPAREN ae_factor ae_tail2 RPAREN ae_tail2"""
    if len(p) == 3:
        p[0] = ASTNode("ae_term", [p[1], p[2]])
    else:
        p[0] = ASTNode("ae_term", [p[2], p[3], p[5]])

def p_ae_factor(p):
    """ae_factor : INT_LIT
                  | FLT_LIT
                  | var_call"""
    p[0] = ASTNode("ae_factor", value=p[1])

def p_ae_tail(p):
    """ae_tail : PLUS ae_term ae_tail
                | MINUS ae_term ae_tail
                | DIVIDE ae_term ae_tail
                | MULTIPLY ae_term ae_tail
                | MODULO ae_term ae_tail
                | EXPONENT ae_term ae_tail
                | empty"""
    if len(p) == 4:
        p[0] = ASTNode("ae_tail", [p[2], p[3]], p[1])
    else:
        p[0] = ASTNode("ae_tail", [])

def p_ae_tail2(p):
    """ae_tail2 : ae_term
                 | ae_tail
                 | empty """
    p[0] = ASTNode("ae_tail2", [p[1]])

def p_relational_expression(p):
    """relational_expression : re_term"""
    p[0] = ASTNode("relational_expression", [p[1]])

def p_re_term(p):
    """re_term : re_factor re_tail2
                | LPAREN re_factor re_tail2 RPAREN re_tail2"""
    if len(p) == 3:
        p[0] = ASTNode("re_term", [p[1], p[2]])
    else:
        p[0] = ASTNode("re_term", [p[2], p[3], p[5]])

def p_re_factor(p):
    """re_factor : arithmetic_expression
                  | INT_LIT
                  | FLT_LIT
                  | BLN_LIT
                  | var_call"""
    p[0] = ASTNode("re_factor", value=p[1])

def p_re_tail(p):
    """re_tail : GT re_term re_tail2
                | LT re_term re_tail2
                | EQ re_term re_tail2
                | NEQ re_term re_tail2
                | GE re_term re_tail2
                | LE re_term re_tail2"""
    p[0] = ASTNode("re_tail", [p[2], p[3]], p[1])

def p_re_tail2(p):
    """re_tail2 : empty
                 | re_tail
                 | re_term"""
    p[0] = ASTNode("re_tail2", [p[1]]) if p[1] else ASTNode("re_tail2", [])

def p_logical_expression(p):
    """logical_expression : le_term"""
    p[0] = ASTNode("logical_expression", [p[1]])

def p_le_term(p):
    """le_term : le_factor le_tail2
                | LPAREN le_factor le_tail2 RPAREN le_tail2"""
    if len(p) == 3:
        p[0] = ASTNode("le_term", [p[1], p[2]])
    else:
        p[0] = ASTNode("le_term", [p[2], p[3], p[5]])

def p_le_factor(p):
    """le_factor : BLN_LIT
                  | relational_expression
                  | var_call"""
    p[0] = ASTNode("le_factor", value=p[1])

def p_le_tail(p):
    """le_tail : AND le_term
                | OR le_term
                | NOT le_term"""
    p[0] = ASTNode("le_tail", [p[2]], p[1])

def p_le_tail2(p):
    """le_tail2 : empty
                | le_tail
                | le_term"""
    if len(p) == 2:
        p[0] = ASTNode("le_tail2", [p[1]]) if p[1] else ASTNode("le_tail2", [])

def p_var_call(p):
    """var_call : IDENTIFIER
                | IDENTIFIER LBRACKET index RBRACKET"""
    if len(p) == 2:
        p[0] = ASTNode("var_call", value=p[1])
    else:
        p[0] = ASTNode("var_call", [p[3]], p[1])

def p_list_dec(p):
    """list_dec : list_dtype IDENTIFIER listdec_tail"""
    p[0] = ASTNode("list_dec", [p[1], p[4], p[5]])

def p_listdec_tail(p):
    """listdec_tail : COMMA IDENTIFIER listdec_tail
                     | empty"""
    if len(p) == 4:
        p[0] = ASTNode("listdec_tail", [p[2], p[3]])
    else:
        p[0] = ASTNode("listdec_tail", [])

def p_list_init(p):
    """list_init : list_dtype IDENTIFIER LBRACKET index RBRACKET EQ LBRACKET list_element RBRACKET listinit_tail"""
    p[0] = ASTNode("list_init", [p[1], p[2], p[4], p[8], p[9]])

def p_listinit_tail(p):
    """listinit_tail : COMMA IDENTIFIER LBRACKET index RBRACKET EQ LBRACKET list_element RBRACKET listinit_tail
                      | empty"""
    if len(p) == 11:
        p[0] = ASTNode("listinit_tail", [p[2], p[4], p[8], p[10]])
    else:
        p[0] = ASTNode("listinit_tail", [])

def p_list_dtype(p):
    """list_dtype : LIST_INT
                  | LIST_FLT
                  | LIST_BLN
                  | LIST_STR
                  | LIST_CHR"""
    p[0] = ASTNode("list_dtype", value=p[1])

def p_list_element(p):
    """list_element : value
                     | value COMMA list_element"""
    if len(p) == 2:
        p[0] = ASTNode("list_element", [p[1]])
    else:
        p[0] = ASTNode("list_element", [p[1], p[3]])

def p_index(p):
    """index : INT_LIT
              | IDENTIFIER"""
    p[0] = ASTNode("index", value=p[1])

def p_conditional_statement(p):
    """conditional_statement : CHECK LPAREN condition RPAREN LBRACE statements RBRACE conditional_tail"""
    p[0] = ASTNode("conditional_statement", [p[3], p[6], p[8]])

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
