import ply.yacc as yacc
from Lexer import tokens
from Token import TokenType

parser = None 
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

# -----------------------------------------------------------------------------
# Production: <program> → birth <global_dec> <function_statements> <main_function> ghost
# -----------------------------------------------------------------------------
def p_program(p):
    """program : BIRTH unli_newline global_dec maybe_newline function_statements maybe_newline main_function unli_newline GHOST"""
    # p[3] = global_dec
    # p[5] = function_statements
    # p[7] = main_function
    p[0] = ASTNode("program", [p[3], p[5], p[7]])

def p_maybe_newline(p):
    """
    maybe_newline : empty
                  | NEWLINE maybe_newline
    """
    # If p[1] is None, do nothing. If p[1] == NEWLINE, we have a newline.
    # No AST node is strictly necessary for an optional newline.
    pass

def p_unli_newline(p):
    """
    unli_newline : NEWLINE
                 | NEWLINE unli_newline
    """
    # No AST node is strictly necessary for an optional newline.
    pass
# -----------------------------------------------------------------------------
# Production: <main_function> → FUNCTION_NAME LPAREN RPAREN LBRACE <statements> RBRACE
# -----------------------------------------------------------------------------
def p_main_function(p):
    """main_function : MAIN_CASPER LPAREN RPAREN maybe_newline LBRACE maybe_newline statements maybe_newline RBRACE"""
    p[0] = ASTNode("main_function", [p[7]], p[1])

# -----------------------------------------------------------------------------
# Production: <global_dec> → <global_statement> <global_tail> | null
# -----------------------------------------------------------------------------
def p_global_dec(p):
    """global_dec : global_statement unli_newline global_tail 
                  | empty"""
    if len(p) == 2:
        p[0] = ASTNode("global_dec", [])
    else:
        tail = p[3] if p[3] is not None else []
        p[0] = ASTNode("global_dec", [p[1]] + tail)

# -----------------------------------------------------------------------------
# Production: <global_tail> → <global_dec> 
# -----------------------------------------------------------------------------
def p_global_tail(p):
    """global_tail : global_dec"""
    p[0] = p[1].children if hasattr(p[1], 'children') else [p[1]]


# -----------------------------------------------------------------------------
# Production: <global_statement> → <data_type> IDENT<global_statement_tail>
# -----------------------------------------------------------------------------
def p_global_statement(p):
    """global_statement : data_type IDENT global_statement_tail """
    p[0] = ASTNode("global_statement", [p[1], ASTNode("IDENT", value=p[2]), p[3]])

# -----------------------------------------------------------------------------
# Production: <global_statement_tail> → null | , IDENT <global_statement_tail> | = <global_dec_value> <global_tail2>
# -----------------------------------------------------------------------------
def p_global_statement_tail(p):
    """global_statement_tail : empty
                             | COMMA IDENT global_statement_tail
                             | EQ global_dec_value global_tail2"""
    if len(p) == 2:
        p[0] = None
    elif p[1] == ',':
        p[0] = ASTNode("global_statement_tail", [ASTNode("IDENT", value=p[2]), p[3]])
    else:
        p[0] = ASTNode("global_statement_tail", [p[2], p[3]])

# -----------------------------------------------------------------------------
# Production: <global_tail2> → , IDENT <global_statement_tail> | null
# -----------------------------------------------------------------------------
def p_global_tail2(p):
    """global_tail2 : empty
                    | COMMA IDENT global_statement_tail"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("global_tail2", [ASTNode("IDENT", value=p[2]), p[3]])

# -----------------------------------------------------------------------------
# Production: <global_dec_value> → <global_value> | [ <list_element> ]
# -----------------------------------------------------------------------------
def p_global_dec_value(p):
    """global_dec_value : global_value 
                        | LBRACKET list_element RBRACKET"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode("global_dec_value_list", [p[2]])

# -----------------------------------------------------------------------------
# Production: <global_value> → <expression>
# -----------------------------------------------------------------------------
def p_global_value(p):
    """global_value : expression"""
    p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <var_statement> → <data_type> IDENT <var_tail>
# -----------------------------------------------------------------------------
def p_var_statement(p):
    """var_statement : data_type IDENT var_tail unli_newline"""
    p[0] = ASTNode("var_statement", [p[1], ASTNode("IDENT", value=p[2]), p[3]])

