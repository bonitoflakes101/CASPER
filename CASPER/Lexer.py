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
            return self.__new_token(TokenType.INT_LIT, int(output))
        return self.__new_token(TokenType.FLT_LIT, float(output))
    
    def __peek_char(self) -> str | None:
        """Peeks at the next character without advancing the lexer."""
        if self.read_position >= len(self.source):
            return None
        return self.source[self.read_position]


    def __read_identifier(self) -> str:
        """Reads an identifier or keyword."""
        start_pos = self.position

        # Allow identifiers to start with $
        if self.current_char == '$' or self.current_char == '@':
            self.__read_char()  # Consume the $

        # Continue reading valid identifier characters
        special_chars = "!\"#%&'()*+,-./:;<=>?@\\^_`{|}~"

        while self.current_char is not None and (
            self.__is_letter(self.current_char)
            or self.current_char.isdigit()
            or self.current_char in ['_', '[', ']', '$']  # Adding allowed special characters
            or self.current_char in special_chars  # Add all special characters here
        ):
            
            self.__read_char()

        return self.source[start_pos:self.position]

    def __skip_invalid_characters(self) -> None:
        """Skips characters after an illegal token."""
        while self.current_char not in [' ', '\n', None]:
            self.__read_char()

    def __skip_single_line_comment(self) -> None:
        """Skips a single-line comment."""
        while self.current_char is not None and self.current_char != '\n':
            self.__read_char()


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
            case '<':
                if self.__peek_char() == '<':
                    self.__read_char()  # Consume the first '<'
                    self.__read_char()  # Consume the second '<'
                    self.__skip_single_line_comment()
                    return self.next_token()  # Skip and get the next token
                elif self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.LT_EQ, "<=")
                return self.__consume_single_char_token(TokenType.LT)
            case '+':
                if self.__peek_char() == '=':
                    self.__read_char()  # Advance for '='
                    self.__read_char()  # Advance after creating token
                    return self.__new_token(TokenType.PLUS_EQ, "+=")
                elif self.__peek_char() == '+':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.PLUS_PLUS, "++")
                return self.__consume_single_char_token(TokenType.PLUS)
            case '-':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.MINUS_EQ, "-=")
                elif self.__peek_char() == '-':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.MINUS_MINUS, "--")
                return self.__consume_single_char_token(TokenType.MINUS)
            case '=':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.EQ_EQ, "==")
                return self.__consume_single_char_token(TokenType.EQ)
            case '!':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.NOT_EQ, "!=")
                return self.__consume_single_char_token(TokenType.BANG)
            case '>':
                if self.__peek_char() == '=':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.GT_EQ, ">=")
                return self.__consume_single_char_token(TokenType.GT)
            case '/':
                if self.__peek_char() == '/':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.DOUBLE_SLASH, "//")
                return self.__consume_single_char_token(TokenType.SLASH)
            case '*':
                if self.__peek_char() == '*':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.DOUBLE_ASTERISK, "**")
                return self.__consume_single_char_token(TokenType.ASTERISK)
            case '&':
                if self.__peek_char() == '&':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.AND, "&&")
                return self.__consume_single_char_token(TokenType.ILLEGAL)        
            case '|':
                if self.__peek_char() == '|':
                    self.__read_char()
                    self.__read_char()
                    return self.__new_token(TokenType.OR, "||")
                return self.__consume_single_char_token(TokenType.ILLEGAL)
            case '[':
                self.__read_char()
                return self.__new_token(TokenType.LBRACKET, "[")
            case ']':
                self.__read_char()
                return self.__new_token(TokenType.RBRACKET, "]")
            case ':': return self.__consume_single_char_token(TokenType.COLON)
            case ';': return self.__consume_single_char_token(TokenType.SEMICOLON)
            case ',': return self.__consume_single_char_token(TokenType.COMMA)
            case '(': return self.__consume_single_char_token(TokenType.LPAREN)
            case ')': return self.__consume_single_char_token(TokenType.RPAREN)
            case '{': return self.__consume_single_char_token(TokenType.LBRACE)
            case '}': return self.__consume_single_char_token(TokenType.RBRACE)
            case '%': return self.__consume_single_char_token(TokenType.MOD)
            
            case '~':  # Handle the tilde token
                return self.__consume_single_char_token(TokenType.TILDE)
            case '"': return self.__new_token(TokenType.STR_LIT, self.__read_string())
            case '@':
            
                identifier = self.__read_identifier()
                if "@" in identifier[1:]:
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                if identifier == "@":
                    return self.__new_token(TokenType.ILLEGAL, identifier)
                return self.__new_token(TokenType.IDENT, f"{identifier}")

            case _:
                # Handling identifiers starting with $
                if self.current_char == '$':
                    start_position = self.position
                    identifier = self.__read_identifier()
                    print(len(identifier))

                    # Validate the identifier (check for length and allowed characters)
                    if len(identifier) > 16:
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                    special_chars = set("!\"#%&'()*+,-./:;<=>?@\\^_`{|}~")

                    if any(char in special_chars for char in identifier.replace('[]', '')):
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                    if "$" in identifier[1:]:
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                    if identifier == "$":
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                    if '[]' in identifier:
                        if identifier.endswith('[]'):
                            if '[' in identifier[:-2] or ']' in identifier[:-2]:
                                return self.__new_token(TokenType.ILLEGAL, identifier)
                        else:
                            return self.__new_token(TokenType.ILLEGAL, identifier)
                    elif '[' in identifier or ']' in identifier:
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                    # Handle array access like $fruits[0]
                    tokens = [self.__new_token(TokenType.IDENT, identifier)]
                    while self.__peek_char() == '[':
                        self.__read_char()  
                        tokens.append(self.__new_token(TokenType.LBRACKET, "["))
                        index = self.__read_number()
                        tokens.append(index)
                        self.__read_char()  
                        tokens.append(self.__new_token(TokenType.RBRACKET, "]"))
                    return tokens

                # Handle keywords and regular identifiers (that do not start with $)
                elif self.__is_letter(self.current_char):
                    identifier = self.__read_identifier()

                    # Check for types like str[] (TokenType.TYPE)
                    if self.__peek_char() == '[':
                        self.__read_char()  
                        if self.__peek_char() == ']':
                            self.__read_char()  
                            return self.__new_token(TokenType.TYPE, f"{identifier}[]")

                    # Check if identifier is a keyword
                    token_type = lookup_ident(identifier)
                    if token_type != TokenType.IDENT:  # It's a keyword
                        # If next character is not space, square bracket, or newline, it's illegal
                        if self.current_char not in [' ', '[', '\n']:
                            self.__skip_invalid_characters()
                            return self.__new_token(TokenType.ILLEGAL, identifier)
                        return self.__new_token(token_type, identifier)
                    else:  # Not a keyword
                        return self.__new_token(TokenType.ILLEGAL, identifier)

                # Handle numeric literals
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
