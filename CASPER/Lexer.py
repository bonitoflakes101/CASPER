from Token import Token, TokenType, lookup_ident
from typing import Any


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

    def __skip_whitespace(self) -> None:
        """Skips whitespace but does not skip newlines."""
        while self.current_char in [' ', '\t', '\r']:
            self.__read_char()

    def __new_token(self, tt: TokenType, literal: Any) -> Token:
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

        while self.current_char is not None and (self.__is_digit(self.current_char) or self.current_char == '.'):
            if self.current_char == '.':
                dot_count += 1
                if dot_count > 1:
                    return self.__new_token(TokenType.ILLEGAL, self.source[start_pos:self.position])
            output += self.current_char
            self.__read_char()

        if dot_count == 0:
            return self.__new_token(TokenType.INT, int(output))
        return self.__new_token(TokenType.FLT, float(output))

    def __read_identifier(self) -> str:
        """Reads an identifier or keyword."""
        start_pos = self.position

        # Allow identifiers to start with $
        if self.current_char == '$':
            self.__read_char()  # Consume the $

        # Continue reading valid identifier characters
        while self.current_char is not None and (
            self.__is_letter(self.current_char)
            or self.current_char.isdigit()
            or self.current_char in ['_', '[', ']', '*']
        ):
            self.__read_char()

        return self.source[start_pos:self.position]

    def next_token(self) -> Token:
        """Returns the next token."""
        self.__skip_whitespace()

        # Handles newline
        if self.current_char == '\n':
            self.line_no += 1
            self.__read_char()
            return self.__new_token(TokenType.NEWLINE, "\\n")

        # Determines end of file
        if self.current_char is None:
            return self.__new_token(TokenType.EOF, "")

        # Handles symbols, identifiers, and keywords
        match self.current_char:
            case '+': return self.__consume_single_char_token(TokenType.PLUS)
            case '-': return self.__consume_single_char_token(TokenType.MINUS)
            case '*': return self.__consume_single_char_token(TokenType.ASTERISK)
            case '/': return self.__consume_single_char_token(TokenType.SLASH)
            case '^': return self.__consume_single_char_token(TokenType.POW)
            case '%': return self.__consume_single_char_token(TokenType.MODULUS)
            case '<': return self.__consume_single_char_token(TokenType.LT)
            case '>': return self.__consume_single_char_token(TokenType.GT)
            case '=': return self.__consume_single_char_token(TokenType.EQ)
            case '!': return self.__consume_single_char_token(TokenType.BANG)
            case ':': return self.__consume_single_char_token(TokenType.COLON)
            case ';': return self.__consume_single_char_token(TokenType.SEMICOLON)
            case ',': return self.__consume_single_char_token(TokenType.COMMA)
            case '(': return self.__consume_single_char_token(TokenType.LPAREN)
            case ')': return self.__consume_single_char_token(TokenType.RPAREN)
            case '{': return self.__consume_single_char_token(TokenType.LBRACE)
            case '}': return self.__consume_single_char_token(TokenType.RBRACE)
            case '"': return self.__new_token(TokenType.STR, self.__read_string())
            case _:
                if self.__is_letter(self.current_char):  # Potential keyword or illegal token
                    identifier = self.__read_identifier()  # Read the full identifier
                    token_type = lookup_ident(identifier)
                    if token_type != TokenType.IDENT:  # It's a keyword
                        return self.__new_token(tt=token_type, literal=identifier)
                    else:  # Not a keyword, and doesn't have a `$`
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                elif self.current_char == '$':  # Valid identifier starts with $
                    identifier = self.__read_identifier()
                    return self.__new_token(TokenType.IDENT, identifier)

                elif self.__is_digit(self.current_char):
                    return self.__read_number()

                else:
                    # Handle other illegal tokens
                    tok = self.__new_token(TokenType.ILLEGAL, self.current_char)
                    self.__read_char()  # Advance the position
                    return tok
                
                

    def __consume_single_char_token(self, token_type: TokenType) -> Token:
        """Helper to return a token for a single character."""
        tok = self.__new_token(token_type, self.current_char)
        self.__read_char()
        return tok

    def __read_string(self) -> str:
        """Reads a string literal."""
        start_pos = self.position + 1  # Skip the opening quote
        self.__read_char()  # Move past the opening quote
        output = ""

        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\n':  # Strings cannot span multiple lines.
                return ""
            output += self.current_char
            self.__read_char()

        if self.current_char == '"':
            self.__read_char()  # Consume the closing quote
            return output
        return ""
