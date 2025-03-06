from enum import Enum
from typing import Any

class TokenType(Enum):
    # Special Tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    # Data Types and Literals
    IDENT = "IDENT"
    INT = "INT"
    INT_LIT = "INT_LIT"  # Integer literal
    FLT = "FLT"
    FLT_LIT = "FLT_LIT"  # Float literal
    BLN = "BLN"
    BLN_LIT = "BLN_LIT"  # Boolean literal
    STR = "STR"
    STR_LIT = "STR_LIT"  # String literal
    CHR = "CHR"
    CHR_LIT = "CHR_LIT"  # Character literal



    # Function Types
    FUNCTION = "FUNCTION"
    FUNCTION_INT = "FUNCTION_INT"
    FUNCTION_STR = "FUNCTION_STR"
    FUNCTION_BLN = "FUNCTION_BLN"
    FUNCTION_FLT = "FUNCTION_FLT"
    FUNCTION_CHR = "FUNCTION_CHR"
    FUNCTION_LIST_INT = "FUNCTION_LIST_INT"
    FUNCTION_LIST_STR = "FUNCTION_LIST_STR"
    FUNCTION_LIST_BLN = "FUNCTION_LIST_BLN"
    FUNCTION_LIST_FLT = "FUNCTION_LIST_FLT"
    FUNCTION_LIST_CHR = "FUNCTION_LIST_CHR"
    FUNCTION_LIST_INT2D = "FUNCTION_LIST_INT2D"
    FUNCTION_LIST_STR2D = "FUNCTION_LIST_STR2D"
    FUNCTION_LIST_BLN2D = "FUNCTION_LIST_BLN2D"
    FUNCTION_LIST_FLT2D = "FUNCTION_LIST_FLT2D"
    FUNCTION_LIST_CHR2D = "FUNCTION_LIST_CHR2D"

    # Type Conversion
    CONVERT_TO_INT = "CONVERT_TO_INT"
    CONVERT_TO_STR = "CONVERT_TO_STR"
    CONVERT_TO_BLN = "CONVERT_TO_BLN"
    CONVERT_TO_FLT = "CONVERT_TO_FLT"

    # List Types
    LIST_INT = "LIST_INT"
    LIST_STR = "LIST_STR"
    LIST_BLN = "LIST_BLN"
    LIST_FLT = "LIST_FLT"
    LIST_CHR = "LIST_CHR"
    LIST_INT2D = "LIST_INT2D"
    LIST_STR2D = "LIST_STR2D"
    LIST_BLN2D = "LIST_BLN2D"
    LIST_FLT2D = "LIST_FLT2D"
    LIST_CHR2D = "LIST_CHR2D"

    # Other
    FUNCTION_NAME = "FUNCTION_NAME"
    MAIN_CASPER = "MAIN_CASPER"

    # Arithmetic Symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "ASTERISK"
    EXPONENT = "EXPONENT"
    MODULO = "%"
    DIVISION = "SLASH"

    DOUBLE_SLASH = "DOUBLE_SLASH"
    POW = "POW"
    
    # Prefix Symbols
    TILDE = "TILDE"
    NOT = "NOT"
    
    # Postfix Symbols
    PLUS_PLUS = "PLUS_PLUS"
    MINUS_MINUS = "MINUS_MINUS"


    # Assignment Symbols
    EQ = "EQ"
    PLUS_EQ = "PLUS_EQ"
    MINUS_EQ = "MINUS_EQ"
    MUL_EQ = "MUL_EQ"
    DIV_EQ = "DIV_EQ"
    MOD_EQ = "MOD_EQ"

    # Comparison Symbols
    EQ_EQ = "EQ_EQ"
    NOT_EQ = "NOT_EQ"
    LT = "LT"
    GT = "GT"
    LT_EQ = "LT_EQ"
    GT_EQ = "GT_EQ"

    # Logical Symbols
    AND = "&&"
    OR = "||"    

    # Comments
    COMMENT = "COMMENT"
    DOUBLE_LT = "DOUBLE_LT"

    COMMA = "COMMA"

    # Keywords
    BIRTH = "BIRTH"
    GHOST = "GHOST"
    INPUT = "INPUT"
    DISPLAY = "DISPLAY"
    CHECK = "CHECK"
    OTHERWISE = "OTHERWISE"
    OTHERWISE_CHECK = "OTHERWISE_CHECK"
    FOR = "FOR"
    REPEAT = "REPEAT"
    UNTIL = "UNTIL"
    STOP = "STOP"
    SKIP = "SKIP"
    SWAP = "SWAP"
    SHIFT = "SHIFT"
    REVIVE = "REVIVE"
    # GLOBAL = "GLOBAL"
    # STRUCTURE = "STRUCTURE"
    DAY = "DAY"
    NIGHT = "NIGHT"
    MEASURE = "MEASURE"
    IN = "IN"
    CARRIAGE_RETURN = "CARRIAGE_RETURN"
    NEWLINE = "NEWLINE"
    SEMICOLON = ";"
    COLON = ":"


    # Typing
    TYPE = "TYPE"

    # Parentheses
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = '{'
    RBRACE = '}'
    LBRACKET = '['
    RBRACKET = ']'


