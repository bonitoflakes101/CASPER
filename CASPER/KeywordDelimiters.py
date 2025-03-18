# KeywordDelimiters.py

from Delimiters import Delimiters

# For convenience, define one general set that includes space, newline, and some punctuation:
DEFAULT_DELIMS = (
    Delimiters.SPACE
    | Delimiters.NEWLINE
    | {',', ';', '(', ')', '[', ']', '{', '}'}
)


# missing 1D and 2D sa TD
# may "function_initiate" sa TD but wala sa reserved words, prolly just remove this sa TD
KEYWORD_DELIMITERS = {
    # Reserved words for start/end
    "BIRTH": Delimiters.NEWLINE, # FIX
    "GHOST": Delimiters.NULL,

    # Global scope
    "GLOBAL": Delimiters.SPACE,

    # Data types
    "INT": Delimiters.SPACE,
    "FLT": Delimiters.SPACE,
    "BLN": Delimiters.SPACE,
    "CHR": Delimiters.SPACE,
    "STR": Delimiters.SPACE,

    # Boolean literals
    "DAY": Delimiters.DEL17,
    "NIGHT": Delimiters.DEL17,

    # I/O statements
    "INPUT": Delimiters.DEL18,
    "DISPLAY": Delimiters.DEL2, # Changed from SPACE to DEL2

    # Conditionals
    "CHECK": Delimiters.DEL2,
    "OTHERWISE": Delimiters.DEL1,
    "OTHERWISE_CHECK": Delimiters.DEL2,

    # Loop constructs
    "FOR": Delimiters.DEL2,
    "UNTIL": Delimiters.DEL2,
    "REPEAT": Delimiters.DEL1,
    "STOP": Delimiters.NEWLINE,
    "SKIP": Delimiters.NEWLINE,
    "SWAP": Delimiters.DEL2,
    "SHIFT": Delimiters.SPACE,

    # Measure function
    "MEASURE": Delimiters.DEL18,

    # Return 
    "REVIVE": Delimiters.SPACE,

    # Functions
    "FUNCTION": Delimiters.SPACE,
    "FUNCTION_INT": Delimiters.SPACE,
    "FUNCTION_STR": Delimiters.SPACE,
    "FUNCTION_BLN": Delimiters.SPACE,
    "FUNCTION_FLT": Delimiters.SPACE,
    "FUNCTION_CHR": Delimiters.SPACE,
    "FUNCTION_LIST_INT": Delimiters.SPACE,
    "FUNCTION_LIST_STR": Delimiters.SPACE,
    "FUNCTION_LIST_BLN": Delimiters.SPACE,
    "FUNCTION_LIST_FLT": Delimiters.SPACE,
    "FUNCTION_LIST_CHR": Delimiters.SPACE,

    # REMOVED
    # "FUNCTION_LIST_INT2D": Delimiters.SPACE,
    # "FUNCTION_LIST_STR2D": Delimiters.SPACE,
    # "FUNCTION_LIST_BLN2D": Delimiters.SPACE,
    # "FUNCTION_LIST_FLT2D": Delimiters.SPACE,
    # "FUNCTION_LIST_CHR2D": Delimiters.SPACE,

    "IN": Delimiters.DEL2,

    # Conversions
    "CONVERT_TO_INT": Delimiters.DEL18,
    "CONVERT_TO_STR": Delimiters.DEL18,
    "CONVERT_TO_BLN": Delimiters.DEL18,
    "CONVERT_TO_FLT": Delimiters.DEL18,

    # List types (1D, 2D), MISSING SA TD, IDK WHAT TO DO HERE, FIX NEXT TIME
    "LIST_INT": Delimiters.SPACE,
    "LIST_STR": Delimiters.SPACE,
    "LIST_BLN": Delimiters.SPACE,
    "LIST_FLT": Delimiters.SPACE,
    "LIST_CHR": Delimiters.SPACE,

    # REMOVED 
    # "LIST_INT2D": Delimiters.SPACE,
    # "LIST_STR2D": Delimiters.SPACE,
    # "LIST_BLN2D": Delimiters.SPACE,
    # "LIST_FLT2D": Delimiters.SPACE,
    # "LIST_CHR2D": Delimiters.SPACE,

    # --------------------------------------------------------
    # Operators (if you want to force them to have valid next chars)
    # --------------------------------------------------------

    # Arithmetic OPs
    "PLUS": Delimiters.DEL4,  # +
    "MINUS": Delimiters.DEL5,  # -
    "DIVISION": Delimiters.DEL5,  # /
    "MULTIPLY": Delimiters.DEL5,  # * 
    "MODULO": Delimiters.DEL5,  # %

    # Postfic OPs
    "PLUS_PLUS":  Delimiters.DEL13,  # ++ (wala sa reserved symbols)
    "MINUS_MINUS":  Delimiters.DEL13,  # --

   
    # Prefix OPs
    "TILDE":        Delimiters.DEL6,  # ~
    

    # Assignment OPs
    "EQ":            Delimiters.DEL5,  # =
    "PLUS_EQ":       Delimiters.DEL5,  # +=
    "MINUS_EQ":      Delimiters.DEL5,  # -=
    "MUL_EQ":        Delimiters.DEL5,  # *=
    "DIV_EQ":        Delimiters.DEL5,  # /=
    "MOD_EQ":        Delimiters.DEL5,  # %=
    

    # Comparison OPs
    "EQ_EQ":         Delimiters.DEL5,  # ==
    "NOT_EQ":        Delimiters.DEL5,  # !=
    "GT":            Delimiters.DEL5,  # >
    "LT":            Delimiters.DEL5,  # <
    "GT_EQ":         Delimiters.DEL5,  # >=
    "LT_EQ":         Delimiters.DEL5,  # <=

    # Logical OPs
    "NOT":          Delimiters.DEL6,  # !
    "AND":           Delimiters.DEL3,  # &&
    "OR":            Delimiters.DEL3,  # ||
 
    "EXPONENT": Delimiters.DEL5, # 
   

    # Brackets, Braces, Parentheses
    "LBRACKET":      Delimiters.DEL15,  # [
    "RBRACKET":      Delimiters.DEL17,  # ]
    "LBRACE":        Delimiters.DEL9,  # {
    "RBRACE":        Delimiters.DEL10,  # }
    "LPAREN":        Delimiters.DEL7,  # (
    "RPAREN":        Delimiters.DEL8,  # )
    
    
    # seems wrong idk
    "STR_LIT": Delimiters.DEL11,  # delims for "hello"
    "CHR_LIT": Delimiters.DEL11,  # for 'x'

    # alpha -> delim_id
    
    # MISSING
    # --- (for multi-line comments) 
    # << (for single-line comments)
    "COMMENT": Delimiters.SPACE,

    # , = COMMA
    "COMMA": Delimiters.DEL15,
    "SEMICOLON": Delimiters.DEL12,
    "COLON": Delimiters.DEL12,
    # missing "measure" sa keywords but asa TD

    # $ -> validIDSym
    # @ -> validIDSym
    "IDENT": Delimiters.identifier_del,
    "FUNCTION_NAME": Delimiters.identifier_del,

    "PUSH": Delimiters.DEL18,  
    "SPLICE": Delimiters.DEL18,
    "DOT": Delimiters.NULL

}
