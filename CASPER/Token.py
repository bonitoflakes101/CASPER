from enum import Enum
from typing import Any

class TokenType(Enum):
    # Special Tokens
    EOF = "EOF"
    ILLEGAL = "ILLEGAL"

    # Data Types
    IDENT = "IDENT"
    INT = "INT"
    FLT = "FLT"
    BLN = "BLN"
    STR = "STR"
    CHR = "CHR"

    # Arithmetic Symbols
    PLUS = "PLUS"
    MINUS = "MINUS"
    ASTERISK = "ASTERISK"
    SLASH = "SLASH"
    DOUBLE_SLASH = "DOUBLE_SLASH"
    POW = "POW"
    MODULUS = "MODULUS"
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
    FUNCTION = "FUNCTION"
    STRUCTURE = "STRUCTURE"
    DAY = "DAY"
    NIGHT = "NIGHT"
    MEASURE = "MEASURE"
    IN = "IN"
    NEWLINE = "NEWLINE"
    SEMICOLON = ";"

    # Typing
    TYPE = "TYPE"

    # Parentheses
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = '{'
    RBRACE = '}'
    LBRACKET = '['
    RBRACKET = ']'

    # Custom Function Syntax
    FUNCTION_NAME = "FUNCTION_NAME"

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
    "function": TokenType.FUNCTION,
    "structure": TokenType.STRUCTURE,
    "Day": TokenType.DAY,
    "Night": TokenType.NIGHT,
    "day": TokenType.DAY,
    "night": TokenType.NIGHT,
    "measure": TokenType.MEASURE,
    "in": TokenType.IN,
    "int": TokenType.INT,
    "flt": TokenType.FLT,
    "bln": TokenType.BLN,
    "str": TokenType.STR,
    "chr": TokenType.CHR,

    # Function keywords
    "function_int": TokenType.FUNCTION,
    "function_str": TokenType.FUNCTION,
    "function_bln": TokenType.FUNCTION,
    "function_flt": TokenType.FUNCTION,
    "function_chr": TokenType.FUNCTION,
    "function_list_int[]": TokenType.FUNCTION,
    "function_list_str[]": TokenType.FUNCTION,
    "function_list_bln[]": TokenType.FUNCTION,
    "function_list_flt[]": TokenType.FUNCTION,
    "function_list_chr[]": TokenType.FUNCTION,
    "function_list_int[][]": TokenType.FUNCTION,
    "function_list_str[][]": TokenType.FUNCTION,
    "function_list_bln[][]": TokenType.FUNCTION,
    "function_list_flt[][]": TokenType.FUNCTION,
    "function_list_chr[][]": TokenType.FUNCTION,

    # Type conversion keywords
    "to_int": TokenType.TYPE,
    "to_str": TokenType.TYPE,
    "to_bln": TokenType.TYPE,
    "to_flt": TokenType.TYPE,

    # List types
    "int[]": TokenType.TYPE,
    "str[]": TokenType.TYPE,
    "bln[]": TokenType.TYPE,
    "flt[]": TokenType.TYPE,
    "chr[]": TokenType.TYPE,
    "int[][]": TokenType.TYPE,
    "str[][]": TokenType.TYPE,
    "bln[][]": TokenType.TYPE,
    "flt[][]": TokenType.TYPE,
    "chr[][]": TokenType.TYPE,
}

def lookup_ident(ident: str) -> TokenType:
    tt: TokenType | None = KEYWORDS.get(ident)
    if tt is not None:
        return tt
    
    if ident.startswith("@"):  # Check for function names starting with @
        return TokenType.FUNCTION_NAME
    
    if ident in {"int", "flt", "bln", "str", "chr"}:
        return TokenType.TYPE
    
    return TokenType.IDENT