class Token:
    def __init__(self, type: TokenType, literal: Any, line_no: int, position: int) -> None:
        self.type = type
        self.literal = literal
        self.line_no = line_no
        self.position = position

    def __str__(self) -> str:
        if self.type == TokenType.ILLEGAL:
            return f"{self.type.name} Token: '{self.literal}' at Line no:  {self.line_no}"
        else:
            return f"Token: {self.type.name} : {self.literal} \nLine no: {self.line_no} - Position no: {self.position}"
        # return f"Token[{self.type} : {self.literal} : Line {self.line_no} : Position {self.position}]"
    
    def __repr__(self) -> str:
        return str(self)

KEYWORDS: dict[str, TokenType] = {
    "birth": TokenType.BIRTH,
    "ghost": TokenType.GHOST,
    "input": TokenType.INPUT,
    "display": TokenType.DISPLAY,
    "check": TokenType.CHECK,
    "otherwise": TokenType.OTHERWISE,
    "otherwise_check": TokenType.OTHERWISE_CHECK,
    "for": TokenType.FOR,
    "repeat": TokenType.REPEAT,
    "until": TokenType.UNTIL,
    "stop": TokenType.STOP,
    "skip": TokenType.SKIP,
    "swap": TokenType.SWAP,
    "shift": TokenType.SHIFT,
    "revive": TokenType.REVIVE,
    # "GLOBAL": TokenType.GLOBAL,
    "Day": TokenType.DAY,
    "Night": TokenType.NIGHT,
    # "day": TokenType.DAY,
    # "night": TokenType.NIGHT,
    "measure": TokenType.MEASURE, # wala pang delims
    "in": TokenType.IN,
    "int": TokenType.INT,
    "flt": TokenType.FLT,
    "bln": TokenType.BLN,
    "str": TokenType.STR,
    "chr": TokenType.CHR,

    # Function keywords
    "function": TokenType.FUNCTION,
    "function_int": TokenType.FUNCTION_INT,
    "function_str": TokenType.FUNCTION_STR,
    "function_bln": TokenType.FUNCTION_BLN,
    "function_flt": TokenType.FUNCTION_FLT,
    "function_chr": TokenType.FUNCTION_CHR,
    # FIX
    "function_list_int": TokenType.FUNCTION_LIST_INT,
    "function_list_str": TokenType.FUNCTION_LIST_STR,
    "function_list_bln": TokenType.FUNCTION_LIST_BLN,
    "function_list_flt": TokenType.FUNCTION_LIST_FLT,
    "function_list_chr": TokenType.FUNCTION_LIST_CHR,

    # REMOVED
    # "function_list_int2d": TokenType.FUNCTION_LIST_INT2D,
    # "function_list_str2d": TokenType.FUNCTION_LIST_STR2D,
    # "function_list_bln2d": TokenType.FUNCTION_LIST_BLN2D,
    # "function_list_flt2d": TokenType.FUNCTION_LIST_FLT2D,
    # "function_list_chr2d": TokenType.FUNCTION_LIST_CHR2D,

    # Type conversion keywords
    "to_int": TokenType.CONVERT_TO_INT,
    "to_str": TokenType.CONVERT_TO_STR,
    "to_bln": TokenType.CONVERT_TO_BLN,
    "to_flt": TokenType.CONVERT_TO_FLT,

    # List types, MISSING TD
    "list_int": TokenType.LIST_INT,
    "list_str": TokenType.LIST_STR,
    "list_bln": TokenType.LIST_BLN,
    "list_flt": TokenType.LIST_FLT,
    "list_chr": TokenType.LIST_CHR,

    # REMOVED
    # "list_int2d": TokenType.LIST_INT2D,
    # "list_str2d": TokenType.LIST_STR2D,
    # "list_bln2d": TokenType.LIST_BLN2D,
    # "list_flt2d": TokenType.LIST_FLT2D,
    # "list_chr2d": TokenType.LIST_CHR2D,
    }

def lookup_ident(ident: str) -> TokenType:
    if ident == "@main_casper":
        return TokenType.MAIN_CASPER
    
    # Prioritize longer, exact matches (e.g., "int[]", "int[][]")
    if ident in KEYWORDS:
        return KEYWORDS[ident]
    
    if "[" in ident:  
        base_ident = ident.split('[')[0]  
        if base_ident in {"int", "flt", "bln", "str", "chr"}:
            return TokenType.ILLEGAL  

    if ident.startswith("@"):
        return TokenType.FUNCTION_NAME
    
    if ident.startswith("$"):
        return TokenType.IDENT

    if ident in {"int", "flt", "bln", "str", "chr"}:
        return TokenType.TYPE

    if ident in {"Day", "Night"}:
        return TokenType.BLN_LIT

    else:
        return TokenType.ILLEGAL
