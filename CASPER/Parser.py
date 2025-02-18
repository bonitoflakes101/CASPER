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
                   | expression statements_tail
                   | declarations statements_tail
                   | empty"""
    if len(p) == 3:
        p[0] = ASTNode("statements", [p[1]] + (p[2].children if isinstance(p[2], ASTNode) else []))
    else:
        p[0] = ASTNode("statements", [p[1]]) if p[1] else ASTNode("statements", [])

def p_statements_tail(p):
    """statements_tail : statements_tail
                        | statements
                        | empty"""
    if len(p) == 3 and p[1] == "\n":  # Ignore NEWLINE tokens
        p[0] = p[2]
    elif len(p) == 2:
        p[0] = p[1]  
    else:
        p[0] = ASTNode("statements_tail", [])  


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
                | DIVISION ae_term ae_tail
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
                | NOT_EQ re_term re_tail2
                | GT_EQ re_term re_tail2
                | LT_EQ re_term re_tail2"""
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
    """var_call : IDENT
                | IDENT LBRACKET index RBRACKET"""
    if len(p) == 2:
        p[0] = ASTNode("var_call", value=p[1])
    else:
        p[0] = ASTNode("var_call", [p[3]], p[1])

def p_list_dec(p):
    """list_dec : list_dtype IDENT listdec_tail"""
    p[0] = ASTNode("list_dec", [p[1], p[2], p[3]])


def p_listdec_tail(p):
    """listdec_tail : COMMA IDENT listdec_tail
                     | empty"""
    if len(p) == 4:
        p[0] = ASTNode("listdec_tail", [p[2], p[3]])
    else:
        p[0] = ASTNode("listdec_tail", [])

def p_list_init(p):
    """list_init : list_dtype IDENT LBRACKET index RBRACKET EQ LBRACKET list_element RBRACKET listinit_tail"""
    p[0] = ASTNode("list_init", [p[1], p[2], p[4], p[8], p[10]])