# -----------------------------------------------------------------------------
# Production: <var_tail> → null | = <tail_value> <var_tail2> | , IDENT <var_tail>
# -----------------------------------------------------------------------------
def p_var_tail(p):
    """var_tail : empty
                | EQ tail_value var_tail2
                | COMMA IDENT var_tail"""
    if len(p) == 2:
        p[0] = None
    elif p[1] == '=':
        p[0] = ASTNode("var_tail", [p[2], p[3]], "=")
    else:
        p[0] = ASTNode("var_tail", [ASTNode("IDENT", value=p[2]), p[3]], ",")

# -----------------------------------------------------------------------------
# Production: <var_tail2> → , IDENT <var_tail> | null
# -----------------------------------------------------------------------------
def p_var_tail2(p):
    """var_tail2 : empty
                 | COMMA IDENT var_tail"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("var_tail2", [ASTNode("IDENT", value=p[2]), p[3]])

# -----------------------------------------------------------------------------
# Production: <tail_value> → <value> | [ <list_element> ]
# -----------------------------------------------------------------------------
def p_tail_value(p):
    """tail_value : value
                  | LBRACKET list_element RBRACKET"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode("tail_value_list", [p[2]])

# -----------------------------------------------------------------------------
# Production: <list_element> → <literal> <element_tail>
# -----------------------------------------------------------------------------
def p_list_element(p):
    """list_element : literal element_tail"""
    if p[2] is None:
        p[0] = ASTNode("list_element", [p[1]])
    else:
        p[0] = ASTNode("list_element", [p[1], p[2]])

# -----------------------------------------------------------------------------
# Production: <element_tail> → , <list_element> | null
# -----------------------------------------------------------------------------
def p_element_tail(p):
    """element_tail : empty
                    | COMMA list_element"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("element_tail", [p[2]])

# -----------------------------------------------------------------------------
# Production: <index> → int_literal | IDENT
# -----------------------------------------------------------------------------
def p_index(p):
    """index : INT_LIT
             | IDENT"""
    p[0] = ASTNode("index", value=p[1])

# -----------------------------------------------------------------------------
# Production: <data_type> → int | flt | bln | chr | str
# -----------------------------------------------------------------------------
def p_data_type(p):
    """data_type : INT
                 | FLT
                 | BLN
                 | CHR
                 | STR"""
    p[0] = ASTNode("data_type", value=p[1])

# -----------------------------------------------------------------------------
# Production: <value> → <type_cast> | <expression> | <function_call>
# -----------------------------------------------------------------------------
def p_value(p):
    """value : type_cast
             | expression
             | function_call"""
    p[0] = ASTNode("value", [p[1]])

# -----------------------------------------------------------------------------
# Production: <type_cast> → to_int(<typecast_value>) | to_flt(<typecast_value>) | to_bln(<typecast_value>) | to_str(<typecast_value>)
# -----------------------------------------------------------------------------
def p_type_cast(p):
    """type_cast : CONVERT_TO_INT LPAREN typecast_value RPAREN
                 | CONVERT_TO_FLT LPAREN typecast_value RPAREN
                 | CONVERT_TO_BLN LPAREN typecast_value RPAREN
                 | CONVERT_TO_STR LPAREN typecast_value RPAREN"""
    p[0] = ASTNode("type_cast", [p[3]], p[1])

# -----------------------------------------------------------------------------
# Production: <typecast_value> → <expression> | FUNCTION_NAME() | <input_statement>
# -----------------------------------------------------------------------------
def p_typecast_value(p):
    """typecast_value :  expression
                      | FUNCTION_NAME LPAREN RPAREN
                      | input_statement"""
    if len(p) == 2:
        p[0] = ASTNode("typecast_value", value=p[1])
    else:
        p[0] = ASTNode("typecast_value", children=[ASTNode("FUNCTION_NAME", value=p[1]), p[2], p[3]])

# -----------------------------------------------------------------------------
# Production: <literal> → int_literal | float_literal | Day | Night | char_literal | str_literal
# -----------------------------------------------------------------------------
def p_literal(p):
    """literal : INT_LIT
               | FLT_LIT
               | DAY
               | NIGHT
               | CHR_LIT
               | STR_LIT"""
    p[0] = ASTNode("literal", value=p[1])

# -----------------------------------------------------------------------------
# Production: <expression> → <expr_head> <expr_tail>
# -----------------------------------------------------------------------------
def p_expression(p):
    "expression : factor factor_tail"
    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


# -----------------------------------------------------------------------------
# Production: <factor> → <var_call> | <literal> | ~<literal> | (<expression>)
# -----------------------------------------------------------------------------
def p_factor(p):
    """factor : var_call
              | literal
              | TILDE literal
              | LPAREN expression RPAREN"""
    if len(p) == 2:
        p[0] = ASTNode("factor", [p[1]])
    elif p[1] == '~':
        p[0] = ASTNode("factor", [p[2]], "~")
    else:
        p[0] = ASTNode("factor", [p[2]])

# -----------------------------------------------------------------------------
# Production: <factor_tail> → null | + <expression> | - <expression> | * <expression> | / <expression> | % <expression> | ** <expression>
# -----------------------------------------------------------------------------
def p_factor_tail(p):
    """factor_tail : empty
                   | PLUS expression
                   | MINUS expression
                   | MULTIPLY expression
                   | DIVISION expression
                   | MODULO expression
                   | EXPONENT expression
                   | GT expression
                   | LT expression
                   | EQ_EQ expression
                   | GT_EQ expression
                   | LT_EQ expression
                   | NOT_EQ expression
                   | AND expression
                   | OR expression"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("factor_tail", [p[1], p[2]])


