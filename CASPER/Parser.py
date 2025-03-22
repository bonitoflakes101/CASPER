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


def p_main_function(p):
    """main_function : MAIN_CASPER LPAREN RPAREN maybe_newline LBRACE maybe_newline statements maybe_newline RBRACE"""
    p[0] = ASTNode("main_function", [p[7]], p[1])
# -----------------------------------------------------------------------------
# GLOBAL DECLARATIONS
# CFG:
#   <global_dec> → <global_statement> <global_tail>
#   <global_dec> → null
#   <global_tail> → <global_dec>
# -----------------------------------------------------------------------------

def p_global_dec(p):
    """
    global_dec : global_statement unli_newline global_tail     
               | empty                            
    """
    if len(p) == 4 and p[1] is not None:  
        # 'global_statement unli_newline global_tail'
        p[0] = [p[1]] + p[3]  
    else:
        p[0] = []


# =============================================================================
# (4) <global_tail> → <global_dec>
# =============================================================================
def p_global_tail(p):
    """
        global_tail : global_dec
    """
    p[0] = p[1]


# =============================================================================
# (5) <global_statement> → <var_statement> <global_statement_tail>
# =============================================================================
def p_global_statement(p):
    """
        global_statement : var_statement global_statement_tail
    """
    var_children = p[1].children.copy()
    assign_expr = None
    if p[2]:
        for tail_item in p[2]:
            if hasattr(tail_item, "children") and tail_item.children:
                if tail_item.children[0].value == "=":
                    assign_expr = tail_item.children[1]
                    break
    if assign_expr is not None:
        if len(var_children) >= 3:
            var_children[2] = assign_expr
        else:
            var_children.append(assign_expr)
    p[0] = ASTNode("global_statement", children=var_children)


# =============================================================================
# (6) <var_statement> → <data_type> IDENTIFIER <list_dec>
# =============================================================================
def p_var_statement(p):
    """
        var_statement : data_type IDENT list_dec
    """
    p[0] = ASTNode("var_statement", [
        p[1],
        ASTNode("IDENT", value=p[2]),
        p[3]
    ])


# =============================================================================
# (7) <list_dec> → null
# (8) <list_dec> → [] <2d_list>
# =============================================================================
def p_list_dec(p):
    """
    list_dec : empty               
             | LBRACKET RBRACKET _2d_list 
    """
    if len(p) == 2:  
        p[0] = None
    else:
        # LBRACKET RBRACKET _2d_list
        p[0] = ASTNode("list_dec", [p[3]])


# =============================================================================
# (9) <2d_list> → null
# (10) <2d_list> → []
# =============================================================================
def p_2d_list(p):
    """
    _2d_list : empty            
             | LBRACKET RBRACKET 
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("2d_list", value="2d")


# =============================================================================
# (11) <global_statement_tail> → null
# (12) <global_statement_tail> → , IDENTIFIER <global_statement_tail>
# (13) <global_statement_tail> → = <global_value> <global_statement_tail2>
# =============================================================================
def p_global_statement_tail(p):
    """
    global_statement_tail : empty                        
                          | COMMA IDENT global_statement_tail 
                          | EQ global_value global_statement_tail2 
    """
    if len(p) == 2:
        p[0] = []
    elif p[1] == ',':
        node = ASTNode("global_statement_tail_item", children=[ASTNode("IDENT", value=p[2])])
        p[0] = [node] + p[3]
    else:
        node = ASTNode("global_statement_tail_item", children=[ASTNode("assign_op", value="="), p[2]])
        p[0] = [node] + p[3]

# =============================================================================
# (14) <global_statement_tail2> → , IDENTIFIER <global_statement_tail>
# (15) <global_statement_tail2> → null
# =============================================================================
def p_global_statement_tail2(p):
    """
    global_statement_tail2 : COMMA IDENT global_statement_tail 
                           | empty                           
    """
    if len(p) == 2:
        p[0] = []
    else:
        node = ASTNode("global_statement_tail_item", children=[ASTNode("IDENT", value=p[2])])
        p[0] = [node] + p[3]


# =============================================================================
# (16) <global_value> → <expression>
# (17) <global_value> → <list_value>
# =============================================================================
def p_global_value(p):
    """
    global_value : expression   
                 | list_value   
    """
    p[0] = p[1]


# =============================================================================
# (18) <list_value> → [ <list_element> ]
# =============================================================================
def p_list_value(p):
    """
     list_value : LBRACKET list_element RBRACKET
    """
    p[0] = ASTNode("list_value", [p[2]])


# =============================================================================
# (19) <list_element> → <literal> <element_tail>
# (20) <element_tail> → , <list_element>
# (21) <element_tail> → null
# =============================================================================
def p_list_element(p):
    """
    list_element : literal element_tail  
    """
    if p[2]:
        p[0] = ASTNode("list_element", [p[1], p[2]])
    else:
        p[0] = ASTNode("list_element", [p[1]])

def p_element_tail(p):
    """
    element_tail : COMMA list_element  
                 | empty              
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = p[2]


# =============================================================================
# (22) <data_type> → int
# (23) <data_type> → flt
# (24) <data_type> → bln
# (25) <data_type> → chr
# (26) <data_type> → str
# =============================================================================
def p_data_type(p):
    """
    data_type : INT   
              | FLT   
              | BLN  
              | CHR  
              | STR  
    """
    p[0] = ASTNode("data_type", value=p[1].lower())


