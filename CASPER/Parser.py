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
    """main_function : MAIN_CASPER LPAREN RPAREN LBRACE maybe_newline statements maybe_newline RBRACE"""
    p[0] = ASTNode("main_function", [p[5]], p[1])

# -----------------------------------------------------------------------------
# Production: <global_dec> → <global_statement> <global_tail> | null
# -----------------------------------------------------------------------------
def p_global_dec(p):
    """global_dec : global_statement unli_newline global_tail 
                  | empty"""
    if len(p) == 2:
        p[0] = ASTNode("global_dec", [])
    else:
        tail = p[2] if p[2] is not None else []
        p[0] = ASTNode("global_dec", [p[1]] + tail)

# -----------------------------------------------------------------------------
# Production: <global_tail> → <global_dec> | null
# -----------------------------------------------------------------------------
def p_global_tail(p):
    """global_tail : global_dec
                   | empty"""
    if p[1] is None:
        p[0] = []
    else:
        # Assuming global_dec returns an ASTNode whose children list holds additional declarations
        p[0] = p[1].children

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
# Production: <global_value> → <factor> | <expression>
# -----------------------------------------------------------------------------
def p_global_value(p):
    """global_value : factor
                    | expression"""
    p[0] = p[1]

# -----------------------------------------------------------------------------
# Production: <var_statement> → <data_type> IDENT <var_tail>
# -----------------------------------------------------------------------------
def p_var_statement(p):
    """var_statement : data_type IDENT var_tail"""
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
# Production: <value> → <factor> | <type_cast> | <expression> | <function_call>
# -----------------------------------------------------------------------------
def p_value(p):
    """value : factor
             | type_cast
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
# Production: <typecast_value> → IDENT | <literal> | <expression> | FUNCTION_NAME() | <input_statement>
# -----------------------------------------------------------------------------
def p_typecast_value(p):
    """typecast_value : IDENT
                      | literal
                      | expression
                      | FUNCTION_NAME LPAREN RPAREN
                      | input_statement"""
    if len(p) == 2:
        p[0] = ASTNode("typecast_value", value=p[1])
    else:
        p[0] = ASTNode("typecast_value", value=p[1])

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
    "expression : expr_head expr_tail"
    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = ASTNode("expression", [p[1], p[2]])

# -----------------------------------------------------------------------------
# Production: <expr_head> → <term> <term_tail>
# -----------------------------------------------------------------------------
def p_expr_head(p):
    "expr_head : term term_tail"
    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = ASTNode("expr_head", [p[1], p[2]])

# -----------------------------------------------------------------------------
# Production: <term> → <factor> <factor_tail>
# -----------------------------------------------------------------------------
def p_term(p):
    "term : factor factor_tail"
    if p[2] is None:
        p[0] = p[1]
    else:
        p[0] = ASTNode("term", [p[1], p[2]])

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
                   | EXPONENT expression"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("factor_tail", [p[2]], p[1])

# -----------------------------------------------------------------------------
# Production: <term_tail> → null | > <expression> | < <expression> | == <expression> | GT_EQ <expression> | LT_EQ <expression> | != <expression>
# -----------------------------------------------------------------------------
def p_term_tail(p):
    """term_tail : empty
                 | GT expression
                 | LT expression
                 | EQ_EQ expression
                 | GT_EQ expression
                 | LT_EQ expression
                 | NOT_EQ expression"""
    if len(p) == 2:
        p[0] = None
    else:
        op = p[1]
        if op == "GT_EQ":
            op = "=>"
        elif op == "LT_EQ":
            op = "=<"
        p[0] = ASTNode("term_tail", [p[2]], op)

# -----------------------------------------------------------------------------
# Production: <expr_tail> → null | AND <expression> | OR <expression>
# -----------------------------------------------------------------------------
def p_expr_tail(p):
    """expr_tail : empty
                 | AND expression
                 | OR expression"""
    if len(p) == 2:
        p[0] = None
    else:
        p[0] = ASTNode("expr_tail", [p[2]], p[1])

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

# -----------------------------------------------------------------------------
# Production: <function_statements> → <ret_type> FUNCTION_NAME ( <parameters> ) { <statements> <revive> }
# -----------------------------------------------------------------------------
def p_function_statements(p):
    """function_statements : maybe_newline ret_type FUNCTION_NAME LPAREN parameters RPAREN maybe_newline LBRACE unli_newline statements revive maybe_newline RBRACE 
                         | empty"""
    if len(p) == 2:
    
        p[0] = None
    else:
        p[0] = ASTNode("function_statements", [p[1],
                                                ASTNode("FUNCTION_NAME", value=p[2]),
                                                p[4],
                                                p[7],
                                                p[8]])

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
# Production: <statements_tail> → null | one of: <conditional_statement> | <switch_statement> | <loop_statement> | <function_call> | <string_operation_statement> | <global_reference> | <output_statement> then <statements_tail>
# -----------------------------------------------------------------------------
def p_statements_tail(p):
    """
    statements_tail : empty
                    | string_operation_statement unli_newline statements_tail
                    | conditional_statement unli_newline statements_tail
                    | switch_statement unli_newline statements_tail
                    | loop_statement unli_newline statements_tail
                    | function_call unli_newline statements_tail
                    | output_statement unli_newline statements_tail
                    | statements unli_newline
    """
    if len(p) == 2:
        p[0] = []  # empty
    # If the alternative starts with string_operation_statement, conditional_statement, etc.
    elif len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        # For the "statements maybe_newline" alternative (when it’s the last alternative)
        if isinstance(p[1], list):
            p[0] = p[1]
        else:
            p[0] = [p[1]] + p[2]

# -----------------------------------------------------------------------------
# Production: <local_dec> → <var_statement>
# -----------------------------------------------------------------------------
def p_local_dec(p):
    """local_dec : empty
                 | var_statement"""
    p[0] = p[1] if p[1] is not None else ASTNode("local_dec", [])


# -----------------------------------------------------------------------------
# Production: <conditional_statement> → check ( <expression> ) { <statements> } <conditional_tail>
# -----------------------------------------------------------------------------
def p_conditional_statement(p):
    "conditional_statement : CHECK LPAREN expression RPAREN LBRACE maybe_newline statements RBRACE conditional_tail"
    p[0] = ASTNode("conditional_statement", [p[3], p[6], p[8]])

# -----------------------------------------------------------------------------
# Production: <conditional_tail> → null | otherwise_check ( <expression> ) { <statements> } | otherwise { <statements> }
# -----------------------------------------------------------------------------
def p_conditional_tail(p):
    """conditional_tail : empty
                        | maybe_newline OTHERWISE_CHECK LPAREN expression RPAREN LBRACE maybe_newline statements RBRACE
                        | maybe_newline OTHERWISE LBRACE maybe_newline statements RBRACE"""
    if len(p) == 2:
        p[0] = None
    elif p[1] == "otherwise_check":
        p[0] = ASTNode("conditional_tail", [p[3], p[6]])
    else:
        p[0] = ASTNode("conditional_tail", [p[3]])

# -----------------------------------------------------------------------------
# Production: <switch_statement> → swap(IDENT){ <switch_condition> otherwise <statements> }
# -----------------------------------------------------------------------------
def p_switch_statement(p):
    "switch_statement : SWAP LPAREN IDENT RPAREN LBRACE switch_condition OTHERWISE statements RBRACE"
    p[0] = ASTNode("switch_statement", [ASTNode("IDENT", value=p[3]), p[6], p[8]])

# -----------------------------------------------------------------------------
# Production: <switch_condition> → shift <value> : <statements> <switchcond_tail>
# -----------------------------------------------------------------------------
def p_switch_condition(p):
    "switch_condition : SHIFT value COLON statements switchcond_tail"
    p[0] = ASTNode("switch_condition", [p[2], p[4], p[5]])

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
    "for_loop : FOR LPAREN control_variable SEMICOLON expression SEMICOLON update RPAREN maybe_newline LBRACE maybe_newline statements RBRACE"
    p[0] = ASTNode("for_loop", [p[3], p[5], p[7], p[11]])

# -----------------------------------------------------------------------------
# Production: <until_loop> → until ( <expression> ) { <statements> }
# -----------------------------------------------------------------------------
def p_until_loop(p):
    "until_loop : UNTIL LPAREN expression RPAREN LBRACE statements RBRACE"
    p[0] = ASTNode("until_loop", [p[3], p[6]])

# -----------------------------------------------------------------------------
# Production: <repeat_until> → repeat { <statements> } until ( <expression> )
# -----------------------------------------------------------------------------
def p_repeat_until(p):
    "repeat_until : REPEAT LBRACE statements RBRACE UNTIL LPAREN expression RPAREN"
    p[0] = ASTNode("repeat_until", [p[3], p[7]])

# -----------------------------------------------------------------------------
# Production: <control_variable> → int IDENT = int_literal
# -----------------------------------------------------------------------------
def p_control_variable(p):
    "control_variable : INT IDENT EQ INT_LIT"
    p[0] = ASTNode("control_variable", [p[1], ASTNode("IDENT", value=p[2]), p[4]])

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
# Production: <function_call> → FUNCTION_NAME ( <arguments> ) | <input_statement>
# -----------------------------------------------------------------------------
def p_function_call(p):
    """function_call : FUNCTION_NAME LPAREN arguments RPAREN
                     | input_statement"""
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
    p[0] = ASTNode("output_statement", [p[2], p[3]])

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
    """string_operation_tail : assign_op value
                             | PLUS string_val stringcon_tail"""
    if p[1] == '+':
        p[0] = ASTNode("string_operation_tail", [p[2], p[3]], "+")
    else:
        p[0] = ASTNode("string_operation_tail", [p[2]], p[1])

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