# -----------------------------------------------------------------------------
# Production: <var_call> → IDENT <var_call_tail>
# -----------------------------------------------------------------------------
def p_var_call(p):
    "var_call : IDENT var_call_tail"
    p[0] = ASTNode("var_call", [p[2]], p[1])

# -----------------------------------------------------------------------------
# Production: <var_call_tail> → null | [ <index> ]
# -----------------------------------------------------------------------------
def p_var_call_tail(p):
    """var_call_tail : empty
                     | LBRACKET index RBRACKET"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("var_call_tail", [p[2]])


def p_function_statements(p):
    """function_statements : ret_type FUNCTION_NAME LPAREN parameters RPAREN LBRACE maybe_newline statements revive maybe_newline RBRACE unli_newline function_statements_tail
                           | empty"""
    if len(p) == 2:
      
        p[0] = []
    else:
        ret_type = ASTNode("ret_type", value=p[1])
        function_name = ASTNode("FUNCTION_NAME", value=p[2])
        parameters = p[4] if p[4] else ASTNode("parameters", [])
        statements = p[8] if p[8] else ASTNode("statements", [])
        revive_node = p[9] if p[9] else ASTNode("revive", [])

        function_node = ASTNode("function_declaration", [
            ret_type,
            function_name,
            parameters,
            statements,
            revive_node
        ])

   
        function_tail = p[13] if isinstance(p[13], list) else []
        p[0] = [function_node] + function_tail




def p_function_statements_tail(p):
    """function_statements_tail : function_statements
                                | empty"""
    if p[1] is None:
        
        p[0] = []
    else:

        if isinstance(p[1], list):
            p[0] = p[1]
        else:
            p[0] = [p[1]]






# -----------------------------------------------------------------------------
# Production: <ret_type> → function | <function_dtype>
# -----------------------------------------------------------------------------
def p_ret_type(p):
    """ret_type : FUNCTION
                | function_dtype"""
    if p[1] == "function":
        p[0] = ASTNode("ret_type", value="function")
    else:
        p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <function_dtype> → function_int | function_flt | function_chr | function_bln | function_str | function_list_int | function_list_flt | function_list_chr | function_list_str | function_list_bln
# -----------------------------------------------------------------------------
def p_function_dtype(p):
    """function_dtype : FUNCTION_INT
                      | FUNCTION_FLT
                      | FUNCTION_CHR
                      | FUNCTION_BLN
                      | FUNCTION_STR
                      | FUNCTION_LIST_INT
                      | FUNCTION_LIST_FLT
                      | FUNCTION_LIST_CHR
                      | FUNCTION_LIST_STR
                      | FUNCTION_LIST_BLN"""
    p[0] = ASTNode("function_dtype", value=p[1])

# -----------------------------------------------------------------------------
# Production: <parameters> → <data_type> IDENT<parameters_tail> | null
# -----------------------------------------------------------------------------
def p_parameters(p):
    """parameters : data_type IDENT parameters_tail
                  | empty"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("parameters", [p[1], ASTNode("IDENT", value=p[2]), p[3]])

# -----------------------------------------------------------------------------
# Production: <parameters_tail> → null | , <data_type> IDENT <parameters_tail>
# -----------------------------------------------------------------------------
def p_parameters_tail(p):
    """parameters_tail : empty
                       | COMMA data_type IDENT parameters_tail"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("parameters_tail", [p[2], ASTNode("IDENT", value=p[3]), p[4]])

# -----------------------------------------------------------------------------
# Production: <revive> → revive <value> | null
# -----------------------------------------------------------------------------
def p_revive(p):
    """revive : REVIVE value
              | empty"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("revive", [p[2]])

