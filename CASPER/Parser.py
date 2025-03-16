from lark import Lark, Transformer, Token as LarkToken
from lark.exceptions import UnexpectedToken
from Lexer import Lexer  # original Casper lexer
from Token import TokenType  # original token type enum
from lark.lexer import Lexer as LarkLexerBase


# --------------------------------------------------------------------
# AST Node definition (to match your semantics)
# --------------------------------------------------------------------
class ASTNode:
    def __init__(self, type, children=None, value=None):
        self.type = type
        self.children = children or []
        self.value = value

    def __repr__(self):
        return f"ASTNode({self.type}, value={self.value}, children={self.children})"

class ASTBuilder(Transformer):
    def __default__(self, data, children, meta):
        return ASTNode(data, children=children)
    def __default_token__(self, token):
        return ASTNode(token.type, value=token.value)
# --------------------------------------------------------------------
# Mapping for friendly error messages (unchanged)
# --------------------------------------------------------------------
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

    # Arithmetic
    "PLUS": "+",
    "MINUS": "-",
    "MULTIPLY": "*",
    "EXPONENT": "**",
    "MODULO": "%",
    "DIVISION": "/",
    "DOUBLE_SLASH": "//",
    "POW": "^",

    # Prefix
    "TILDE": "~",
    "NOT": "!",

    # Postfix
    "PLUS_PLUS": "++",
    "MINUS_MINUS": "--",

    # Assignment
    "EQ": "=",
    "PLUS_EQ": "+=",
    "MINUS_EQ": "-=",
    "MUL_EQ": "*=",
    "DIV_EQ": "/=",
    "MOD_EQ": "%=",

    # Comparison
    "EQ_EQ": "==",
    "NOT_EQ": "!=",
    "LT": "<",
    "GT": ">",
    "LT_EQ": "<=",
    "GT_EQ": ">=",

    # Logical
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

# --------------------------------------------------------------------
# Custom lexer class for Lark (unchanged)
# --------------------------------------------------------------------
class LarkLexer(LarkLexerBase):
    def __init__(self, lexer_conf):
        pass

    def lex(self, data):
        # Initialize the original Casper lexer
        lexer = Lexer(data)
        while True:
            tok = lexer.next_token()
            if tok.type == TokenType.EOF:
                break
            column = self._calculate_column(data, tok.position)
            lark_tok = LarkToken(
                type=tok.type.name,      # Use the enum name, e.g., "IDENT", "INT_LIT"
                value=tok.literal,       # The token's literal value
                start_pos=tok.position,
                line=tok.line_no,
                column=column
            )
            yield lark_tok

    def _calculate_column(self, data, position):
        line_start = data.rfind('\n', 0, position) + 1
        return position - line_start + 1