# =============================================================================
# (27) <expression> → <factor> <factor_tail>
# =============================================================================
def p_expression(p):
    """
    expression : factor factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


# =============================================================================
# (28) <factor> → <var_call> <postfix>
# (29) <factor> → <literal1>
# (30) <factor> → ~ <int_literal>
# (31) <factor> → ~ <flt_literal>
# (32) <factor> → ( <expression> )
# =============================================================================
def p_factor(p):
    """
    factor : var_call postfix           
           | literal1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN factor_expression RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("factor_var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("factor_neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("factor_neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("factor_paren", [p[2]])



def p_factor_expression(p):
    """
    factor_expression : factor_expression_factor factor_expression_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_factor_expression_factor(p):
    """
    factor_expression_factor : var_call postfix           
           | factor_expression1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN factor_expression RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_factor_expression_tail(p):
    """
    factor_expression_tail : PLUS factor_expression_factor factor_expression_tail
                | MINUS factor_expression_factor factor_expression_tail
                | MULTIPLY factor_expression_factor factor_expression_tail
                | DIVISION factor_expression_factor factor_expression_tail
                | MODULO factor_expression_factor factor_expression_tail
                | EXPONENT factor_expression_factor factor_expression_tail
                | GT factor_expression_factor factor_expression_tail
                | LT factor_expression_factor factor_expression_tail
                | EQ_EQ factor_expression_factor factor_expression_tail
                | GT_EQ factor_expression_factor factor_expression_tail
                | LT_EQ factor_expression_factor factor_expression_tail
                | NOT_EQ factor_expression_factor factor_expression_tail
                | AND factor_expression_factor factor_expression_tail
                | OR factor_expression_factor factor_expression_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("factor_tail_binop", [p[1], p[2], p[3]])

def p_factor_expression1 (p):
    """
    factor_expression1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT
    """
    p[0] = p[1]  


# =============================================================================
# (33) <factor_tail> → + <factor> <factor_tail>
# (34) <factor_tail> → - <factor> <factor_tail>
# (35) <factor_tail> → * <factor> <factor_tail>
# (36) <factor_tail> → / <factor> <factor_tail>
# (37) <factor_tail> → % <factor> <factor_tail>
# (38) <factor_tail> → ** <factor> <factor_tail>
# (39) <factor_tail> → > <factor> <factor_tail>
# (40) <factor_tail> → < <factor> <factor_tail>
# (41) <factor_tail> → == <factor> <factor_tail>
# (42) <factor_tail> → >= <factor> <factor_tail>
# (43) <factor_tail> → <= <factor> <factor_tail>
# (44) <factor_tail> → != <factor> <factor_tail>
# (45) <factor_tail> → && <factor> <factor_tail>
# (46) <factor_tail> → || <factor> <factor_tail>
# (47) <factor_tail> → null
# =============================================================================
def p_factor_tail(p):
    """
    factor_tail : PLUS factor factor_tail
                | MINUS factor factor_tail
                | MULTIPLY factor factor_tail
                | DIVISION factor factor_tail
                | MODULO factor factor_tail
                | EXPONENT factor factor_tail
                | GT factor factor_tail
                | LT factor factor_tail
                | EQ_EQ factor factor_tail
                | GT_EQ factor factor_tail
                | LT_EQ factor factor_tail
                | NOT_EQ factor factor_tail
                | AND factor factor_tail
                | OR factor factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("factor_tail_binop", [p[1], p[2], p[3]])


# =============================================================================
# (48) <literal> → <literal1> | <literal2>
# =============================================================================
def p_literal(p):
    """
    literal : literal1
            | literal2
    """
    p[0] = ASTNode("literal", value=p[1])


# =============================================================================
# (49) <literal1> → int_literal
# (50) <literal1> → float_literal
# (51) <literal1> → Day
# (52) <literal1> → Night
# (53) <literal1> → str_literal
# (54) <literal2> → char_literal
# =============================================================================
def p_literal1(p):
    """
    literal1 : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT
    """
    p[0] = p[1]  # store the actual value

def p_literal2(p):
    """
    literal2 : CHR_LIT
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (55) <function_statements> → <ret_type> FUNCTION_NAME ( <parameters> ) { <statements> <revive> } <function_statements_tail>
# (56) <function_statements> → null
# -----------------------------------------------------------------------------

def p_function_statements(p):
    """
    function_statements : ret_type FUNCTION_NAME LPAREN parameters RPAREN LBRACE maybe_newline statements revive maybe_newline RBRACE unli_newline function_statements_tail  
                        | empty                                                          
    """
    if len(p) == 2:
        p[0] = []
    else:
        # Wrap return type into an ASTNode
        if isinstance(p[1], tuple) and p[1][0] == "ret_type_void":
            ret_node = ASTNode("ret_type", value="void")
        elif isinstance(p[1], tuple) and p[1][0] == "ret_type":
            ret_node = ASTNode("ret_type", value=p[1][1])
        else:
            ret_node = p[1]

        func_decl = ASTNode(
            "function_declaration",
            children=[
                ret_node,                              # ret_type
                ASTNode("FUNCTION_NAME", value=p[2]),  # function name
                p[4],                                   # parameters
                p[7],                                   # statements
                p[8],                                   # revive
            ]
        )
        p[0] = [func_decl] + p[13]



# -----------------------------------------------------------------------------
# (57) <function_statements_tail> → <function_statements>
# (58) <function_statements_tail> → null
# -----------------------------------------------------------------------------
def p_function_statements_tail(p):
    """
    function_statements_tail : function_statements 
                             | empty               
    """
    if len(p) == 2 and p[1] is not None:
        p[0] = p[1]
    else:
        p[0] = []

# -----------------------------------------------------------------------------
# (59) <ret_type> → function
# (60) <ret_type> → <function_dtype>
# -----------------------------------------------------------------------------
def p_ret_type(p):
    """
    ret_type : FUNCTION           
             | function_dtype    
    """
    if p[1] == 'function':
        p[0] = ("ret_type_void",)  # or store a node
    else:
        p[0] = ("ret_type", p[1])

# -----------------------------------------------------------------------------
# (61) <function_dtype> → function_int
# (62) <function_dtype> → function_flt
# (63) <function_dtype> → function_chr
# (64) <function_dtype> → function_bln
# (65) <function_dtype> → function_str
# (66) <function_dtype> → function_list_int
# (67) <function_dtype> → function_list_flt
# (68) <function_dtype> → function_list_chr
# (69) <function_dtype> → function_list_str
# (70) <function_dtype> → function_list_bln
# -----------------------------------------------------------------------------
def p_function_dtype(p):
    """
    function_dtype : FUNCTION_INT       
                   | FUNCTION_FLT      
                   | FUNCTION_CHR       
                   | FUNCTION_BLN       
                   | FUNCTION_STR       
                   | FUNCTION_LIST_INT 
                   | FUNCTION_LIST_FLT  
                   | FUNCTION_LIST_CHR 
                   | FUNCTION_LIST_STR  
                   | FUNCTION_LIST_BLN  
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (71) <parameters> → <data_type> IDENTIFIER <parameters_tail>
# (72) <parameters> → null
# -----------------------------------------------------------------------------
def p_parameters(p):
    """
    parameters : data_type IDENT parameters_tail  
               | empty                            
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [ASTNode("param_decl", children=[p[1], ASTNode("IDENT", value=p[2])])] + p[3]

# -----------------------------------------------------------------------------
# (73) <parameters_tail> → , <data_type> IDENTIFIER <parameters_tail>
# (74) <parameters_tail> → null
# -----------------------------------------------------------------------------
def p_parameters_tail(p):
    """
    parameters_tail : COMMA data_type IDENT parameters_tail 
                    | empty                                 
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [ASTNode("param_decl", children=[p[2], ASTNode("IDENT", value=p[3])])] + (p[4] if p[4] is not None else [])
# -----------------------------------------------------------------------------
# (75) <revive> → revive <value>
# (76) <revive> → null
# -----------------------------------------------------------------------------
def p_revive(p):
    """
    revive : REVIVE revive_value  
           | empty        
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("revive_statement", children=[p[2]])

def p_revive_value(p):
    """revive_value : revive_type_cast
             | revive_expression
             | function_call"""
    p[0] = ASTNode("value", [p[1]])


def p_revive_expression(p):
    """
    revive_expression : revive_factor revive_factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_revive_factor(p):
    """
    revive_factor : var_call postfix           
           | revive_factor1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN revive_factor RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_revive_factor_tail(p):
    """
    revive_factor_tail : PLUS revive_factor revive_factor_tail
                | MINUS revive_factor revive_factor_tail
                | MULTIPLY revive_factor revive_factor_tail
                | DIVISION revive_factor revive_factor_tail
                | MODULO revive_factor revive_factor_tail
                | EXPONENT revive_factor revive_factor_tail
                | GT revive_factor revive_factor_tail
                | LT revive_factor revive_factor_tail
                | EQ_EQ revive_factor revive_factor_tail
                | GT_EQ revive_factor revive_factor_tail
                | LT_EQ revive_factor revive_factor_tail
                | NOT_EQ revive_factor revive_factor_tail
                | AND revive_factor revive_factor_tail
                | OR revive_factor revive_factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("factor_tail_binop", [p[1], p[2], p[3]])

def p_revive_factor1 (p):
    """
    revive_factor1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT
    """
    p[0] = p[1]  

def p_revive_type_cast(p):
    """revive_type_cast : CONVERT_TO_INT LPAREN typecast_value RPAREN
                 | CONVERT_TO_FLT LPAREN typecast_value RPAREN
                 | CONVERT_TO_BLN LPAREN typecast_value RPAREN
                 | CONVERT_TO_STR LPAREN typecast_value RPAREN"""
    p[0] = ASTNode("type_cast", [p[3]], p[1])
# -----------------------------------------------------------------------------
# (77) <statements> → <local_dec> <statements_tail>
# -----------------------------------------------------------------------------

def p_statements(p):
    """statements : empty
                  | local_dec unli_newline statements_tail"""


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
    statements_tail : switch_statement unli_newline statements
                    | loop_statement unli_newline statements
                    | function_call unli_newline statements
                    | assignment_statement unli_newline statements
                    | output_statement unli_newline statements
                    | conditional_statement unli_newline statements
                    | statements
    """
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = p[1]
            
# -----------------------------------------------------------------------------
# (78) <statements_tail> → <statements_list>
# -----------------------------------------------------------------------------
# def p_statements_tail_list(p):
#     """
#     statements_tail : statements_list  
#     """
#     p[0] = p[1]

# -----------------------------------------------------------------------------
# (79) <statements_list> → <conditional_statement> <statements_list2>
# (80) <statements_list> → <switch_statement> <statements_list2>
# (81) <statements_list> → <loop_statement> <statements_list2>
# (82) <statements_list> → <function_call> <statements_list2>
# (83) <statements_list> → <assignment_statement> <statements_list2>
# (84) <statements_list> → <output_statement> <statements_list2>
# (85) <statements_list> → null
# -----------------------------------------------------------------------------
# def p_statements_list(p):
#     """
#     statements_list :   
#                      switch_statement unli_newline statements_list2       
#                     | loop_statement unli_newline statements_list2        
#                     | function_call unli_newline statements_list2          
#                     | assignment_statement unli_newline statements_list2    
#                     | output_statement unli_newline statements_list2    
#                     | conditional_statement unli_newline statements_list2    
#                     | empty                                   
#     """
#     if len(p) == 2:
#         # empty => null
#         p[0] = []
#     else:
#         # e.g. conditional_statement statements_list2
#         p[0] = [p[1]] + p[3]

# -----------------------------------------------------------------------------
# (86) <statements_list2> → <statements>
# -----------------------------------------------------------------------------
# def p_statements_list2(p):
#     """
#     statements_list2 : statements 
#     """
#     p[0] = [p[1]] if p[1] is not None else []

# -----------------------------------------------------------------------------
# (87) <local_dec> → <var_statement> <local_dec_tail>
# (88) <local_dec> → null
# -----------------------------------------------------------------------------
def p_local_dec(p):
    """
    local_dec : local_var_statement local_dec_tail
              | empty
    """
    if len(p) == 2:
        # empty
        p[0] = []
    else:
        var_node = p[1]             
        tail_nodes = p[2]         
        if isinstance(tail_nodes, list):
            var_node.children.extend(tail_nodes)
        p[0] = [var_node]

def p_local_var_statement(p):
    """
        local_var_statement : local_data_type IDENT local_list_dec
    """
    p[0] = ASTNode("var_statement", [
        p[1],
        ASTNode("IDENT", value=p[2]),
        p[3]
    ])

def p_local_data_type(p):
    """
    local_data_type : INT   
              | FLT   
              | BLN  
              | CHR  
              | STR  
    """
    p[0] = ASTNode("local_data_type", value=p[1].lower())

def p_local_list_dec(p):
    """
    local_list_dec : empty               
             | LBRACKET RBRACKET local_2d_list 
    """
    if len(p) == 2:  
        p[0] = None
    else:
        # LBRACKET RBRACKET _2d_list
        p[0] = ASTNode("list_dec", [p[3]])


def p_local_2d_list(p):
    """
    local_2d_list : empty            
             | LBRACKET RBRACKET 
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("2d_list", value="2d")


# -----------------------------------------------------------------------------
# (89) <local_dec_tail> → null
# (90) <local_dec_tail> → , IDENTIFIER <local_dec_tail>
# (91) <local_dec_tail> → = <local_value> <local_dec_tail2>
# -----------------------------------------------------------------------------
def p_local_dec_tail(p):
    """
    local_dec_tail : empty                          
                   | COMMA IDENT local_dec_tail     
                   | EQ local_value local_dec_tail2  
    """
    if len(p) == 2:
        p[0] = []
    elif p[1] == ',':
        p[0] = [ASTNode("local_var_more", children=[ASTNode("IDENT", value=p[2])])] + p[3]
    else:
        p[0] = [ASTNode("local_var_assign", children=[p[2]])] + p[3]

# -----------------------------------------------------------------------------
# (92) <local_dec_tail2> → , IDENTIFIER <local_dec_tail>
# (93) <local_dec_tail2> → null
# -----------------------------------------------------------------------------
def p_local_dec_tail2(p):
    """
    local_dec_tail2 : COMMA IDENT local_dec_tail  
                    | empty                      
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [ASTNode("local_var_more", children=[ASTNode("IDENT", value=p[2])])] + p[3]


# -----------------------------------------------------------------------------
# (94) <local_value> → <value>
# (95) <local_value> → <list_value>
# -----------------------------------------------------------------------------
def p_local_value(p):
    """
    local_value : local_value_value      
                | list_value  
    """
    p[0] = p[1]

def p_local_value_value(p):
    """local_value_value  : local_type_cast
             | local_expression
             | function_call"""
    p[0] = ASTNode("value", [p[1]])
    
def p_local_expression(p):
    """
    local_expression : local_factor local_factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_local_factor(p):
    """
    local_factor : var_call postfix           
           | local_factor1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN local_factor RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_local_factor_tail(p):
    """
    local_factor_tail : PLUS local_factor local_factor_tail
                | MINUS local_factor local_factor_tail
                | MULTIPLY local_factor local_factor_tail
                | DIVISION local_factor local_factor_tail
                | MODULO local_factor local_factor_tail
                | EXPONENT local_factor local_factor_tail
                | GT local_factor local_factor_tail
                | LT local_factor local_factor_tail
                | EQ_EQ local_factor local_factor_tail
                | GT_EQ local_factor local_factor_tail
                | LT_EQ local_factor local_factor_tail
                | NOT_EQ local_factor local_factor_tail
                | AND local_factor local_factor_tail
                | OR local_factor local_factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("local_factor_tail_binop", [p[1], p[2], p[3]])

def p_local_factor1 (p):
    """
    local_factor1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT
    """
    p[0] = p[1]  

def p_local_type_cast(p):
    """local_type_cast : CONVERT_TO_INT LPAREN typecast_value RPAREN
                 | CONVERT_TO_FLT LPAREN typecast_value RPAREN
                 | CONVERT_TO_BLN LPAREN typecast_value RPAREN
                 | CONVERT_TO_STR LPAREN typecast_value RPAREN"""
    p[0] = ASTNode("type_cast", [p[3]], p[1])
# -----------------------------------------------------------------------------
# (96) <conditional_statement> → check(<expression>){<statements>} <conditional_tail> otherwise {<statements>}
# -----------------------------------------------------------------------------
def p_conditional_statement(p):
    """
    conditional_statement : CHECK LPAREN condition RPAREN LBRACE maybe_newline statements maybe_newline RBRACE  maybe_newline conditional_tail  maybe_newline OTHERWISE  maybe_newline LBRACE  maybe_newline statements  maybe_newline RBRACE  
    """
    p[0] = ASTNode("conditional_statement", children=[p[3], p[7], p[11], p[16]])


# -----------------------------------------------------------------------------
# (97) <conditional_tail> → otherwise_check(<expression>){<statements>} <conditional_tail>
# (98) <conditional_tail> → null
# -----------------------------------------------------------------------------
def p_conditional_tail(p):
    """
    conditional_tail : OTHERWISE_CHECK LPAREN condition RPAREN LBRACE statements RBRACE conditional_tail 
                     | empty                                            
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [ASTNode("otherwise_check", children=[p[3], p[6]])] + p[8]


def p_condition(p):
    """
    condition : condition_factor condition_tail
    """
    if p[2] is None:
        p[0] = ASTNode("condition", [p[1]])
    else:
        p[0] = ASTNode("condition", [p[1], p[2]])


def p_condition_factor(p):
    """
    condition_factor : var_call postfix           
           | condition1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN condition RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_condition_tail(p):
    """
    condition_tail : PLUS condition_factor condition_tail
                | MINUS condition_factor condition_tail
                | MULTIPLY condition_factor condition_tail
                | DIVISION condition_factor condition_tail
                | MODULO condition_factor condition_tail
                | EXPONENT condition_factor condition_tail
                | GT condition_factor condition_tail
                | LT condition_factor condition_tail
                | EQ_EQ condition_factor condition_tail
                | GT_EQ condition_factor condition_tail
                | LT_EQ condition_factor condition_tail
                | NOT_EQ condition_factor condition_tail
                | AND condition_factor condition_tail
                | OR condition_factor condition_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("factor_tail_binop", [p[1], p[2], p[3]])

def p_condition1(p):
    """
    condition1 : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT
    """
    p[0] = p[1]  




# -----------------------------------------------------------------------------
# (99) <switch_statement> → swap(IDENTIFIER){<switch_condition> otherwise <statements>}
# -----------------------------------------------------------------------------
def p_switch_statement(p):
    """
    switch_statement : SWAP LPAREN IDENT RPAREN LBRACE switch_condition OTHERWISE LBRACE statements RBRACE RBRACE 
    """
    p[0] = ASTNode("switch_statement", children=[
        ASTNode("IDENT", value=p[3]),
        p[6],
        p[9]
    ])

# -----------------------------------------------------------------------------
# (100) <switch_condition> → shift <value> : <statements> <switchcond_tail>
# -----------------------------------------------------------------------------
def p_switch_condition(p):
    """
    switch_condition : SHIFT switch_value COLON statements switchcond_tail  
    """
    p[0] = ASTNode("switch_condition", children=[p[2], p[4], p[5]])

def p_switch_value(p):
    """switch_value  : switch_type_cast
             | switch_expression
             | function_call"""
    p[0] = ASTNode("value", [p[1]])

def p_switch_expression(p):
    """
    switch_expression : switch_factor switch_factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_switch_factor(p):
    """
    switch_factor : var_call postfix           
           | switch_factor1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN switch_factor RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("factor_var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("factor_neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("factor_neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("factor_paren", [p[2]])


def p_switch_factor_tail(p):
    """
    switch_factor_tail : PLUS switch_factor switch_factor_tail
                | MINUS switch_factor switch_factor_tail
                | MULTIPLY switch_factor switch_factor_tail
                | DIVISION switch_factor switch_factor_tail
                | MODULO switch_factor switch_factor_tail
                | EXPONENT switch_factor switch_factor_tail
                | GT switch_factor switch_factor_tail
                | LT switch_factor switch_factor_tail
                | EQ_EQ switch_factor switch_factor_tail
                | GT_EQ switch_factor switch_factor_tail
                | LT_EQ switch_factor switch_factor_tail
                | NOT_EQ switch_factor switch_factor_tail
                | AND switch_factor switch_factor_tail
                | OR switch_factor switch_factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("factor_tail_binop", [p[1], p[2], p[3]])

def p_switch_factor1 (p):
    """
    switch_factor1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT  
    """
    p[0] = p[1]  

def p_switch_type_cast(p):
    """switch_type_cast : CONVERT_TO_INT LPAREN typecast_value RPAREN
                 | CONVERT_TO_FLT LPAREN typecast_value RPAREN
                 | CONVERT_TO_BLN LPAREN typecast_value RPAREN
                 | CONVERT_TO_STR LPAREN typecast_value RPAREN"""
    p[0] = ASTNode("local_type_cast", [p[3]], p[1])
# -----------------------------------------------------------------------------
# (101) <switchcond_tail> → <switch_condition>
# (102) <switchcond_tail> → null
# -----------------------------------------------------------------------------
def p_switchcond_tail(p):
    """
    switchcond_tail : switch_condition  
                    | empty          
    """
    if len(p) == 2:
        if p[1] is None:
            p[0] = []
        else:
            p[0] = [p[1]]

# -----------------------------------------------------------------------------
# (103) <loop_statement> → <for_loop>
# (104) <loop_statement> → <until_loop>
# (105) <loop_statement> → <repeat_until>
# -----------------------------------------------------------------------------
def p_loop_statement(p):
    """
    loop_statement : for_loop    
                   | until_loop  
                   | repeat_until
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (106) <for_loop> → for ( <control_variable> ; <expression> ; <update> ) { <statements> }
# -----------------------------------------------------------------------------
def p_for_loop(p):
    """for_loop : FOR LPAREN control_variable SEMICOLON for_expression SEMICOLON update RPAREN LBRACE maybe_newline statements maybe_newline RBRACE"""
    p[0] = ASTNode("for_loop", children=[p[3], p[5], p[7], p[11]])

def p_for_expression(p):
    """
    for_expression : for_factor for_factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_for_factor(p):
    """
    for_factor : var_call postfix           
           | for_factor1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN for_factor RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_for_factor_tail(p):
    """
    for_factor_tail : PLUS for_factor for_factor_tail
                | MINUS for_factor for_factor_tail
                | MULTIPLY for_factor for_factor_tail
                | DIVISION for_factor for_factor_tail
                | MODULO for_factor for_factor_tail
                | EXPONENT for_factor for_factor_tail
                | GT for_factor for_factor_tail
                | LT for_factor for_factor_tail
                | EQ_EQ for_factor for_factor_tail
                | GT_EQ for_factor for_factor_tail
                | LT_EQ for_factor for_factor_tail
                | NOT_EQ for_factor for_factor_tail
                | AND for_factor for_factor_tail
                | OR for_factor for_factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("for_factor_tail_binop", [p[1], p[2], p[3]])

def p_for_factor1 (p):
    """
    for_factor1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT  
    """
    p[0] = p[1]  
# -----------------------------------------------------------------------------
# (107) <until_loop> → until ( <expression> ) { <statements> }
# -----------------------------------------------------------------------------
def p_until_loop(p):
    """
    until_loop : UNTIL LPAREN until_expression RPAREN LBRACE statements RBRACE  
    """
    p[0] = ASTNode("until_loop", children=[p[3], p[6]])


def p_until_expression(p):
    """
    until_expression : until_factor until_factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_until_factor(p):
    """
    until_factor : var_call postfix           
           | until_factor1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN until_factor RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_until_factor_tail(p):
    """
    until_factor_tail : PLUS until_factor until_factor_tail
                | MINUS until_factor until_factor_tail
                | MULTIPLY until_factor until_factor_tail
                | DIVISION until_factor until_factor_tail
                | MODULO until_factor until_factor_tail
                | EXPONENT until_factor until_factor_tail
                | GT until_factor until_factor_tail
                | LT until_factor until_factor_tail
                | EQ_EQ until_factor until_factor_tail
                | GT_EQ until_factor until_factor_tail
                | LT_EQ until_factor until_factor_tail
                | NOT_EQ until_factor until_factor_tail
                | AND until_factor until_factor_tail
                | OR until_factor until_factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("for_factor_tail_binop", [p[1], p[2], p[3]])

def p_until_factor1 (p):
    """
    until_factor1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT  
    """
    p[0] = p[1]  
# -----------------------------------------------------------------------------
# (108) <repeat_until> → repeat { <statements> } until(<expression>)
# -----------------------------------------------------------------------------
def p_repeat_until(p):
    """
    repeat_until : REPEAT LBRACE statements RBRACE UNTIL LPAREN until_expression RPAREN 
    """
    p[0] = ASTNode("repeat_until", children=[p[3], p[7]])

# -----------------------------------------------------------------------------
# (109) <control_variable> → int IDENTIFIER = <control_var_tail>
# -----------------------------------------------------------------------------
def p_control_variable(p):
    """control_variable : INT IDENT EQ control_var_tail"""
    p[0] = ASTNode("control_variable", [
        ASTNode("data_type", value="int"), 
        ASTNode("IDENT", value=p[2]),
        p[4]
    ])



# -----------------------------------------------------------------------------
# (110) <control_var_tail> → int_literal
# (111) <control_var_tail> → <var_call>
# -----------------------------------------------------------------------------
def p_control_var_tail(p):
    """control_var_tail : INT_LIT 
                        | var_call
    """
    if isinstance(p[1], int): 
        p[0] = ASTNode("literal", value=p[1])
    else:
        p[0] = p[1]  


# -----------------------------------------------------------------------------
# (112) <update> → <var_call><update_tail>
# -----------------------------------------------------------------------------
def p_update(p):
    """
    update : var_call update_tail  
    """
    p[0] = ASTNode("update", children=[p[1], p[2]])

# -----------------------------------------------------------------------------
# (113) <update_tail> → <postfix_op>
# (114) <update_tail> → <compound_op><value>
# -----------------------------------------------------------------------------
def p_update_tail(p):
    """
    update_tail : postfix_op         
                | compound_op value   
    """
    if len(p) == 2:
        p[0] = ASTNode("update_tail_postfix", value=p[1])
    else:
        p[0] = ASTNode("update_tail_compound", children=[p[1], p[2]])

# -----------------------------------------------------------------------------
# (115) <postfix_op> → ++
# (116) <postfix_op> → –
# -----------------------------------------------------------------------------
def p_postfix_op(p):
    """
    postfix_op : PLUS_PLUS   
               | MINUS_MINUS 
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (117) <function_call> → FUNCTION_NAME(<arguments>)
# (118) <function_call> → <input_statement>
# -----------------------------------------------------------------------------
def p_function_call(p):
    """
    function_call : FUNCTION_NAME LPAREN arguments RPAREN  
                  | input_statement                      
    """
    if len(p) == 5:
        p[0] = ASTNode("function_call", children=[ASTNode("FUNCTION_NAME", value=p[1]), p[3]])
    else:
        p[0] = p[1]

# -----------------------------------------------------------------------------
# (119) <arguments> → null
# (120) <arguments> → <arg_value><arg_tail>
# -----------------------------------------------------------------------------
def p_arguments(p):
    """
    arguments : empty                  
              | arg_value arg_tail    
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[1]] + p[2]

# -----------------------------------------------------------------------------
# (121) <arg_tail> → , <arg_value><arg_tail>
# (122) <arg_tail> → null
# -----------------------------------------------------------------------------
def p_arg_tail(p):
    """
    arg_tail : COMMA arg_value arg_tail   
             | empty                     
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[3]

# -----------------------------------------------------------------------------
# (123) <arg_value> → <literal>
# (124) <arg_value> → <var_call>
# -----------------------------------------------------------------------------
def p_arg_value(p):
    """
    arg_value : literal   
              | var_call 
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (125) <output_statement> → display <value> <next_val>
# -----------------------------------------------------------------------------
def p_output_statement(p):
    """
    output_statement : DISPLAY value next_val   
    """
    p[0] = ASTNode("output_statement", children=[p[2], p[3]])

# -----------------------------------------------------------------------------
# (126) <next_val> → , <value> <next_val>
# (127) <next_val> → null
# -----------------------------------------------------------------------------
def p_next_val(p):
    """
    next_val : COMMA value next_val  
             | empty                
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[3]

# -----------------------------------------------------------------------------
# (128) <assignment_statement> → IDENTIFIER <assign_tail>
# -----------------------------------------------------------------------------
def p_assignment_statement(p):
    """
    assignment_statement : IDENT assign_tail  
    """
    p[0] = ASTNode("assignment_statement", children=[ASTNode("IDENT", value=p[1]), p[2]])


# -----------------------------------------------------------------------------
# (129) <assign_tail> → .splice(<start>, <deleteCount>, <splice_items>)
# (130) <assign_tail> → .push(<list_element>)
# (131) <assign_tail> → <assign_op><value>
# -----------------------------------------------------------------------------
def p_assign_tail(p):
    """
    assign_tail : DOT SPLICE LPAREN start COMMA deleteCount COMMA splice_items RPAREN  
                | DOT PUSH LPAREN list_element RPAREN                                  
                | assign_op value                                                     
    """
    if len(p) == 10:
        p[0] = ASTNode("assign_tail_splice", children=[p[4], p[6], p[8]])
    elif len(p) == 6:
        p[0] = ASTNode("assign_tail_push", children=[p[4]])
    else:
        p[0] = ASTNode("assign_tail_op", children=[p[1], p[2]])


# -----------------------------------------------------------------------------
# (132) <assign_op> → <compound_op>
# (133) <assign_op> → =
# -----------------------------------------------------------------------------
def p_assign_op(p):
    """
    assign_op : compound_op  
              | EQ           
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (134) <compound_op> → +=
# (135) <compound_op> → -=
# (136) <compound_op> → *=
# (137) <compound_op> → /=
# (138) <compound_op> → %=
# -----------------------------------------------------------------------------
def p_compound_op(p):
    """
    compound_op : PLUS_EQ 
                | MINUS_EQ  
                | MUL_EQ   
                | DIV_EQ    
                | MOD_EQ   
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (139) <start> → int_literal
# -----------------------------------------------------------------------------
def p_start(p):
    """
    start : INT_LIT 
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (140) <deleteCount> → null
# (141) <deleteCount> → int_literal
# -----------------------------------------------------------------------------
def p_deleteCount(p):
    """
    deleteCount : empty     
                | INT_LIT  
    """
    if len(p) == 2 and p[1] is None:
        p[0] = None
    else:
        p[0] = p[1]

# -----------------------------------------------------------------------------
# (142) <splice_items> → null
# (143) <splice_items> → <list_element>
# -----------------------------------------------------------------------------
def p_splice_items(p):
    """
    splice_items : empty          
                 | list_element  
    """
    if len(p) == 2 and p[1] is None:
        p[0] = None
    else:
        p[0] = p[1]

# -----------------------------------------------------------------------------
# (144) <var_call> → IDENTIFIER <list_index>
# -----------------------------------------------------------------------------
def p_var_call(p):
    """
    var_call : IDENT list_index  
    """
    p[0] = ASTNode("var_call", children=[ASTNode("IDENT", value=p[1]), p[2]])


# -----------------------------------------------------------------------------
# (145) <list_index> → [<index>]<list_index2>
# (146) <list_index> → null
# -----------------------------------------------------------------------------
def p_list_index(p):
    """
    list_index : LBRACKET index RBRACKET list_index2  
               | empty                                
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]] + p[4]

# -----------------------------------------------------------------------------
# (147) <list_index2> → [<index>]
# (148) <list_index2> → null
# -----------------------------------------------------------------------------
def p_list_index2(p):
    """
    list_index2 : LBRACKET index RBRACKET 
                | empty                   
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[2]]

# -----------------------------------------------------------------------------
# (149) <index> → int_literal
# (150) <index> → IDENTIFIER
# -----------------------------------------------------------------------------
def p_index(p):
    """
    index : INT_LIT    
          | IDENT      
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (151) <postfix> → null
# (152) <postfix> → <postfix_op>
# -----------------------------------------------------------------------------
def p_postfix(p):
    """
    postfix : empty        
            | postfix_op  
    """
    p[0] = p[1]

# -----------------------------------------------------------------------------
# (153) <value> → <type_cast>
# (154) <value> → <expression>
# (155) <value> → <function_call>
# -----------------------------------------------------------------------------
def p_value(p):
    """
    value : type_cast     
          | value_expression   
          | function_call 
    """
    p[0] = p[1]


def p_value_expression(p):
    """
    value_expression : value_factor value_factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_value_factor(p):
    """
    value_factor : var_call postfix           
           | value_factor1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN value_factor RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("var_postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_value_factor_tail(p):
    """
    value_factor_tail : PLUS value_factor value_factor_tail
                | MINUS value_factor value_factor_tail
                | MULTIPLY value_factor value_factor_tail
                | DIVISION value_factor value_factor_tail
                | MODULO value_factor value_factor_tail
                | EXPONENT value_factor value_factor_tail
                | GT value_factor value_factor_tail
                | LT value_factor value_factor_tail
                | EQ_EQ value_factor value_factor_tail
                | GT_EQ value_factor value_factor_tail
                | LT_EQ value_factor value_factor_tail
                | NOT_EQ value_factor value_factor_tail
                | AND value_factor value_factor_tail
                | OR value_factor value_factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("for_factor_tail_binop", [p[1], p[2], p[3]])

def p_value_factor1 (p):
    """
    value_factor1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT  
    """
    p[0] = p[1]  
# -----------------------------------------------------------------------------
# (156) <type_cast> → to_int(<typecast_value>)
# (157) <type_cast> → to_flt(<typecast_value>)
# (158) <type_cast> → to_bln(<typecast_value>)
# (159) <type_cast> → to_str(<typecast_value>)
# -----------------------------------------------------------------------------
def p_type_cast(p):
    """
    type_cast : CONVERT_TO_INT LPAREN typecast_value RPAREN 
              | CONVERT_TO_FLT LPAREN typecast_value RPAREN  
              | CONVERT_TO_BLN LPAREN typecast_value RPAREN  
              | CONVERT_TO_STR LPAREN typecast_value RPAREN 
    """
    p[0] = ASTNode("type_cast", children=[ASTNode("conversion", value=p[1]), p[3]])


# -----------------------------------------------------------------------------
# (160) <typecast_value> → <expression>
# (161) <typecast_value> → FUNCTION_NAME()
# (162) <typecast_value> → <input_statement>
# -----------------------------------------------------------------------------
def p_typecast_value(p):
    """
    typecast_value : typecast_expression                           
                   | FUNCTION_NAME LPAREN RPAREN          
                   | input_statement                     
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ASTNode("typecast_funcname", value=p[1])


def p_typecast_expression(p):
    """
    typecast_expression : typecast_factor typecast_factor_tail
    """
    if p[2] is None:
        p[0] = ASTNode("expression", [p[1]])
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])


def p_typecast_factor(p):
    """
    typecast_factor : var_call postfix           
           | typecast_factor1                    
           | TILDE INT_LIT               
           | TILDE FLT_LIT                
           | LPAREN typecast_factor RPAREN    
    """
    # We must handle each case by length of p
    if len(p) == 3 and p[2] in ("++", "--", None):  # var_call postfix
        p[0] = ASTNode("postfix", [p[1], p[2]])
    elif len(p) == 2:
        # literal1
        p[0] = ASTNode("literal", value=p[1])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], int):
        # TILDE INT_LIT
        p[0] = ASTNode("neg_int", value=p[2])
    elif len(p) == 3 and p[1] == '~' and isinstance(p[2], float):
        # TILDE FLT_LIT
        p[0] = ASTNode("neg_flt", value=p[2])
    else:
        # ( expression )
        p[0] = ASTNode("paren", [p[2]])


def p_typecast_factor_tail(p):
    """
    typecast_factor_tail : PLUS typecast_factor typecast_factor_tail
                | MINUS typecast_factor typecast_factor_tail
                | MULTIPLY typecast_factor typecast_factor_tail
                | DIVISION typecast_factor typecast_factor_tail
                | MODULO typecast_factor typecast_factor_tail
                | EXPONENT typecast_factor typecast_factor_tail
                | GT typecast_factor typecast_factor_tail
                | LT typecast_factor typecast_factor_tail
                | EQ_EQ typecast_factor typecast_factor_tail
                | GT_EQ typecast_factor typecast_factor_tail
                | LT_EQ typecast_factor typecast_factor_tail
                | NOT_EQ typecast_factor typecast_factor_tail
                | AND typecast_factor typecast_factor_tail
                | OR typecast_factor typecast_factor_tail
                | empty
    """
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("local_factor_tail_binop", [p[1], p[2], p[3]])

def p_typecast_factor1 (p):
    """
    typecast_factor1  : INT_LIT
             | FLT_LIT
             | DAY
             | NIGHT
             | STR_LIT
    """
    p[0] = p[1]  
# -----------------------------------------------------------------------------
# (163) <input_statement> → input()
# -----------------------------------------------------------------------------
def p_input_statement(p):
    """
    input_statement : INPUT LPAREN RPAREN  
    """
    p[0] = ASTNode("input_statement", value=p[1])

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