def p_listinit_tail(p):
    """listinit_tail : COMMA IDENT LBRACKET index RBRACKET EQ LBRACKET list_element RBRACKET listinit_tail
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

# bawal float?
def p_index(p):
    """index : INT_LIT
              | IDENT"""
    p[0] = ASTNode("index", value=p[1])

def p_conditional_statement(p):
    """conditional_statement : CHECK LPAREN condition RPAREN LBRACE statements RBRACE conditional_tail"""
    p[0] = ASTNode("conditional_statement", [p[3], p[6], p[8]])

def p_conditional_tail(p):
    """conditional_tail : OTHERWISE_CHECK LPAREN condition RPAREN LBRACE statements RBRACE
                         | OTHERWISE LBRACE statements RBRACE
                         | empty"""
    if len(p) == 8:
        p[0] = ASTNode("conditional_tail", [p[3], p[6]])
    elif len(p) == 5:
        p[0] = ASTNode("conditional_tail", [p[3]])
    else:
        p[0] = ASTNode("conditional_tail", [])

def p_switch_statement(p):
    """switch_statement : SWAP LPAREN IDENT RPAREN LBRACE switch_condition OTHERWISE statements RBRACE"""
    p[0] = ASTNode("switch_statement", [p[3], p[6], p[8]])

def p_switch_condition(p):
    """switch_condition : SHIFT value COLON statements switch_cond_tail"""
    p[0] = ASTNode("switch_condition", [p[2], p[4], p[5]])

def p_switch_cond_tail(p):
    """switch_cond_tail : switch_condition
                         | empty"""
    p[0] = ASTNode("switch_cond_tail", [p[1]]) if p[1] else ASTNode("switch_cond_tail", [])

def p_condition(p):
    """condition : relational_expression
                 | logical_expression"""
    p[0] = ASTNode("condition", [p[1]])

def p_loop_statement(p):
    """loop_statement : for_loop
                      | until_loop
                      | repeat_until"""
    p[0] = ASTNode("loop_statement", [p[1]])

def p_for_loop(p):
    """for_loop : FOR LPAREN control_variable SEMICOLON relational_expression SEMICOLON update RPAREN LBRACE statements RBRACE"""
    p[0] = ASTNode("for_loop", [p[3], p[5], p[7], p[10]])

def p_until_loop(p):
    """until_loop : UNTIL LPAREN relational_expression RPAREN LBRACE statements RBRACE"""
    p[0] = ASTNode("until_loop", [p[3], p[6]])

def p_repeat_until(p):
    """repeat_until : REPEAT LBRACE statements RBRACE UNTIL LPAREN relational_expression RPAREN"""
    p[0] = ASTNode("repeat_until", [p[3], p[7]])

def p_control_variable(p):
    """control_variable : IDENT EQ INT_LIT
                        | var_call"""
    p[0] = ASTNode("control_variable", [p[1], p[3]]) if len(p) == 4 else ASTNode("control_variable", [p[1]])

def p_update(p):
    """update : unary
              | assignment_statement"""
    p[0] = ASTNode("update", [p[1]])

def p_unary(p):
    """unary : value unary_op"""
    p[0] = ASTNode("unary", [p[1]], p[2])

def p_unary_op(p):
    """unary_op : PLUS_PLUS
                 | MINUS_MINUS"""
    p[0] = ASTNode("unary_op", value=p[1])

def p_assignment_statement(p):
    """assignment_statement : var_call assign_op value"""
    p[0] = ASTNode("assignment_statement", [p[1], p[3]], p[2])

def p_assign_op(p):
    """assign_op : PLUS_EQ
                 | MINUS_EQ
                 | MUL_EQ
                 | DIV_EQ
                 | MOD_EQ"""
    p[0] = ASTNode("assign_op", value=p[1])

def p_function_statement(p):
    """function_statement : ret_type FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements revive RBRACE
                           | function_call"""
    if len(p) == 10:
        p[0] = ASTNode("function_statement", [p[1], p[2], p[4], p[7], p[8]])
    else:
        p[0] = ASTNode("function_statement", [p[1]])

def p_function_call(p):
    """function_call : FUNCTION_NAME LPAREN arguments RPAREN
                     | output_statement
                     | input_statement"""
    if len(p) == 5:
        p[0] = ASTNode("function_call", [p[1], p[3]])
    else:
        p[0] = ASTNode("function_call", [p[1]])

def p_arguments(p):
    """arguments : var_call
                 | literal"""
    p[0] = ASTNode("arguments", [p[1]])

def p_ret_type(p):
    """ret_type : FUNCTION
                 | function_dtype"""
    p[0] = ASTNode("ret_type", [p[1]])


# function_list_int, function_bln etc... sa CFG
def p_function_dtype(p):
    """function_dtype : FUNCTION_INT
                      | FUNCTION_FLT
                      | FUNCTION_CHR
                      | FUNCTION_STR
                      | FUNCTION_BLN
                      | FUNCTION_LIST_INT
                      | FUNCTION_LIST_FLT
                      | FUNCTION_LIST_CHR
                      | FUNCTION_LIST_STR
                      | FUNCTION_LIST_BLN"""
    p[0] = ASTNode("function_dtype", value=p[1])

def p_parameters(p):
    """parameters : data_type IDENT parameters_tail
                  | empty"""
    if len(p) == 4:
        p[0] = ASTNode("parameters", [p[1], p[2]] + (p[3].children if isinstance(p[3], ASTNode) else []))
    else:
        p[0] = ASTNode("parameters", [])


def p_parameters_tail(p):
    """parameters_tail : COMMA data_type IDENT parameters_tail
                        | empty"""
    if len(p) == 5:
        p[0] = ASTNode("parameters_tail", [p[2], p[3]] + (p[4].children if isinstance(p[4], ASTNode) else []))
    else:
        p[0] = ASTNode("parameters_tail", [])



def p_revive(p):
    """revive : REVIVE value
               | empty"""
    p[0] = ASTNode("revive", [p[2]]) if len(p) == 3 else ASTNode("revive", [])

# new DISPLAY LPAREN value RPAREN, wala sa cfg
def p_output_statement(p):
    """output_statement : DISPLAY value
                        """
    if len(p) == 3:
        p[0] = ASTNode("output_statement", [p[2]])
    else:
        p[0] = ASTNode("output_statement", [p[3]])


def p_input_statement(p):
    """input_statement : INPUT LPAREN statements RPAREN"""
    p[0] = ASTNode("input_statement", [p[3]])

def p_type_cast(p):
    """type_cast : CONVERT_TO_INT LPAREN value RPAREN
                 | CONVERT_TO_FLT LPAREN value RPAREN
                 | CONVERT_TO_BLN LPAREN value RPAREN
                 | CONVERT_TO_STR LPAREN value RPAREN"""
    p[0] = ASTNode("type_cast", [p[3]], p[1])

def p_string_concat(p):
    """string_concat : string_lit stringcon_tail"""
    p[0] = ASTNode("string_concat", [p[1], p[2]])

def p_stringcon_tail(p):
    """stringcon_tail : PLUS string_lit stringcon_tail2"""
    p[0] = ASTNode("stringcon_tail", [p[2], p[3]])

def p_stringcon_tail2(p):
    """stringcon_tail2 : stringcon_tail
                        | empty"""
    p[0] = ASTNode("stringcon_tail2", [p[1]]) if p[1] else ASTNode("stringcon_tail2", [])

def p_string_lit(p):
    """string_lit : STR_LIT"""
    p[0] = ASTNode("string_lit", value=p[1])

def p_not_op(p):
    """not_op : NOT value"""
    p[0] = ASTNode("not_op", [p[2]])

def p_arithmetic_op(p):
    """arithmetic_op : PLUS
                      | MINUS
                      | DIVISION
                      | MULTIPLY
                      | MODULO"""
    p[0] = ASTNode("arithmetic_op", value=p[1])



def p_empty(p):
    """empty :"""
    p[0] = None


# Error Handling
def p_error(p):
    if p:
        error_message = f"Syntax Error: Unexpected token '{p.value}' at line {p.lineno} (Token Type: {p.type})"
    else:
        error_message = "Syntax Error: Unexpected end of input (EOF)"
    
    raise SyntaxError(error_message)


# Build Parser
def build_parser():
    return yacc.yacc()