# -----------------------------------------------------------------------------
# Production: <statements> → null | <local_dec> <statements_tail>
# -----------------------------------------------------------------------------
def p_statements(p):
    """statements : empty
                  | local_dec maybe_newline statements_tail"""
    if len(p) == 2:
        # 'empty'
        p[0] = []     # Return an empty list instead of None
    else:
        # 'local_dec NEWLINE statements_tail'
        # p[1] is local_dec, p[2] is NEWLINE, p[3] is the remainder
        p[0] = [p[1]] + p[3]

# -----------------------------------------------------------------------------
# Production: <statements_tail> →  one of: <conditional_statement> | <switch_statement> | <loop_statement> | <function_call> | <string_operation_statement> | <output_statement> then <statements_tail2>
# -----------------------------------------------------------------------------
def p_statements_tail(p):
    """
    statements_tail : string_operation_statement unli_newline statements
                    | conditional_statement unli_newline statements
                    | switch_statement unli_newline statements
                    | loop_statement unli_newline statements
                    | function_call unli_newline statements
                    | output_statement unli_newline statements
                    | statements
    """
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = p[1]


# def p_statements_tail2(p):
#     """
#     statements_tail2 : statements
#     """
#     p[0] = p[1] 
# -----------------------------------------------------------------------------
# Production: <local_dec> → <var_statement>
# -----------------------------------------------------------------------------
def p_local_dec(p):
    """local_dec : empty
                 | var_statement"""
    p[0] = p[1] if p[1] is not None else ASTNode("local_dec", [])


#NEW CONDITIONALS

def p_conditional_statement(p):
    """
    conditional_statement : CHECK LPAREN condition RPAREN maybe_newline LBRACE maybe_newline statements RBRACE maybe_newline conditional_tail  OTHERWISE maybe_newline LBRACE maybe_newline statements RBRACE
    """
    p[0] = (
        "conditional_statement",
        p[3], 
        p[8],   
        p[11],  
        p[16],  
    )

def p_conditional_tail(p):
    """
    conditional_tail : OTHERWISE_CHECK LPAREN condition RPAREN maybe_newline LBRACE maybe_newline statements RBRACE  maybe_newline conditional_tail
                     | empty
    """
  
    if len(p) == 2:
        p[0] = None
    else:
         p[0] = (
            "conditional_tail",
            p[3], 
            p[8],   
            p[11],  
        )


def p_condition(p):
    "condition : condition_factor condition_factor_tail"
    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = ASTNode("condition", [p[1], p[2]])


# -----------------------------------------------------------------------------
# Production: <factor> → <var_call> | <literal> | ~<literal> | (<expression>)
# -----------------------------------------------------------------------------
def p_condition_factor(p):
    """condition_factor : var_call
              | condition_literal
              | TILDE condition_literal
              | LPAREN condition RPAREN"""
    if len(p) == 2:
        p[0] = ASTNode("condition_factor", [p[1]])
    elif p[1] == '~':
        p[0] = ASTNode("condition_factor", [p[2]], "~")
    else:
        p[0] = ASTNode("condition_factor", [p[2]])

