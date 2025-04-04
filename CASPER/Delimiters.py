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
    LOGEXP = {'|', '&'}
    COMPARATOR = {'==', '!', '!=', '<', '>', '<=', '>='}
    NULL = {None, ''}
    COMMENT = {'<<', '---'}
    ASCII = {'ascii code'} # mema
    SPX_CHAR1 = {'!', '@', '#', '$', '%', '^', '&', '*'}
    SPX_CHAR2 = {'(', ')', '[', ']', '{', '}', '<', '>'}
    SPX_CHAR3 = {'.', ',', ':', ';', '-', '_', '=', '+'}
    SPX_CHAR4 = {'`', '~', '|', '/', '?', '!', '"'}
    SPX_CHAR5 = {'\''}
    SPX_CHAR6 = {'\'', '"', '`', '~', '^', '_', '-'}
    SPECIAL = SPX_CHAR1 | SPX_CHAR2 | SPX_CHAR3 | SPX_CHAR4 | SPX_CHAR5 | SPX_CHAR6
    NEWLINE = {'\r'}
    STRING_FORM = {'"', '"'}
    CARRIAGE_RETURN = {'\r'}
    

    # Delimiters
    DELIM_ID = OPERATORS | SPACE | NEWLINE | CARRIAGE_RETURN | NULL | {'=', '!', '>', '<', '(', ')', '[', ']', ','}
    DEL1 = SPACE | {'{'}  | NEWLINE
    DEL2 = SPACE | {'('}  | NEWLINE
    DEL3 = SPACE | NUM | BOOLEAN | {'(', '$', '|'} # logical ops
    DEL4 = SPACE | NUM | {'(', '$', '\'', '"', None,'', '\r'} # plus delim
    DEL5 = SPACE | ALPHANUM |{'$', '(', '@','',None,'\r', ''}  # minus, multiply, divide, modulo delims, all assignment ops
    DEL6 = NUM | {'$', '(', '\''} #prefix | **
    DEL7 =  SPACE | ALPHANUM | NEWLINE | {'$', '@', '"', '(', '{', '\'', ')','['} # open LPAREN (
    DEL8 = SPACE | NEWLINE | ALPHANUM | NULL | {'+', '-', '*', '/', '{', '(', ')', ']', '}', ',','$', '@','|','&', ';'} # closing RPAREN )
    DEL9 = SPACE | NEWLINE | {'(', '{', '$', '@', '"'} # opening LBRACE {
    DEL10 = SPACE | NEWLINE | NULL | OPERATORS | COMPARATOR | LOGEXP | {'"', '(', '{', '[',']',')', ',', ':' ,';','='} # closing RBRACE }
    DEL11 = SPACE | NEWLINE | NULL | {',', '(', '{', '[', '+', ')',']'}
    DEL12 = SPACE | NEWLINE | NULL | {'\r', '$'}
    DEL13 = SPACE | NULL | {')', '\'', None,'','\r', ''} # postfix
    DEL14 = SPACE | ALPHA
    DEL15 = SPACE | NEWLINE | ALPHANUM | {'[', ']', '"', '$', '\''} # L bracket
    DEL16 = SPACE | NEWLINE | {'[', ']', '$', '@', ',', '='} 
    DEL17 = SPACE | NEWLINE | NULL | OPERATORS |{',', ')', ']','.','[','='} # R bracket
    DEL18 = {'('}
    DEL19 = {'['}
    identifier_del = OPERATORS | SPACE | NEWLINE | CARRIAGE_RETURN | NULL | {'<', '-', '+', '*', '/', '%', '=', '<', '>', '!', '(', ')', '[', ']', ',' , '{', '}','&','|',';', '.'} 
    DEL20 = NULL | {'p','s'}


    # Check if a character is a valid delimiter
    @classmethod
    def is_delimiter(cls, char):
    
        return char in cls.DELIM_ID

    # Check if a character is valid for identifiers
    @classmethod
    def is_valid_identifier_char(cls, char):
       
        return char in cls.VALID_ID_SYM
