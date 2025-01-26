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

    def __read_identifier_or_keyword(self) -> Token:
        """Reads an identifier or keyword and validates its delimiter."""
        start_pos = self.position
        next_char = None 

        while self.current_char and Delimiters.is_valid_identifier_char(self.current_char):
            next_char = self.__peek_char() 
            self.__read_char()  # Advance to the next character

        identifier = self.source[start_pos:self.position]
        token_type = lookup_ident(identifier)

        if token_type != TokenType.IDENT:  

            valid_delims = KEYWORD_DELIMITERS.get(token_type.name, set())

            if next_char in valid_delims:
                return self.__new_token(token_type, identifier)
            else:
                return self.__new_token(TokenType.ILLEGAL, identifier)

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