# -----------------------------------------------------------------------------
# Production: <factor_tail> → null | + <expression> | - <expression> | * <expression> | / <expression> | % <expression> | ** <expression>
# -----------------------------------------------------------------------------
def p_condition_factor_tail(p):
    """condition_factor_tail : empty
                   | PLUS condition
                   | MINUS condition
                   | MULTIPLY condition
                   | DIVISION condition
                   | MODULO condition
                   | EXPONENT condition
                   | GT condition
                   | LT condition
                   | EQ_EQ condition
                   | GT_EQ condition
                   | LT_EQ condition
                   | NOT_EQ condition
                   | AND condition
                   | OR condition"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("condition_factor_tail", [p[1], p[2]])

def p_condition_literal(p):
    """condition_literal : INT_LIT
               | FLT_LIT
               | DAY
               | NIGHT
               | CHR_LIT
               | STR_LIT"""
    p[0] = ASTNode("condition_literal", value=p[1])



# -----------------------------------------------------------------------------
# Production: <switch_statement> → swap(IDENT){ <switch_condition> otherwise <statements> }
# -----------------------------------------------------------------------------
def p_switch_statement(p):
    "switch_statement : SWAP LPAREN IDENT RPAREN LBRACE maybe_newline switch_condition maybe_newline OTHERWISE maybe_newline  LBRACE maybe_newline statements maybe_newline RBRACE maybe_newline RBRACE"
    p[0] = ASTNode("switch_statement", [ASTNode("IDENT", value=p[3]), p[7], p[13]])

# -----------------------------------------------------------------------------
# Production: <switch_condition> → shift <value> : <statements> <switchcond_tail>
# -----------------------------------------------------------------------------
def p_switch_condition(p):
    "switch_condition : SHIFT value COLON maybe_newline statements switchcond_tail"
    p[0] = ASTNode("switch_condition", [p[2], p[5], p[6]])

# -----------------------------------------------------------------------------
# Production: <switchcond_tail> → <switch_condition> | null
# -----------------------------------------------------------------------------
def p_switchcond_tail(p):
    """switchcond_tail : empty
                       | switch_condition"""
    if p[1] is None:
        p[0] = None
    else:
        p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <loop_statement> → <for_loop> | <until_loop> | <repeat_until>
# -----------------------------------------------------------------------------
def p_loop_statement(p):
    """loop_statement : for_loop
                      | until_loop
                      | repeat_until"""
    p[0] = ASTNode("loop_statement", [p[1]])

# -----------------------------------------------------------------------------
# Production: <for_loop> → for ( <control_variable> ; <expression> ; <update> ) { <statements> }
# -----------------------------------------------------------------------------
def p_for_loop(p):
    "for_loop : FOR LPAREN control_variable SEMICOLON for_loop_condition SEMICOLON update RPAREN maybe_newline LBRACE maybe_newline statements RBRACE"
    p[0] = ASTNode("for_loop", [p[3], p[5], p[7], p[12]])

def p_for_loop_condition(p):
    "for_loop_condition : for_loop_condition_factor for_loop_condition_factor_tail"
    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = ASTNode("for_loop_condition", [p[1], p[2]])


# -----------------------------------------------------------------------------
# Production: <factor> → <var_call> | <literal> | ~<literal> | (<expression>)
# -----------------------------------------------------------------------------
def p_for_loop_condition_factor(p):
    """for_loop_condition_factor : var_call
              | for_loop_condition_literal
              | TILDE for_loop_condition_literal
              | LPAREN for_loop_condition RPAREN"""
    if len(p) == 2:
        p[0] = ASTNode("for_loop_condition_factor", [p[1]])
    elif p[1] == '~':
        p[0] = ASTNode("for_loop_condition_factor", [p[2]], "~")
    else:
        p[0] = ASTNode("for_loop_condition_factor", [p[2]])

# -----------------------------------------------------------------------------
# Production: <factor_tail> → null | + <expression> | - <expression> | * <expression> | / <expression> | % <expression> | ** <expression>
# -----------------------------------------------------------------------------
def p_for_loop_condition_factor_tail(p):
    """for_loop_condition_factor_tail : empty
                   | PLUS for_loop_condition
                   | MINUS for_loop_condition
                   | MULTIPLY for_loop_condition
                   | DIVISION for_loop_condition
                   | MODULO for_loop_condition
                   | EXPONENT for_loop_condition
                   | GT for_loop_condition
                   | LT for_loop_condition
                   | EQ_EQ for_loop_condition
                   | GT_EQ for_loop_condition
                   | LT_EQ for_loop_condition
                   | NOT_EQ for_loop_condition
                   | AND for_loop_condition
                   | OR for_loop_condition"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("for_loop_condition_factor_tail", [p[1], p[2]])

def p_for_loop_condition_literal(p):
    """for_loop_condition_literal : INT_LIT
               | FLT_LIT
               | DAY
               | NIGHT
               | CHR_LIT
               | STR_LIT"""
    p[0] = ASTNode("for_loop_condition_literal", value=p[1])


# -----------------------------------------------------------------------------
# Production: <until_loop> → until ( <expression> ) { <statements> }
# -----------------------------------------------------------------------------
def p_until_loop(p):
    "until_loop : UNTIL LPAREN until_loop_condition RPAREN LBRACE maybe_newline statements RBRACE"
    p[0] = ASTNode("until_loop", [p[3], p[7]])

