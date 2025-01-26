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
    # Arithmetic Symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    DOUBLE_ASTERISK = "DOUBLE_ASTERISK"

    SLASH = "SLASH"
    DOUBLE_SLASH = "DOUBLE_SLASH"
    POW = "POW"
    TILDE = "TILDE"

    # Prefix Symbols
    BANG = "BANG"
    
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
    GLOBAL = "GLOBAL"
    # STRUCTURE = "STRUCTURE"
    DAY = "DAY"
    NIGHT = "NIGHT"
    MEASURE = "MEASURE"
    IN = "IN"
    NEWLINE = "NEWLINE"
    SEMICOLON = ";"
    COLON = ":"
    MOD = "%"
    AND = "&&"
    OR = "||"

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
        return f"Token[{self.type} : {self.literal} : Line {self.line_no} : Position {self.position}]"
    
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
    "GLOBAL": TokenType.GLOBAL,
    "Day": TokenType.DAY,
    "Night": TokenType.NIGHT,
    "day": TokenType.DAY,
    "night": TokenType.NIGHT,
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
    "function_list_int_1D": TokenType.FUNCTION_LIST_INT,
    "function_list_str_1D": TokenType.FUNCTION_LIST_STR,
    "function_list_bln_1D": TokenType.FUNCTION_LIST_BLN,
    "function_list_flt_1D": TokenType.FUNCTION_LIST_FLT,
    "function_list_chr_1D": TokenType.FUNCTION_LIST_CHR,
    "function_list_int_2D": TokenType.FUNCTION_LIST_INT2D,
    "function_list_str_2D": TokenType.FUNCTION_LIST_STR2D,
    "function_list_bln_2D": TokenType.FUNCTION_LIST_BLN2D,
    "function_list_flt_2D": TokenType.FUNCTION_LIST_FLT2D,
    "function_list_chr_2D": TokenType.FUNCTION_LIST_CHR2D,

    # Type conversion keywords
    "to_int": TokenType.CONVERT_TO_INT,
    "to_str": TokenType.CONVERT_TO_STR,
    "to_bln": TokenType.CONVERT_TO_BLN,
    "to_flt": TokenType.CONVERT_TO_FLT,

    # List types, MISSING TD
    "int_1D": TokenType.LIST_INT,
    "str_1D": TokenType.LIST_STR,
    "bln_1D": TokenType.LIST_BLN,
    "flt_1D": TokenType.LIST_FLT,
    "chr_1D": TokenType.LIST_CHR,
    "int_2D": TokenType.LIST_INT2D,
    "str_2D": TokenType.LIST_STR2D,
    "bln_2D": TokenType.LIST_BLN2D,
    "flt_2D": TokenType.LIST_FLT2D,
    "chr_2D": TokenType.LIST_CHR2D,
    }

def lookup_ident(ident: str) -> TokenType:
    # Check for keywords
    tt: TokenType | None = KEYWORDS.get(ident)
    if tt is not None:
        return tt
    
    # Check for function names starting with "@"
    if ident.startswith("@"):
        return TokenType.FUNCTION_NAME

    # Check for type keywords
    if ident in {"int", "flt", "bln", "str", "chr"}:
        return TokenType.TYPE

    # Handle boolean literals
    if ident in {"Day", "Night"}:
        return TokenType.BLN_LIT

    return TokenType.IDENT
