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
    "DISPLAY": Delimiters.SPACE,

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
    "FUNCTION_LIST_INT": Delimiters.DEL19,
    "FUNCTION_LIST_STR": Delimiters.DEL19,
    "FUNCTION_LIST_BLN": Delimiters.DEL19,
    "FUNCTION_LIST_FLT": Delimiters.DEL19,
    "FUNCTION_LIST_CHR": Delimiters.DEL19,

    # Wala sa TD to, should be [][] yung delims
    "FUNCTION_LIST_INT2D": Delimiters.DEL19,
    "FUNCTION_LIST_STR2D": Delimiters.DEL19,
    "FUNCTION_LIST_BLN2D": Delimiters.DEL19,
    "FUNCTION_LIST_FLT2D": Delimiters.DEL19,
    "FUNCTION_LIST_CHR2D": Delimiters.DEL19,

    "IN": Delimiters.DEL2,

    # Conversions
    "CONVERT_TO_INT": Delimiters.DEL18,
    "CONVERT_TO_STR": Delimiters.DEL18,
    "CONVERT_TO_BLN": Delimiters.DEL18,
    "CONVERT_TO_FLT": Delimiters.DEL18,

    # List types (1D, 2D), MISSING SA TD, IDK WHAT TO DO HERE, FIX NEXT TIME
    "LIST_INT": DEFAULT_DELIMS,
    "LIST_STR": DEFAULT_DELIMS,
    "LIST_BLN": DEFAULT_DELIMS,
    "LIST_FLT": DEFAULT_DELIMS,
    "LIST_CHR": DEFAULT_DELIMS,
    "LIST_INT2D": DEFAULT_DELIMS,
    "LIST_STR2D": DEFAULT_DELIMS,
    "LIST_BLN2D": DEFAULT_DELIMS,
    "LIST_FLT2D": DEFAULT_DELIMS,
    "LIST_CHR2D": DEFAULT_DELIMS,

    # --------------------------------------------------------
    # Operators (if you want to force them to have valid next chars)
    # --------------------------------------------------------
    "PLUS":          Delimiters.DEL6,  # +
    "PLUS_PLUS":  Delimiters.DEL13,  # ++ (wala sa reserved symbols)
    "MINUS":         Delimiters.DEL6,  # -
    "MINUS_MINUS":  Delimiters.DEL13,  # --
   
    "SLASH":         Delimiters.DEL5,  # /
    "ASTERISK":      Delimiters.DEL5,  # * 
    "MOD":           Delimiters.DEL5,  # %
    "DOUBLE_SLASH":  Delimiters.DEL5,  # // not sure
    "DOUBLE_ASTERISK": Delimiters.DEL5, # ** not sure
    "EQ":            Delimiters.DEL6,  # =

    # WALA SA TD, mema delims muna
    "PLUS_EQ":       Delimiters.DEL2,  # +=
    "MINUS_EQ":      Delimiters.DEL2,  # -=
    "MUL_EQ":        Delimiters.DEL2,  # *=
    "DIV_EQ":        Delimiters.DEL2,  # /=
    "MOD_EQ":        Delimiters.DEL2,  # %=

    "EQ_EQ":         Delimiters.DEL6,  # ==
    "NOT_EQ":        Delimiters.DEL6,  # !=
    "GT":            Delimiters.DEL9,  # >
    "LT":            Delimiters.DEL9,  # <
    "GT_EQ":         Delimiters.DEL6,  # >=
    "LT_EQ":         Delimiters.DEL6,  # <=
    "AND":           Delimiters.DEL2,  # &&
    "OR":            Delimiters.DEL2,  # ||
    "BANG":          Delimiters.DEL8,  # !
    "LBRACKET":      Delimiters.DEL6,  # [
    "RBRACKET":      Delimiters.DEL7,  # ]
    "LBRACE":        Delimiters.DEL16,  # {
    "RBRACE":        Delimiters.DEL4,  # }
    "LPAREN":        Delimiters.DEL15,  # (
    "RPAREN":        Delimiters.DEL7,  # )
    
    
    # seems wrong idk
    "STR_LIT": Delimiters.DEL11,  # delims for "hello"
    "CHR_LIT": Delimiters.DEL11,  # for 'x'

    # alpha -> delim_id
    
    # MISSING
    # --- (for multi-line comments) 
    # << (for single-line comments)
    # , = COMMA
    # missing "measure" sa keywords but asa TD

    # $ -> validIDSym
    # @ -> validIDSym


}