# --------------------------------------------------------------------
# Grammar string updated with new CFG and terminal declarations
# --------------------------------------------------------------------
grammar = """
// Program structure
program: BIRTH NEWLINE* global_dec NEWLINE* function_statements NEWLINE* MAIN_CASPER LPAREN RPAREN LBRACE NEWLINE* statements NEWLINE* RBRACE NEWLINE* GHOST

// Global declarations
global_dec: (global_statement NEWLINE* global_tail)?
global_tail: global_dec
global_statement: data_type IDENT global_statement_tail
global_statement_tail: (COMMA IDENT global_statement_tail | EQ global_dec_value global_tail2 | empty)
global_tail2: (COMMA IDENT global_statement_tail | empty)
global_dec_value: global_value | LBRACKET list_element RBRACKET
global_value: expression

// Variable statements
var_statement: data_type IDENT var_tail NEWLINE*
var_tail: (EQ tail_value var_tail2 | COMMA IDENT var_tail | empty)
var_tail2: (COMMA IDENT var_tail | empty)
tail_value: value | LBRACKET list_element RBRACKET

// List elements
list_element: literal element_tail
element_tail: (COMMA list_element | empty)

// Index
index: INT_LIT | IDENT

// Data types
data_type: INT | FLT | BLN | CHR | STR

// Values
value: type_cast | expression | function_call

// Type Casting
type_cast: CONVERT_TO_INT LPAREN typecast_value RPAREN
         | CONVERT_TO_FLT LPAREN typecast_value RPAREN
         | CONVERT_TO_BLN LPAREN typecast_value RPAREN
         | CONVERT_TO_STR LPAREN typecast_value RPAREN
typecast_value: expression | FUNCTION_NAME LPAREN RPAREN | input_statement

// Literals
literal: INT_LIT | FLT_LIT | BLN_LIT | CHR_LIT | STR_LIT

// Expressions
expression: factor factor_tail
factor: var_call | literal | TILDE literal | LPAREN expression RPAREN
factor_tail: (PLUS | MINUS | MULTIPLY | DIVISION | MODULO | EXPONENT | GT | LT | EQ_EQ | GT_EQ | LT_EQ | NOT_EQ | AND | OR) factor factor_tail | empty

// Variable calls
var_call: IDENT var_call_tail
var_call_tail: (LBRACKET index RBRACKET | empty)

// Function statements
function_statements: (function_declaration)*
function_declaration: ret_type FUNCTION_NAME LPAREN parameters RPAREN LBRACE NEWLINE* statements NEWLINE* revive NEWLINE* RBRACE

ret_type: FUNCTION | function_dtype
function_dtype: FUNCTION_INT | FUNCTION_FLT | FUNCTION_CHR | FUNCTION_BLN | FUNCTION_STR 
              | FUNCTION_LIST_INT | FUNCTION_LIST_FLT | FUNCTION_LIST_CHR | FUNCTION_LIST_STR | FUNCTION_LIST_BLN

parameters: (data_type IDENT parameters_tail)?
parameters_tail: (COMMA data_type IDENT parameters_tail | empty)

revive: (REVIVE value | empty)

// Statements
statements: (local_dec | conditional_statement | switch_statement | loop_statement | function_call | string_operation_statement | output_statement)*
local_dec: var_statement

// Conditional statements
conditional_statement: CHECK LPAREN expression RPAREN LBRACE NEWLINE* statements NEWLINE* RBRACE conditional_tail OTHERWISE LBRACE NEWLINE* statements NEWLINE* RBRACE NEWLINE
conditional_tail: (otherwise_check_tail | empty)
otherwise_check_tail: OTHERWISE_CHECK LPAREN expression RPAREN LBRACE statements RBRACE conditional_tail

// Switch statements
switch_statement: SWAP LPAREN IDENT RPAREN LBRACE switch_condition OTHERWISE statements RBRACE
switch_condition: SHIFT value COLON statements switchcond_tail
switchcond_tail: (switch_condition | empty)

// Loop statements
loop_statement: for_loop | until_loop | repeat_until
for_loop: FOR LPAREN control_variable SEMICOLON expression SEMICOLON update RPAREN LBRACE statements RBRACE
until_loop: UNTIL LPAREN expression RPAREN LBRACE statements RBRACE
repeat_until: REPEAT LBRACE statements RBRACE UNTIL LPAREN expression RPAREN

control_variable: INT IDENT EQ control_var_tail
control_var_tail: INT_LIT | var_call

update: var_call update_tail
update_tail: (postfix | assign_op value)
postfix: PLUS_PLUS | MINUS_MINUS

// Function call and arguments
function_call: (FUNCTION_NAME LPAREN arguments RPAREN) | input_statement
arguments: (arg_value arg_tail)?
arg_tail: (COMMA arg_value arg_tail | empty)
arg_value: literal | var_call

// Output statement
output_statement: DISPLAY value next_val
next_val: (COMMA value next_val | empty)

// Input statement
input_statement: INPUT LPAREN RPAREN

// String operation statements
string_operation_statement: var_call string_operation_tail
string_operation_tail: (PLUS string_val stringcon_tail | update_tail)
stringcon_tail: (PLUS string_val stringcon_tail | empty)
string_val: var_call | STR_LIT

// Assignment operators
assign_op: PLUS_EQ | MINUS_EQ | MUL_EQ | DIV_EQ | MOD_EQ | EQ

// Empty rule
empty:

// Terminal Symbols

// Main Keywords
%declare BIRTH GHOST MAIN_CASPER

// Identifiers
%declare IDENT

// Literals
%declare INT_LIT FLT_LIT BLN_LIT CHR_LIT STR_LIT

// Data Types
%declare INT FLT BLN CHR STR

// Arithmetic Operators
%declare PLUS MINUS MULTIPLY DIVISION MODULO EXPONENT

// Assignment Operators
%declare EQ PLUS_EQ MINUS_EQ MUL_EQ DIV_EQ MOD_EQ

// Relational/Comparison Operators
%declare GT LT EQ_EQ GT_EQ LT_EQ NOT_EQ

// Logical Operators
%declare AND OR

// Prefix Operators
%declare TILDE NOT

// Postfix Operators
%declare PLUS_PLUS MINUS_MINUS

// Conditional Keywords
%declare CHECK OTHERWISE OTHERWISE_CHECK

// Loop Keywords
%declare SWAP SHIFT FOR UNTIL REPEAT

// Function Types
%declare FUNCTION FUNCTION_INT FUNCTION_FLT FUNCTION_CHR FUNCTION_BLN FUNCTION_STR FUNCTION_LIST_INT FUNCTION_LIST_FLT FUNCTION_LIST_CHR FUNCTION_LIST_STR FUNCTION_LIST_BLN

// Function Keywords
%declare FUNCTION_NAME REVIVE STOP SKIP

// Input - Output
%declare INPUT DISPLAY

// Type Cast
%declare CONVERT_TO_INT CONVERT_TO_FLT CONVERT_TO_BLN CONVERT_TO_STR

// Parentheses
%declare LPAREN RPAREN LBRACE RBRACE LBRACKET RBRACKET

// Comments
%declare COMMENT DOUBLE_LT

// Other Keywords
%declare COMMA COLON SEMICOLON NEWLINE CARRIAGE_RETURN IN MEASURE
"""

# --------------------------------------------------------------------
# Build the parser using the new grammar, custom lexer, and our AST transformer
# --------------------------------------------------------------------
parser = Lark(grammar, parser='lalr', lexer=LarkLexer, start='program', transformer=ASTBuilder())

def parse(code):
    """
    # NEW: Instead of returning AST or string,
    #      we return a dictionary with 'ast' and 'error' keys.
    """
    try:
        ast = parser.parse(code)  
        return {
            "ast": ast,        # The AST
            "error": None      # No error
        }
    except UnexpectedToken as e:
        friendly_unexpected = token_display.get(e.token.type, e.token.type)
        friendly_expected_list = [token_display.get(t, t) for t in e.accepts]
        friendly_expected_str = ", ".join(friendly_expected_list)

        error_message = (
            f"Syntax Error at line {e.token.line}, column {e.token.column}:\n"
            f"  Unexpected token '{e.token.value}'\n"
            f"  Expected one of: {friendly_expected_str}"
        )
        return {
            "ast": None,       # No AST
            "error": error_message
        }
    except Exception as e:
        return {
            "ast": None,
            "error": f"Unexpected error: {e}"
        }