from Token import Token, TokenType, lookup_ident
from Delimiters import Delimiters
from KeywordDelimiters import KEYWORD_DELIMITERS

class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position: int = -1
        self.read_position: int = 0
        self.line_no: int = 1
        self.current_char: str | None = None
        self.__read_char()

    def __read_char(self) -> None:
        """Reads the next character in the source input."""
        if self.read_position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.read_position]
        self.position = self.read_position
        self.read_position += 1

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
    def next_token(self) -> Token:
        """Returns the next token."""
        self.__skip_whitespace()

        if self.current_char is None:
            return self.__new_token(TokenType.EOF, "")
        
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
            case '+':
                if self.__peek_char() == '+':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.PLUS_PLUS, "++")
                elif self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.PLUS_EQ, "+=")
                return self.__new_token(TokenType.PLUS, "+")

            case '-':
                if self.__peek_char() == '-':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.MINUS_MINUS, "--")
                elif self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.MINUS_EQ, "-=")
                return self.__new_token(TokenType.MINUS, "-")

            case '=':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.EQ_EQ, "==")
                return self.__new_token(TokenType.EQ, "=")

            case '<':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.LT_EQ, "<=")
                return self.__new_token(TokenType.LT, "<")

            case '>':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.GT_EQ, ">=")
                return self.__new_token(TokenType.GT, ">")

            case '!':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.NOT_EQ, "!=")
                else:
                    return self.__new_token(TokenType.BANG, "!")

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


    