# -----------------------------------------------------------------------------
# Production: <repeat_until> → repeat { <statements> } until ( <expression> )
# -----------------------------------------------------------------------------
def p_repeat_until(p):
    "repeat_until : REPEAT LBRACE maybe_newline statements RBRACE UNTIL LPAREN until_loop_condition RPAREN"
    p[0] = ASTNode("repeat_until", [p[3], p[7]])


def p_until_loop_condition(p):
    "until_loop_condition : until_loop_condition_factor until_loop_condition_factor_tail"
    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = ASTNode("until_for_loop_condition", [p[1], p[2]])


# -----------------------------------------------------------------------------
# Production: <factor> → <var_call> | <literal> | ~<literal> | (<expression>)
# -----------------------------------------------------------------------------
def p_until_loop_condition_factor(p):
    """until_loop_condition_factor : var_call
              | until_loop_condition_literal
              | TILDE until_loop_condition_literal
              | LPAREN until_loop_condition RPAREN"""
    if len(p) == 2:
        p[0] = ASTNode("until_loop_condition_factor", [p[1]])
    elif p[1] == '~':
        p[0] = ASTNode("until_loop_condition_factor", [p[2]], "~")
    else:
        p[0] = ASTNode("until_loop_condition_factor", [p[2]])

# -----------------------------------------------------------------------------
# Production: <factor_tail> → null | + <expression> | - <expression> | * <expression> | / <expression> | % <expression> | ** <expression>
# -----------------------------------------------------------------------------
def p_until_loop_condition_factor_tail(p):
    """until_loop_condition_factor_tail : empty
                   | PLUS until_loop_condition
                   | MINUS until_loop_condition
                   | MULTIPLY until_loop_condition
                   | DIVISION until_loop_condition
                   | MODULO until_loop_condition
                   | EXPONENT until_loop_condition
                   | GT until_loop_condition
                   | LT until_loop_condition
                   | EQ_EQ until_loop_condition
                   | GT_EQ until_loop_condition
                   | LT_EQ until_loop_condition
                   | NOT_EQ until_loop_condition
                   | AND until_loop_condition
                   | OR until_loop_condition"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("until_loop_condition_factor_tail", [p[1], p[2]])

def p_until_loop_condition_literal(p):
    """until_loop_condition_literal : INT_LIT
               | FLT_LIT
               | DAY
               | NIGHT
               | CHR_LIT
               | STR_LIT"""
    p[0] = ASTNode("until_loop_condition_literal", value=p[1])

# -----------------------------------------------------------------------------
# Production: <control_variable> → int IDENT = int_literal
# -----------------------------------------------------------------------------
def p_control_variable(p):
    "control_variable : INT IDENT EQ control_var_tail"
    p[0] = ASTNode("control_variable", [
        ASTNode("data_type", value=p[1]),
        ASTNode("IDENT", value=p[2]),
        p[4]
    ])

def p_control_var_tail(p):
    """control_var_tail : INT_LIT
                        | var_call"""
    if isinstance(p[1], int):
        p[0] = ASTNode("literal", value=p[1])
    else:
        p[0] = p[1]


# -----------------------------------------------------------------------------
# Production: <update> → <var_call> <update_tail>
# -----------------------------------------------------------------------------
def p_update(p):
    "update : var_call update_tail"
    p[0] = ASTNode("update", [p[1], p[2]])

# -----------------------------------------------------------------------------
# Production: <update_tail> → <postfix> | <assign_op> <value>
# -----------------------------------------------------------------------------
def p_update_tail(p):
    """update_tail : postfix
                   | assign_op value"""
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode("update_tail", [p[2]], p[1])

# -----------------------------------------------------------------------------
# Production: <postfix> → ++ | --
# -----------------------------------------------------------------------------
def p_postfix(p):
    """postfix : PLUS_PLUS
               | MINUS_MINUS"""
    p[0] = ASTNode("postfix", value=p[1])

# -----------------------------------------------------------------------------
# Production: <function_call> → FUNCTION_NAME ( <arguments> ) | <output_statement>
# -----------------------------------------------------------------------------
def p_function_call(p):
    """function_call : FUNCTION_NAME LPAREN arguments RPAREN
                     | output_statement"""
    if len(p) == 5:
        p[0] = ASTNode("function_call", [ASTNode("FUNCTION_NAME", value=p[1]), p[3]])
    else:
        p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <arguments> → null | <arg_value> <arg_tail>
# -----------------------------------------------------------------------------
def p_arguments(p):
    """arguments : empty
                 | arg_value arg_tail"""
    if p[1] is None:
        p[0] = None
    else:
        p[0] = ASTNode("arguments", [p[1], p[2]])

# -----------------------------------------------------------------------------
# Production: <arg_tail> → null | , <arg_value> <arg_tail>
# -----------------------------------------------------------------------------
def p_arg_tail(p):
    """arg_tail : empty
                | COMMA arg_value arg_tail"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("arg_tail", [p[2], p[3]])

