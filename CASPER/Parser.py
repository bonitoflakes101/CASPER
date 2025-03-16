from lark import Lark
from lark.lexer import Lexer as LarkLexerBase, Token as LarkToken
from lark.exceptions import UnexpectedToken
from Lexer import Lexer  # orig lexer class ni casper
from Token import TokenType  # orig tokentype class ni casper

# Custom lexer class for lark
class LarkLexer(LarkLexerBase):
    def __init__(self, lexer_conf):
        pass

    def lex(self, data):
        # Initialize the lexer (orig class natin)
        lexer = Lexer(data)
        while True:
            tok = lexer.next_token()
           
            if tok.type == TokenType.EOF:
                break

            # Calculates column number from position
            column = self._calculate_column(data, tok.position)
    
            lark_tok = LarkToken(
                type=tok.type.name,      # Uses the enum name (e.g., "IDENT", "INT_LIT")
                value=tok.literal,       # The token's literal value
                start_pos=tok.position,  # Starting position in the source
                line=tok.line_no,        # Line number
                column=column            # Calculated column number
            )
            yield lark_tok

    def _calculate_column(self, data, position):
        line_start = data.rfind('\n', 0, position) + 1
        return position - line_start + 1


grammar = """
    // Program structure
    program: BIRTH NEWLINE* global_dec NEWLINE* function_statements NEWLINE* MAIN_CASPER LPAREN RPAREN LBRACE NEWLINE* statements NEWLINE* RBRACE NEWLINE NEWLINE* GHOST

    // Literals
    literal: INT_LIT | FLT_LIT | BLN_LIT | CHR_LIT | STR_LIT

    // Global declarations
    global_dec: (global_statement NEWLINE* global_tail)? 
    global_tail: global_dec
    global_statement: data_type IDENT global_statement_tail
    global_statement_tail: | COMMA IDENT global_statement_tail | EQ global_dec_value global_tail2
    global_tail2: COMMA IDENT global_statement_tail | empty
    global_dec_value: global_value | LBRACKET list_element RBRACKET
    global_value: expression

    // Variable statements
    var_statement: data_type IDENT var_tail NEWLINE*
    var_tail: | EQ tail_value var_tail2 | COMMA IDENT var_tail
    var_tail2: COMMA IDENT var_tail | empty
    tail_value: value | LBRACKET list_element RBRACKET

    // List elements
    list_element: literal element_tail
    element_tail: COMMA list_element | empty

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

   

    // Expressions
    expression: factor factor_tail
    factor: var_call | literal | TILDE literal | LPAREN expression RPAREN
    factor_tail: (PLUS | MINUS | MULTIPLY | DIVISION | MODULO | EXPONENT | GT | LT | EQ_EQ | GT_EQ | LT_EQ | NOT_EQ | AND | OR) factor factor_tail | empty

    // Variable calls
    var_call: IDENT var_call_tail
    var_call_tail: LBRACKET index RBRACKET | empty

    // Function statements
    function_statements: (ret_type FUNCTION_NAME LPAREN parameters RPAREN LBRACE statements revive RBRACE)?
    ret_type: FUNCTION | function_dtype
    function_dtype: FUNCTION_INT | FUNCTION_FLT | FUNCTION_CHR | FUNCTION_BLN | FUNCTION_STR 
                | FUNCTION_LIST_INT | FUNCTION_LIST_FLT | FUNCTION_LIST_CHR | FUNCTION_LIST_STR | FUNCTION_LIST_BLN
    parameters: (data_type IDENT parameters_tail)?
    parameters_tail: COMMA data_type IDENT parameters_tail | empty
    revive: REVIVE value | empty

    // Statements TRY 1
    # statements: local_dec statements_tail
    # statements_tail: conditional_statement | switch_statement | loop_statement | function_call | string_operation_statement | output_statement statements_tail2 | empty
    # statements_tail2: statements

    // Statements TRY 2
    statements: local_dec statements_tail | empty
    statements_tail: conditional_statement | switch_statement | loop_statement | function_call | string_operation_statement | output_statement | statements
   

    // Local declarations
    local_dec: var_statement 
   

    // Conditional statements
    conditional_statement: CHECK LPAREN expression RPAREN LBRACE NEWLINE* statements NEWLINE* RBRACE conditional_tail OTHERWISE LBRACE NEWLINE* statements NEWLINE* RBRACE NEWLINE

    //conditional_tail: OTHERWISE_CHECK LPAREN expression RPAREN LBRACE statements RBRACE conditional_tail | empty

    conditional_tail: otherwise_check_tail | empty
    otherwise_check_tail: OTHERWISE_CHECK LPAREN expression RPAREN LBRACE statements RBRACE conditional_tail

    // Switch statements
    switch_statement: SWAP LPAREN IDENT RPAREN LBRACE switch_condition OTHERWISE statements RBRACE
    switch_condition: SHIFT value COLON statements switchcond_tail
    switchcond_tail: switch_condition | empty

    // Loop statements
    loop_statement: for_loop | until_loop | repeat_until

    for_loop: FOR LPAREN control_variable SEMICOLON expression SEMICOLON update RPAREN LBRACE statements RBRACE

    until_loop: UNTIL LPAREN expression RPAREN LBRACE statements RBRACE

    repeat_until: REPEAT LBRACE statements RBRACE UNTIL LPAREN expression RPAREN

    control_variable: INT IDENT EQ INT_LIT

    //Update
    update: var_call update_tail
    update_tail: postfix | assign_op value
    postfix: PLUS_PLUS | MINUS_MINUS

    // Function calls
    function_call: FUNCTION_NAME LPAREN arguments RPAREN

    // Arguments
    arguments: (arg_value arg_tail)?
    arg_tail: COMMA arg_value arg_tail | empty
    arg_value: literal | var_call

    // Output statements
    output_statement: DISPLAY value next_val
    next_val: COMMA value next_val | empty

    // Input statements
    input_statement: INPUT LPAREN RPAREN

    // String operation statements
    string_operation_statement: var_call string_operation_tail
    string_operation_tail: PLUS string_val stringcon_tail | update_tail
    stringcon_tail: PLUS string_val stringcon_tail | empty
    string_val: var_call | STR_LIT

    // Assignment operators
    assign_op: PLUS_EQ | MINUS_EQ | MUL_EQ | DIV_EQ | MOD_EQ | EQ

    // Empty rule
    empty:



    // Terminal Symbols

    // Main Keywords
    %declare BIRTH GHOST MAIN_CASPER

    //Identifiers
    %declare IDENT

    //literals
    %declare INT_LIT FLT_LIT BLN_LIT CHR_LIT STR_LIT

    // Data Types
    %declare INT FLT BLN CHR STR

    // Arithmetic Operators
    %declare PLUS MINUS MULTIPLY DIVISION MODULO EXPONENT 

    // Assignment Operators
    %declare EQ PLUS_EQ MINUS_EQ MUL_EQ DIV_EQ MOD_EQ
    
    // Relational/Comparison Operatos
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

    //Input - Output
    %declare INPUT DISPLAY

    //Type Cast
    %declare CONVERT_TO_INT CONVERT_TO_FLT CONVERT_TO_BLN CONVERT_TO_STR

    // Parentheses
    %declare LPAREN RPAREN LBRACE RBRACE LBRACKET RBRACKET  

    // COMMENTS
    %declare COMMENT DOUBLE_LT

    // Other Keywords
    %declare COMMA COLON SEMICOLON NEWLINE CARRIAGE_RETURN IN MEASURE 

"""


parser = Lark(grammar, parser='lalr', lexer=LarkLexer, start='program')

def parse(code):
    try:
        tree = parser.parse(code)
        # return {"status": "success", "tree": str(tree)}
        return "No Syntax Errors"
    except UnexpectedToken as e:
        unexpected = e.token
        expected = e.accepts
        error_msg = (
            f"Syntax error at line {unexpected.line}, column {unexpected.column}\n"
            f"Unexpected token '{unexpected.value}'\n"
            f"Expected: {', '.join(sorted(expected))}"
        )
        return error_msg
    except Exception as e:
        return f"Unexpected error: {e}"