from Token import Token, TokenType, lookup_ident
from Delimiters import Delimiters
from KeywordDelimiters import KEYWORD_DELIMITERS

class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source  # current code
        self.position: int = -1  #starting position (starts at -1 kasi string index starts at 0)
        self.read_position: int = 0 # next position to be read
        self.line_no: int = 1  
        self.current_char: str | None = None  # variable to hold the current symbol or character
        self.__read_char() #immidiately updates the value once an object is created

    def __read_char(self) -> None:
        """Reads the next character in the source input."""
        if self.read_position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.read_position] #reads the character and pass to the current char variable
        self.position = self.read_position #updates the current position
        self.read_position += 1 #ready for reading the next char

    def __skip_whitespace(self) -> None:
        """Skips whitespace but does not skip newlines."""
        while self.current_char in [' ', '\t', '\r']:
            self.__read_char()

    def __new_token(self, tt: TokenType, literal: any) -> Token:
        """Creates and returns a new token."""
        return Token(type=tt, literal=literal, line_no=self.line_no, position=self.position)

    def __is_digit(self, ch: str) -> bool:
        """Checks if the character is a digit."""
        return '0' <= ch <= '9'

    def __is_letter(self, ch: str) -> bool:
        """Checks if the character is a letter or valid identifier character."""
        return 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch == '_'

    def __read_number(self) -> Token:
        """Reads a number from the input and returns a Token."""
        start_pos = self.position
        dot_count = 0
        output = ""
        integer_part = ""
        decimal_part = ""
        is_decimal = False

        while self.current_char is not None and (self.__is_digit(self.current_char) or self.current_char == '.'):
            if self.current_char == '.':
                dot_count += 1
                if dot_count > 1:
           
                    self.__skip_invalid_characters()
                    return self.__new_token(TokenType.ILLEGAL, self.source[start_pos:self.position])
                is_decimal = True  
            else:
                if not is_decimal:
                    integer_part += self.current_char
                    if len(integer_part) > 9:
                        self.__skip_invalid_characters()
                        return self.__new_token(TokenType.ILLEGAL, self.source[start_pos:self.position])
                else:
                    decimal_part += self.current_char
                    if len(decimal_part) > 9:
                        self.__skip_invalid_characters()
                        return self.__new_token(TokenType.ILLEGAL, self.source[start_pos:self.position])

            output += self.current_char
            self.__read_char()

        # Check if it's an integer or float based on the presence of a dot
        if dot_count == 0:
            return self.__new_token(TokenType.INT_LIT, int(output))
        return self.__new_token(TokenType.FLT_LIT, float(output))


    # LOOKAHEAD
    def __peek_char(self) -> str | None:
        """Peeks at the next character without advancing the lexer."""
        if self.read_position >= len(self.source):
            return None
        return self.source[self.read_position]

    def __skip_whitespace(self) -> None:
        """Skips whitespace but does not skip newlines."""
        while self.current_char in [' ', '\t', '\r']:
            self.__read_char()

    def __new_token(self, tt: TokenType, literal: str) -> Token:
        """Creates and returns a new token."""
        # self.__read_char()
        return Token(type=tt, literal=literal, line_no=self.line_no, position=self.position)
        


    # OKAY NA TO BAI
    def __read_identifier_or_keyword(self) -> Token:
        """Reads an identifier or keyword and validates its delimiter."""
        start_pos = self.position
        is_valid = True  # Flag to track validity

        # IDENTIFIERS - $ or @
        if self.current_char in {'$', '@'}:
            self.__read_char()  

            # use VALID_ID_SYM
            while self.current_char:
                # PROBLEM : may prob sa mga gumagamit ng [], gawan ng delimiter ang identifiers dapat kasama ang [] para ma tokenize separately
                if self.current_char in Delimiters.VALID_ID_SYM:
                    self.__read_char()
                else:
                    if self.current_char.isspace():
                        break  
                    is_valid = False
                    self.__read_char()  # Consume the invalid character)  
        else:
            # KEYWORDS
            while self.current_char and (
                # PROBLEM : may prob sa mga gumagamit ng [], hindi siya nacocount as delimiter
                Delimiters.is_valid_identifier_char(self.current_char) or self.current_char in {'[', ']'}
            ):
                    self.__read_char()

        identifier = self.source[start_pos:self.position]

        # invalid token = ILLEGAL
        if not is_valid:
            return self.__new_token(TokenType.ILLEGAL, identifier)

        token_type = lookup_ident(identifier)

        # Specific logic for the "BIRTH" keyword
        if token_type == TokenType.BIRTH or token_type == TokenType.SKIP or token_type == TokenType.STOP:
            next_char = self.__peek_char()
            valid_delims = KEYWORD_DELIMITERS.get("BIRTH", set())

            # Allow both newline and other valid delimiters for BIRTH
            if next_char == '\n':
                return self.__new_token(token_type, identifier)
            else:
                return self.__new_token(TokenType.ILLEGAL, identifier)
            
        # General keyword validation for other keywords
        if token_type != TokenType.IDENT:
            valid_delims = KEYWORD_DELIMITERS.get(token_type.name, set())
            if self.current_char in valid_delims:
                return self.__new_token(token_type, identifier)
            else:
                return self.__new_token(TokenType.ILLEGAL, identifier)

        # Handle as an illegal identifier if it doesn't start with $ or @
        if not identifier.startswith(('$', '@')):
    
            return self.__new_token(TokenType.ILLEGAL, identifier)

        # Otherwise, return the identifier token
        return self.__new_token(TokenType.IDENT, identifier)





    def __read_number(self) -> Token:
        """Reads a number (integer or float) with up to 9 digits in each part."""
        start_pos = self.position
        dot_count = 0

        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                dot_count += 1
                if dot_count > 1:
                    break
            self.__read_char()

        literal = self.source[start_pos:self.position]
        if dot_count == 0:
            return self.__new_token(TokenType.INT_LIT, literal)
        return self.__new_token(TokenType.FLT_LIT, literal)

    def __read_string(self) -> str:
        """Reads a string literal enclosed in double quotes."""
        self.__read_char()  # Skip the opening quote
        start_pos = self.position
        
        while self.current_char and self.current_char != '"':
            if self.current_char == '\n':  # Strings cannot span multiple lines
                break
            self.__read_char()

        literal = self.source[start_pos:self.position]
        if self.current_char == '"':
            self.__read_char()  # Consume closing quote
        return literal

    def __read_char_literal(self) -> str:
        """Reads a character literal enclosed in single quotes."""
        self.__read_char()  # Skip the opening single quote
        start_pos = self.position

        # Read the character inside the single quotes
        if self.current_char and self.current_char != "'":
            self.__read_char()

        literal = self.source[start_pos:self.position]

        # Check and consume the closing single quote
        if self.current_char == "'":
            self.__read_char()
        else:
            # If no closing single quote, mark it as incomplete
            return None

        # Ensure the literal is only a single character
        if len(literal) != 1:
            return None

        return literal
    
    def __is_valid_delimiter(self, token_type: TokenType) -> bool:
        """
        Validates if the next character after a token is a valid delimiter.
        
        :param token_type: The type of the token being validated.
        :return: True if the next character is a valid delimiter, False otherwise.
        """
        print("current token: " , self.current_char)
        print("token type: ", token_type.name)
        valid_delims = KEYWORD_DELIMITERS.get(token_type.name)
        print("valid delims: ",valid_delims)
        next_char = self.__peek_char()
        print("next char: ",next_char)
        return next_char in valid_delims
    
    def __skip_invalid_characters(self) -> None:
        """Skips invalid characters until a valid delimiter is found."""
        while self.current_char and not self.current_char.isspace():
            self.__read_char()

    def __return_illegal_token(self) -> Token:
        """Returns an illegal token for invalid characters."""
        self.__skip_invalid_characters()
        self.__read_char()

        return self.__new_token(TokenType.ILLEGAL, self.source)
    
    def next_token(self) -> Token:
        """Returns the next token."""
        self.__skip_whitespace()

        if self.current_char is None:
            return self.__new_token(TokenType.EOF, "")
        
        # NEW LINE TOKEN
        if self.current_char == '\n':
            self.line_no += 1  # Increment line number for tracking
            self.__read_char()  # Consume the newline character
            return self.__new_token(TokenType.NEWLINE, "\\n")  # Return newline token


        if self.current_char.isalpha() or self.current_char in {'$', '@'}:
            return self.__read_identifier_or_keyword()

        if self.current_char.isdigit():
            return self.__read_number()

        if self.current_char == '"':
            literal = self.__read_string()
            return self.__new_token(TokenType.STR_LIT, literal)
        
        if self.current_char == "'":
            literal = self.__read_char_literal()
            return self.__new_token(TokenType.CHR_LIT, literal)

        # Handle single-character tokens and illegal characters
        match self.current_char:

            # ARITHMETIC OPERATORS & ASSIGNMENT OPERATORS

            # Token Creation for +, +=, ++
            case '+':
                if self.__peek_char() == '+':  # Handle '++'
                    self.__read_char()  # Consume the first '+'
                    
                    print("after seconf read: ", self.current_char)  # Second '+'
                    if self.__is_valid_delimiter(TokenType.PLUS_PLUS):  # Validate delimiter
                        self.__read_char()  # Consume the second '+'
                        return self.__new_token(TokenType.PLUS_PLUS, "++")
                    
                    # Skip the invalid character and consume until a valid point
                    return self.__return_illegal_token()
                
                elif self.__peek_char() == '=':  # Handle '+='
                    self.__read_char()  # Consume the first '+'
                    
                    if  self.__is_valid_delimiter(TokenType.PLUS_EQ):  # Validate delimiter
                        self.__read_char() # Consume the '='
                        return self.__new_token(TokenType.PLUS_EQ, "+=")
                    return self.__return_illegal_token()
                
                # Handles single '+'
                if self.__is_valid_delimiter(TokenType.PLUS):
                    return self.__consume_single_char_token(TokenType.PLUS)
                return self.__return_illegal_token()
            
            # Token Creation for -, -=, --
            case '-':
                if self.__peek_char() == '-':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.MINUS_MINUS):
                        self.__read_char()
                        return self.__new_token(TokenType.MINUS_MINUS, "--")
                    return self.__return_illegal_token()
                elif self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.MINUS_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.MINUS_EQ, "-=")
                    return self.__return_illegal_token()
                # Single -
                if self.__is_valid_delimiter(TokenType.MINUS):
                    return self.__consume_single_char_token(TokenType.MINUS)
                return self.__return_illegal_token()

            # Token Creation for *, *=, **
            case '*':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.MUL_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.MUL_EQ, "*=")
                    return self.__return_illegal_token()
                elif self.__peek_char == '*':
                    if self.__is_valid_delimiter(TokenType.EXPONENT):
                        self.__read_char()
                        return self.__new_token(TokenType.EXPONENT, "**")
                    return self.__return_illegal_token()
                if self.__is_valid_delimiter(TokenType.MULTIPLY):
                    return self.__consume_single_char_token(TokenType.MULTIPLY)
                return self.__return_illegal_token()          


            # Token Creation for /, /=
            case '/':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.DIV_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.DIV_EQ, "*/=")
                    return self.__return_illegal_token()
                if self.__is_valid_delimiter(TokenType.DIVISION):
                    return self.__consume_single_char_token(TokenType.DIVISION)
                return self.__return_illegal_token() 
                   
            # Token Creation for Modulo (%, %=)
            case '%':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.MOD_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.MOD_EQ, "%=")
                    return self.__return_illegal_token()
                if self.__is_valid_delimiter(TokenType.MODULO):
                    return self.__consume_single_char_token(TokenType.MODULO)
                return self.__return_illegal_token()
            

            # Token Creation for =, ==
            case '=':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.EQ_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.EQ_EQ, "==")
                    return self.__return_illegal_token()
                if self.__is_valid_delimiter(TokenType.EQ):
                    return self.__consume_single_char_token(TokenType.EQ)
                return self.__return_illegal_token()

            # COMPARISON OPERATORS
            
            # Token Creation for Less than, Less than Equals (<, <=)
            case '<':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.LT_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.LT_EQ, "<=")
                    return self.__return_illegal_token()
                if self.__is_valid_delimiter(TokenType.LT):
                    return self.__consume_single_char_token(TokenType.LT)
                return self.__return_illegal_token()
            
            # Token Creation for Greater than, Greater than Equals (<, <=)
            case '>':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.GT_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.GT_EQ, ">=")
                    return self.__return_illegal_token()
                if self.__is_valid_delimiter(TokenType.GT):
                    return self.__consume_single_char_token(TokenType.GT)
                return self.__return_illegal_token()
                       
            # Token Creation for Not,  Not Equals (!, !=)
            case '!':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.NOT_EQ, "!=")
                return self.__consume_single_char_token(TokenType.NOT)
                
            # LOGICAL OPERATORS

            # Token Creation for AND (&&)
            case '&':
                if self.__peek_char() == '&':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.AND, "&&")   
                return self.__consume_single_char_token(TokenType.ILLEGAL)
            
            # Token Creation for OR (||)
            case '|':
                if self.__peek_char() == '|':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.OR, "||")   
                return self.__consume_single_char_token(TokenType.ILLEGAL)
            
            # Token Creation NEGATIVE OP/TILDE
            case '~':
                return self.__consume_single_char_token(TokenType.TILDE)
                

            case '(': return self.__consume_single_char_token(TokenType.LPAREN)
            case ')': return self.__consume_single_char_token(TokenType.RPAREN)
            case '[': return self.__consume_single_char_token(TokenType.LBRACKET)
            case ']': return self.__consume_single_char_token(TokenType.RBRACKET)
            case '{': return self.__consume_single_char_token(TokenType.LBRACE)
            case '}': return self.__consume_single_char_token(TokenType.RBRACE)
            case ',': return self.__consume_single_char_token(TokenType.COMMA)
            case ';': return self.__consume_single_char_token(TokenType.SEMICOLON)
            case ':': return self.__consume_single_char_token(TokenType.COLON)

            case _:
                tok = self.__new_token(TokenType.ILLEGAL, self.current_char)
                self.__read_char()
                return tok

    def __consume_single_char_token(self, token_type: TokenType) -> Token:
        """Helper to return a token for a single character."""
        tok = self.__new_token(token_type, self.current_char)
        self.__read_char()
        return tok


    