# -----------------------------------------------------------------------------
# Production: <arg_value> → <literal> | <var_call>
# -----------------------------------------------------------------------------
def p_arg_value(p):
    """arg_value : literal
                 | var_call"""
    p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <output_statement> → display <value> <next_val>
# -----------------------------------------------------------------------------
def p_output_statement(p):
    """output_statement : DISPLAY value next_val
                        |  DISPLAY LPAREN value next_val RPAREN"""
    if len(p) == 4:  
        p[0] = ASTNode("output_statement", [p[2], p[3]])
    else:  
        p[0] = ASTNode("output_statement", [p[3], p[4]])



# -----------------------------------------------------------------------------
# Production: <next_val> → null | , <value> <next_val>
# -----------------------------------------------------------------------------
def p_next_val(p):
    """next_val : empty
                | COMMA value next_val"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("next_val", [p[2], p[3]])

# -----------------------------------------------------------------------------
# Production: <input_statement> → input()
# -----------------------------------------------------------------------------
def p_input_statement(p):
    "input_statement : INPUT LPAREN RPAREN"
    p[0] = ASTNode("input_statement")

# -----------------------------------------------------------------------------
# Production: <string_operation_statement> → <var_call> <string_operation_tail>
# -----------------------------------------------------------------------------
def p_string_operation_statement(p):
    "string_operation_statement : var_call string_operation_tail"
    # Wrap the left-hand side so that it's clearly marked as an assignment target.
    lhs = ASTNode("assignment_target", [p[1]])
    p[0] = ASTNode("string_operation_statement", [lhs, p[2]])

# -----------------------------------------------------------------------------
# Production: <string_operation_tail> → <assign_op> <value> | + <string_val> <stringcon_tail>
# -----------------------------------------------------------------------------
def p_string_operation_tail(p):
    """string_operation_tail : PLUS string_val stringcon_tail
                             | update_tail"""
    if p.slice[1].type == 'PLUS':
        p[0] = ASTNode("string_operation_tail", [p[2], p[3]], "+")
    else:
        p[0] = ASTNode("string_operation_tail", [p[1]], "update_tail")

# -----------------------------------------------------------------------------
# Production: <assign_op> → += | -= | *= | /= | %=
# -----------------------------------------------------------------------------
def p_assign_op(p):
    """assign_op : PLUS_EQ
                 | MINUS_EQ
                 | MUL_EQ
                 | DIV_EQ
                 | MOD_EQ
                 | EQ"""
    p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <stringcon_tail> → null | + <string_val> <stringcon_tail>
# -----------------------------------------------------------------------------
def p_stringcon_tail(p):
    """stringcon_tail : empty
                      | PLUS string_val stringcon_tail"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("stringcon_tail", [p[2], p[3]])

# -----------------------------------------------------------------------------
# Production: <string_val> → <var_call> | str_literal
# -----------------------------------------------------------------------------
def p_string_val(p):
    """string_val : var_call
                  | STR_LIT"""
    if isinstance(p[1], str):
        p[0] = ASTNode("string_val", value=p[1])
    else:
        p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <global_reference> → global <var_call>
# -----------------------------------------------------------------------------
# def p_global_reference(p):
#     "global_reference : GLOBAL var_call EQ value"
#     p[0] = ASTNode("global_reference", [p[2]])



def p_empty(p):
    """empty :"""
    p[0] = None



