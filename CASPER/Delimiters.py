class Delimiters:
    ZERO = {'0'}
    ALPHA_UP = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    ALPHA_DOWN = set('abcdefghijklmnopqrstuvwxyz')
    ALPHA = ALPHA_UP | ALPHA_DOWN
    DIGITS = set('123456789')
    NUM = ZERO | DIGITS
    ALPHANUM = ALPHA | NUM
    UNDERSCORE = {'_'}
    SPACE = {' '}  
    VALID_ID_SYM = ALPHANUM | UNDERSCORE
    BOOLEAN = {'Day', 'Night'}
    OPERATORS = {'+', '-', '*', '/', '%'}
    LOGEXP = {'||', '&&'}
    COMPARATOR = {'==', '!', '!=', '<', '>', '<=', '>='}
    NULL = {None}
    COMMENT = {'<<', '---'}
    ASCII = {'ascii code'} # mema
    SPX_CHAR1 = {'!', '@', '#', '$', '%', '^', '&', '*'}
    SPX_CHAR2 = {'(', ')', '[', ']', '{', '}', '<', '>'}
    SPX_CHAR3 = {'.', ',', ':', ';', '-', '_', '=', '+'}
    SPX_CHAR4 = {'`', '~', '|', '/', '?', '!', '"'}
    SPX_CHAR5 = {'\''}
    SPX_CHAR6 = {'\'', '"', '`', '~', '^', '_', '-'}
    SPECIAL = SPX_CHAR1 | SPX_CHAR2 | SPX_CHAR3 | SPX_CHAR4 | SPX_CHAR5 | SPX_CHAR6
    NEWLINE = {'\n'}
    STRING_FORM = {'"', '"'}
    

    # Delimiters
    DELIM_ID = OPERATORS | SPACE | NEWLINE | {'=', '!', '>', '<', '(', ')', '[', ']', ','}
    DEL1 = SPACE | {'{'}
    DEL2 = SPACE | {'('}
    DEL3 = {'{', '\n'}
    DEL4 = SPACE | NEWLINE | ALPHANUM
    DEL5 = SPACE | ALPHANUM
    DEL6 = SPACE | NULL | ALPHANUM | {'"', '[', ']', '\''}
    DEL7 = SPACE | NEWLINE | {'+', '-', '*', '/', '.', '{', '(', ')', ']', '}', ','}
    DEL8 = ALPHANUM | {',', '+', '-', '*', '/'}
    DEL9 = SPACE | {'(', '{'} | ALPHANUM | {'}'}
    DEL10 = SPACE | {',', '(', '{', '[', '+', '-', '*', '/', '<', '>', '=', ']', ')', '}'}
    DEL11 = SPACE | NEWLINE | {',', '(', '{', '[', '+'}
    DEL12 = SPACE | NEWLINE | NULL
    DEL13 = SPACE | NULL | {')', '\n'}
    DEL14 = SPACE | ALPHA
    DEL15 = SPACE | {')', '"'} | ALPHANUM | {'(', '[', '\''}
    DEL16 = SPACE | {'}', '"', '\n'}
    DEL17 = SPACE | {',', ')', ']'}
    DEL18 = {'('}
    DEL19 = {'['}
    identifier_del = SPACE | {'<', '-', '+', '*', '/', '%', '=', '<', '>', '!', '(', ')', '[', ']', ',' , '{', '}'} 
   


    # Check if a character is a valid delimiter
    @classmethod
    def is_delimiter(cls, char):
    
        return char in cls.DELIM_ID

    # Check if a character is valid for identifiers
    @classmethod
    def is_valid_identifier_char(cls, char):
       
        return char in cls.VALID_ID_SYM