def p_error(p):
    global parser 
    token_display = {
        "EOF": "EOF",
        "ILLEGAL": "ILLEGAL",
        
        "IDENT": "identifier",
        "INT": "int",
        "INT_LIT": "integer literal",
        "FLT": "float",
        "FLT_LIT": "float literal",
        "BLN": "boolean",
        "BLN_LIT": "boolean literal",
        "STR": "string",
        "STR_LIT": "string literal",
        "CHR": "char",
        "CHR_LIT": "char literal",
        
        "FUNCTION": "function",
        "FUNCTION_INT": "function_int",
        "FUNCTION_STR": "function_str",
        "FUNCTION_BLN": "function_bln",
        "FUNCTION_FLT": "function_flt",
        "FUNCTION_CHR": "function_chr",
        "FUNCTION_LIST_INT": "function_list_int",
        "FUNCTION_LIST_STR": "function_list_str",
        "FUNCTION_LIST_BLN": "function_list_bln",
        "FUNCTION_LIST_FLT": "function_list_flt",
        "FUNCTION_LIST_CHR": "function_list_chr",
        "FUNCTION_LIST_INT2D": "function_list_int2D",
        "FUNCTION_LIST_STR2D": "function_list_str2D",
        "FUNCTION_LIST_BLN2D": "function_list_bln2D",
        "FUNCTION_LIST_FLT2D": "function_list_flt2D",
        "FUNCTION_LIST_CHR2D": "function_list_chr2D",
        
        "CONVERT_TO_INT": "to_int",
        "CONVERT_TO_STR": "to_str",
        "CONVERT_TO_BLN": "to_bln",
        "CONVERT_TO_FLT": "to_flt",
        
        "LIST_INT": "list_int",
        "LIST_STR": "list_str",
        "LIST_BLN": "list_bln",
        "LIST_FLT": "list_flt",
        "LIST_CHR": "list_chr",
        "LIST_INT2D": "list_int2D",
        "LIST_STR2D": "list_str2D",
        "LIST_BLN2D": "list_bln2D",
        "LIST_FLT2D": "list_flt2D",
        "LIST_CHR2D": "list_chr2D",
        
        "FUNCTION_NAME": "function_name",
        "MAIN_CASPER": "main_casper",
        
        # Arithmetic Symbols
        "PLUS": "+",
        "MINUS": "-",
        "MULTIPLY": "*",
        "EXPONENT": "**",   
        "MODULO": "%",
        "DIVISION": "/",
        "DOUBLE_SLASH": "//",
        "POW": "^",        
        
        # Prefix Symbols
        "TILDE": "~",
        "NOT": "!",
        
        # Postfix Symbols
        "PLUS_PLUS": "++",
        "MINUS_MINUS": "--",
        
        # Assignment Symbols
        "EQ": "=",
        "PLUS_EQ": "+=",
        "MINUS_EQ": "-=",
        "MUL_EQ": "*=",
        "DIV_EQ": "/=",
        "MOD_EQ": "%=",
        
        # Comparison Symbols
        "EQ_EQ": "==",
        "NOT_EQ": "!=",
        "LT": "<",
        "GT": ">",
        "LT_EQ": "<=",
        "GT_EQ": ">=",
        
        # Logical Symbols
        "AND": "&&",
        "OR": "||",
        
        # Comments
        "COMMENT": "comment",  
        "DOUBLE_LT": "<<",
        
        "COMMA": ",",
        
        # Keywords
        "BIRTH": "birth",
        "GHOST": "ghost",
        "INPUT": "input",
        "DISPLAY": "display",
        "CHECK": "check",
        "OTHERWISE": "otherwise",
        "OTHERWISE_CHECK": "otherwise_check",
        "FOR": "for",
        "REPEAT": "repeat",
        "UNTIL": "until",
        "STOP": "stop",
        "SKIP": "skip",
        "SWAP": "swap",
        "SHIFT": "shift",
        "REVIVE": "revive",
        "DAY": "Day",
        "NIGHT": "Night",
        "MEASURE": "measure",
        "IN": "in",
        "CARRIAGE_RETURN": "NEWLINE",
        "NEWLINE": "NEWLINE",
        "SEMICOLON": ";",
        "COLON": ":",
        

        "TYPE": "type",
        "LPAREN": "(",
        "RPAREN": ")",
        "LBRACE": "{",
        "RBRACE": "}",
        "LBRACKET": "[",
        "RBRACKET": "]",
    }
    
    if p:
        state = parser.statestack[-1] if parser and parser.statestack else None
        expected_tokens = list(parser.action[state].keys()) if state in parser.action else []
        expected_tokens_disp = [token_display.get(tok, tok) for tok in expected_tokens]
        expected_tokens_str = ", ".join(expected_tokens_disp)
        
        error_message = (
            f"Syntax Error:\n"
            f"Unexpected token: '{p.value}' at line {p.lineno}.\n"
        )
        if expected_tokens:
            error_message += f"Expected one of: {expected_tokens_str}"
    else:
        error_message = "Syntax Error:\nUnexpected end of input (EOF)."
    
    raise SyntaxError(error_message)



# Build Parser
def build_parser():
    global parser
    parser = yacc.yacc()
    return parser
