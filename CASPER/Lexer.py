from Token import Token, TokenType, lookup_ident
from Delimiters import Delimiters
from KeywordDelimiters import KEYWORD_DELIMITERS

tokens = [token.name for token in TokenType] 

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
        while self.current_char in [' ', '\t', '\r', '\n']:
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
        """
        Reads a number (integer or float) with up to 9 digits in each part,
        enforcing DEL10 as a delimiter, and returns the token with int/float value.
        """
        start_pos = self.position
        dot_count = 0
        output = ""
        integer_part = ""
        decimal_part = ""
        is_decimal = False

        # Collect digits and optional single dot
        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                dot_count += 1
                if dot_count > 1:
                    # More than one dot => break and treat as ILLEGAL
                    break
                is_decimal = True
            else:
                if not is_decimal:
                    # Building the integer part
                    if len(integer_part) >= 11:
                        # Exceeds 9 digits => ILLEGAL
                        while self.current_char and self.current_char not in Delimiters.DEL10 and self.current_char != '\n':
                            self.__read_char()
                        illegal_literal = self.source[start_pos:self.position]
                        return self.__new_token(TokenType.ILLEGAL, illegal_literal)
                    integer_part += self.current_char
                else:
                    # Building the decimal part
                    if len(decimal_part) >= 11:
                        # Exceeds 9 digits => ILLEGAL
                        while self.current_char and self.current_char not in Delimiters.DEL10 and self.current_char != '\n':
                            self.__read_char()
                        illegal_literal = self.source[start_pos:self.position]
                        return self.__new_token(TokenType.ILLEGAL, illegal_literal)
                    decimal_part += self.current_char

            output += self.current_char
            self.__read_char()

        # After collecting digits, check the next character is a valid delimiter
        if self.current_char not in Delimiters.DEL10:
            # Read until we find a valid delimiter or newline, then treat as ILLEGAL
            while self.current_char and self.current_char not in Delimiters.DEL10 and self.current_char != '\n':
                self.__read_char()
            illegal_literal = self.source[start_pos:self.position]
            return self.__new_token(TokenType.ILLEGAL, illegal_literal)

        # Now produce the numeric token
        if dot_count == 0:
            # It's an integer
            return self.__new_token(TokenType.INT_LIT, int(output))
        else:
            # It's a float
            return self.__new_token(TokenType.FLT_LIT, float(output))



    # LOOKAHEAD
    def __peek_char(self) -> str | None:
        """Peeks at the next character without advancing the lexer."""
        if self.read_position >= len(self.source):
            return None
        return self.source[self.read_position]

    # def __skip_whitespace(self) -> None:
    #     """Skips whitespace including newlines while updating line numbers."""
    #     while self.current_char in [' ', '\t']:
    #         if self.current_char == '\n':
    #             self.line_no += 1  # Update line count
    #         self.__read_char()

    def __new_token(self, tt: TokenType, literal: str, valid_delims=None):
        return Token(
            type=tt,
            literal=literal,
            line_no=self.line_no,
            position=self.position,
            valid_delims=valid_delims
        )




        
    # OKAY NA TO BAI
    def __read_identifier_or_keyword(self) -> Token:
        start_pos = self.position # Position of the first char of the sequence
        
        # IDENTIFIERS - $ or @
        if self.current_char in {'$', '@'}:
            self.__read_char()  # Consume $ or @

            # Ensure the identifier starts with a valid character
            if self.current_char is None or not (self.current_char.isalpha() or self.current_char == '_'):
                # If the first character after $ is invalid, treat it as ILLEGAL
                while self.current_char and self.current_char not in Delimiters.identifier_del and self.current_char != '\\n':
                    self.__read_char()
                illegal_literal = self.source[start_pos:self.position]
            
                # TAMA LANG TO
                return self.__new_token(TokenType.ILLEGAL, illegal_literal)

            # Continue reading the identifier
            while self.current_char and (self.current_char.isalnum() or self.current_char == '_'):
                if Delimiters.is_valid_identifier_char(self.current_char):
                    self.__read_char()
                elif self.current_char in {'$', '@'}:
               
                    # If another $ or @ is encountered mid-identifier, read the whole sequence as ILLEGAL
                    while self.current_char and self.current_char not in Delimiters.identifier_del and self.current_char != '\\n':
                        self.__read_char()
                    illegal_literal = self.source[start_pos:self.position]
                    return self.__new_token(TokenType.ILLEGAL, illegal_literal)
                else:
                    # Stop if a non-identifier character is encountered
                    # if self.__checkIDforAfterBracketsError():
                    #     illegal_literal = self.source[start_pos:self.position]
                    #     return self.__new_token(TokenType.ILLEGAL, illegal_literal)
              
                    break

            # After reading, validate delimiters for identifiers
            identifier = self.source[start_pos:self.position]
            valid_delims = Delimiters.identifier_del 

            # Check if the identifier starts with '@' for FUNCTION_NAME
            if identifier.startswith('@'):
                # If the identifier is the main function token, return MAIN_CASPER.
                if identifier == "@main_casper":
                    if self.current_char in valid_delims:
                        return self.__new_token(TokenType.MAIN_CASPER, identifier)
                    else:
                        while self.current_char and self.current_char not in Delimiters.identifier_del:
                            self.__read_char()
                        illegal_literal = self.source[start_pos:self.position]
                        return self.__return_illegal_token(identifier, valid_delims=valid_delims)
                else:
                    # For any other '@'-prefixed identifier, return FUNCTION_NAME.
                    if self.current_char in valid_delims:
                        return self.__new_token(TokenType.FUNCTION_NAME, identifier)
                    else:
                        while self.current_char and self.current_char not in Delimiters.identifier_del:
                            self.__read_char()
                        illegal_literal = self.source[start_pos:self.position]
                        return self.__return_illegal_token(identifier, valid_delims=valid_delims)

            # Check if the identifier starts with '$' for IDENT
            elif identifier.startswith('$'):
                if self.current_char in Delimiters.identifier_del:
                    return self.__new_token(TokenType.IDENT, identifier)
                else:
                    # If no valid delimiter, treat as ILLEGAL
                    while self.current_char and self.current_char not in Delimiters.identifier_del:
                        self.__read_char()
                    illegal_literal = self.source[start_pos:self.position]
                    return self.__return_illegal_token(identifier, valid_delims=valid_delims)

            # Otherwise, treat as ILLEGAL (e.g. if logic above is incomplete for $/@)
            while self.current_char and self.current_char != ' ':   
                self.__read_char()
            illegal_literal = self.source[start_pos:self.position]
            return self.__new_token(TokenType.ILLEGAL, illegal_literal)
        # For sequences not starting with $ or @ (potential keywords or plain illegal sequences)
        else:
            # Read the full sequence of characters that could form an identifier/keyword
            # self.current_char is the first char (e.g., 'B'), start_pos is its position.
            
            while self.current_char and Delimiters.is_valid_identifier_char(self.current_char):
                self.__read_char()
            
            # 'identifier' is the sequence we just read (e.g., "Birth")
            # self.current_char is now the character *after* this sequence (e.g., ' ' or '{')
            # self.position is the position of this terminating character.
            identifier = self.source[start_pos : self.position] 
            
            token_type_from_lookup = lookup_ident(identifier)

            if token_type_from_lookup == TokenType.ILLEGAL:
                # The sequence 'identifier' (e.g., "Birth") is not a recognized keyword
                # and lookup_ident has confirmed it's ILLEGAL as a whole.
                # Tokenize only its first character as ILLEGAL.
                
                first_char_of_sequence = self.source[start_pos]
                
                tok = Token(type=TokenType.ILLEGAL, 
                            literal=first_char_of_sequence, 
                            line_no=self.line_no, 
                            position=start_pos)
                
                # Reset the lexer's state so that the *next* character
                # to be processed is identifier[1] (the second char of the sequence).
                self.position = start_pos  # Position of the char we just tokenized
                self.read_position = start_pos + 1 # Next read position for char after it
                
                self.__read_char() # Consumes first_char_of_sequence from lexer's perspective,
                                   # sets self.current_char to the next one, and updates positions.
                                   
                return tok
            else:
                # The 'identifier' is a known keyword.
                # token_type_from_lookup is the actual TokenType (e.g., TokenType.BIRTH).
                # Proceed with normal keyword delimiter checking.
                # self.current_char is the character *after* 'identifier'.
                
                token_type = token_type_from_lookup

                # General keyword validation
                # (lookup_ident for non-$/@ returns specific keyword TokenType or ILLEGAL, not IDENT)
                valid_delims = KEYWORD_DELIMITERS.get(token_type.name, set())
                
                if self.current_char in valid_delims:
                    # Keyword followed by a valid delimiter.
                    return self.__new_token(token_type, identifier)
                else:
                    # Keyword is valid, but followed by an invalid delimiter.
                    # Tokenize the keyword. The invalid delimiter will be handled
                    # by the next call to next_token(). (This was the previous edit)
                    return self.__new_token(token_type, identifier)




    def __read_string(self) -> str | None:
        self.__read_char() 
        literal = ""

        while self.current_char is not None and self.current_char != '"':
            if self.current_char == "\\":
                next_char = self.__peek_char()
                escape_sequences = {
                    '"': '"',  
                    "'": "'",  
                    "\\": "\\",  
                    "n": "\n", 
                    "t": "\t",  
                }
                if next_char in escape_sequences:
                    self.__read_char()  # Consume the escape character
                    literal += escape_sequences[next_char]
                else:
                    # Not a valid escape sequence; treat '\' as literal.
                    literal += self.current_char
            else:
                literal += self.current_char  
            
            self.__read_char()

        if self.current_char == '"':
            self.__read_char()  
            if self.current_char in Delimiters.DEL11:
                return literal 
            return None  

        return None


    def __read_char_literal(self) -> str | None:
        """Reads a character literal enclosed in single quotes and returns the character (or None if invalid)."""
        start_pos = self.position  # Store starting position
        self.__read_char()  # Consume the opening single quote

        if self.current_char is None or self.current_char == "'":
            return None  # Mark as ILLEGAL if empty or immediately closed

        literal = ""  # Store the character(s) inside the single quotes

        while self.current_char is not None and self.current_char != "'":
            # Handle escaped single quote (\')
            if self.current_char == "\\" and self.__peek_char() == "'":
                self.__read_char()  # Skip past backslash
                literal += "'"  # Append actual single quote
            else:
                literal += self.current_char  # Append normal character
            
            self.__read_char()

        # If we correctly find a closing quote
        if self.current_char == "'":
            self.__read_char()  # Consume closing quote

            # Check if the next character is a valid delimiter (DEL11)
            if self.current_char in Delimiters.DEL11:
                if len(literal) == 1:
                    return literal  # Return valid single-character literal
                else:
                    return None  # Mark as ILLEGAL if more than one character is found
            else:
                return None  # Mark as ILLEGAL if no valid delimiter after closing quote

        return None  # If no closing quote is found, mark as ILLEGAL



    
    def __is_valid_delimiter(self, token_type: TokenType) -> bool:
        """
        Validates if the next character after a token is a valid delimiter.
        
        :param token_type: The type of the token being validated.
        :return: True if the next character is a valid delimiter, False otherwise.
        """
        # Debugging shit
        prev = self.position-1
        prevChar = self.source[prev]
      
        valid_delims = KEYWORD_DELIMITERS.get(token_type.name)
    


        next_char = self.__peek_char()
       
        return next_char in valid_delims

    def __skip_invalid_characters(self) -> None:
        """Skips invalid characters until a valid delimiter is found."""
        while self.current_char and not self.current_char.isspace():
            self.__read_char()

    def __return_illegal_token(self, literal=None, valid_delims=None) -> Token:
        """
        Returns an ILLEGAL token with optional 'literal' and 'valid_delims'.
        If 'literal' is not provided, it defaults to the current_char.
        """
        if literal is None:
            literal = self.current_char
        
        # If we want to consume the current char
        self.__read_char()

        return self.__new_token(
            TokenType.ILLEGAL,
            literal,
            valid_delims=valid_delims
        )



    def next_token(self) -> Token:
        """Returns the next token."""
        self.__skip_whitespace()

        if self.current_char is None:
            return self.__new_token(TokenType.EOF, "")
        
       
        # if self.current_char == '\r':
        #     self.__read_char() 
        #     if self.current_char == '\n':
        #         self.__read_char()  
        #     self.line_no += 1
        #     return self.__new_token(TokenType.NEWLINE, "\\n")
        # elif self.current_char == '\n':
        #     self.__read_char()  
        #     self.line_no += 1
        #     return self.__new_token(TokenType.NEWLINE, "\\n")




        if self.current_char.isalpha() or self.current_char in {'$', '@'}:
            return self.__read_identifier_or_keyword()

        if self.current_char.isdigit():
            return self.__read_number()

        if self.current_char == '"':
            start_pos = self.position  # Store the starting position
            literal = self.__read_string()

            if literal is None:
                return self.__new_token(TokenType.ILLEGAL, self.source[start_pos:self.position])  # Unclosed or invalid string

            return self.__new_token(TokenType.STR_LIT, literal)  # Return valid string literal

            
        if self.current_char == "'":
            start_pos = self.position  # Store the starting position
            literal = self.__read_char_literal()

            if literal is None:
                return self.__new_token(TokenType.ILLEGAL, self.source[start_pos:self.position])  # Unclosed or invalid char literal

            return self.__new_token(TokenType.CHR_LIT, literal)  # Return valid character literal


        # Handle single-character tokens and illegal characters
        match self.current_char:

            # ARITHMETIC OPERATORS & ASSIGNMENT OPERATORS

            # Token Creation for +, +=, ++
            case '+':
                if self.__peek_char() == '+':  # Potential "++"
                    # If there's whitespace before, we don't treat it as "++"
                    if self.position > 0 and self.source[self.position - 1].isspace():      
                        if self.__is_valid_delimiter(TokenType.PLUS):
                            return self.__consume_single_char_token(TokenType.PLUS)
                        else:
                            valid_delims = KEYWORD_DELIMITERS.get(TokenType.PLUS.name, set())
                            return self.__return_illegal_token("+", valid_delims=valid_delims)

                    # Otherwise, attempt "++"
                    self.__read_char()  # consume second '+'
                    if self.__is_valid_delimiter(TokenType.PLUS_PLUS):
                        self.__read_char()  # fully consume "++"
                        return self.__new_token(TokenType.PLUS_PLUS, "++")
                    else:
                        # If the delimiter is invalid for "++"
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.PLUS_PLUS.name, set())
                        return self.__return_illegal_token("++", valid_delims=valid_delims)

                elif self.__peek_char() == '=':  # Handle '+='
                    self.__read_char()  # consume the first '+'
                    if self.__is_valid_delimiter(TokenType.PLUS_EQ):
                        self.__read_char()  # consume '='
                        return self.__new_token(TokenType.PLUS_EQ, "+=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.PLUS_EQ.name, set())
                        return self.__return_illegal_token("+=", valid_delims=valid_delims)

                # Handles single '+'
                if self.__is_valid_delimiter(TokenType.PLUS):
                    return self.__consume_single_char_token(TokenType.PLUS)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.PLUS.name, set())
                    return self.__return_illegal_token("+", valid_delims=valid_delims)
                        # Token Creation for -, -=, --
            case '-':
                if self.__peek_char() == '-':  
                    orig_pos = self.position  
                    self.__read_char()  
                    if self.__peek_char() == '-':
                        self.__read_char()
                        self.__read_char()

                        comment_content = ""
                        while True:
                            self.__read_char()

                            if self.current_char == '\n':
                                self.line_no += 1

                            if self.current_char is None:
                                return self.__new_token(TokenType.ILLEGAL, comment_content.strip())

                            if self.current_char == '-' and self.__peek_char() == '-':
                                self.__read_char()
                                if self.__peek_char() == '-':
                                    self.__read_char()
                                    if self.__peek_char() in {'-'}:
                                        comment_content += "---"
                                    else:
                                        self.__read_char()
                                        return self.__new_token(TokenType.COMMENT, comment_content.strip())

                            comment_content += self.current_char
                       
                    else:
                        if orig_pos > 0 and self.source[orig_pos - 1].isspace():
                            valid_delims = KEYWORD_DELIMITERS.get(TokenType.MINUS.name, set())
                            return self.__return_illegal_token("-", valid_delims=valid_delims)
                        if self.__is_valid_delimiter(TokenType.MINUS_MINUS):
                            self.__read_char() 
                            return self.__new_token(TokenType.MINUS_MINUS, "--")
                        else:
                            valid_delims = KEYWORD_DELIMITERS.get(TokenType.MINUS_MINUS.name, set())
                            return self.__return_illegal_token("--", valid_delims=valid_delims)

                elif self.__peek_char() == '=':
                    self.__read_char() 
                    if self.__is_valid_delimiter(TokenType.MINUS_EQ):
                        self.__read_char()  
                        return self.__new_token(TokenType.MINUS_EQ, "-=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.MINUS_EQ.name, set())
                        return self.__return_illegal_token("-=", valid_delims=valid_delims)
                                        

                if self.__is_valid_delimiter(TokenType.MINUS):
                    return self.__consume_single_char_token(TokenType.MINUS)
                                        
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.MINUS.name, set())
                    return self.__return_illegal_token("-", valid_delims=valid_delims)




            # Token Creation for *, *=, **
            case '*':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.MUL_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.MUL_EQ, "*=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.MUL_EQ.name, set())
                        return self.__return_illegal_token("*=", valid_delims=valid_delims)
                elif self.current_char == '*':
                    if self.__peek_char() == '*':
                        self.__read_char()
                        if self.__is_valid_delimiter(TokenType.EXPONENT):
                            self.__read_char()
                            return self.__new_token(TokenType.EXPONENT, "**")
                        else:
                            valid_delims = KEYWORD_DELIMITERS.get(TokenType.EXPONENT.name, set())
                            return self.__return_illegal_token("**", valid_delims=valid_delims)
                    elif self.__is_valid_delimiter(TokenType.MULTIPLY):
                        return self.__consume_single_char_token(TokenType.MULTIPLY)
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.MULTIPLY.name, set())
                        return self.__return_illegal_token("*", valid_delims=valid_delims)
                    

            # Token Creation for /, /=
            case '/':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.DIV_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.DIV_EQ, "/=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.DIV_EQ.name, set())
                        return self.__return_illegal_token("/=", valid_delims=valid_delims)
                if self.__is_valid_delimiter(TokenType.DIVISION):
                    return self.__consume_single_char_token(TokenType.DIVISION)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.DIVISION.name, set())
                    return self.__return_illegal_token("/", valid_delims=valid_delims)
                   
            # Token Creation for Modulo (%, %=)
            case '%':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.MOD_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.MOD_EQ, "%=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.MOD_EQ.name, set())
                        return self.__return_illegal_token("%=", valid_delims=valid_delims)
                if self.__is_valid_delimiter(TokenType.MODULO):
                    return self.__consume_single_char_token(TokenType.MODULO)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.MODULO.name, set())
                    return self.__return_illegal_token("%", valid_delims=valid_delims)
            

            # Token Creation for =, ==
            case '=':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.EQ_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.EQ_EQ, "==")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.EQ_EQ.name, set())
                        return self.__return_illegal_token("==", valid_delims=valid_delims)
                if self.__is_valid_delimiter(TokenType.EQ):
                    return self.__consume_single_char_token(TokenType.EQ)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.EQ.name, set())
                    return self.__return_illegal_token("=", valid_delims=valid_delims)


            # COMPARISON OPERATORS
            
                       # Token Creation for Less than, Less than Equals (<, <=)
            case '<':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.LT_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.LT_EQ, "<=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.LT_EQ.name, set())
                        return self.__return_illegal_token("<=", valid_delims=valid_delims)
                
                if self.__peek_char() == '<':  
                    self.__read_char()  
                    if self.__is_valid_delimiter(TokenType.COMMENT):
                        self.__read_char()  
                        self.__skip_whitespace() 
                        comment_content = ""
                        while self.current_char and self.current_char != '\n':
                            comment_content += self.current_char
                            self.__read_char()
                        return self.__new_token(TokenType.COMMENT, comment_content.strip())  
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.COMMENT.name, set())
                        return self.__return_illegal_token("<<", valid_delims=valid_delims)
                if self.__is_valid_delimiter(TokenType.LT):
                    return self.__consume_single_char_token(TokenType.LT)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.LT.name, set())
                    return self.__return_illegal_token("<", valid_delims=valid_delims)
            
            # Token Creation for Greater than, Greater than Equals (> , >=)
            case '>':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.GT_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.GT_EQ, ">=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.GT_EQ.name, set())
                        return self.__return_illegal_token(">=", valid_delims=valid_delims)
                if self.__is_valid_delimiter(TokenType.GT):
                    return self.__consume_single_char_token(TokenType.GT)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.GT.name, set())
                    return self.__return_illegal_token(">", valid_delims=valid_delims)
                       
            # Token Creation for Not, Not Equals (!, !=)
            case '!':
                if self.__peek_char() == '=':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.NOT_EQ):
                        self.__read_char()
                        return self.__new_token(TokenType.NOT_EQ, "!=")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.NOT_EQ.name, set())
                        return self.__return_illegal_token("!=", valid_delims=valid_delims)
                if self.__is_valid_delimiter(TokenType.NOT):
                    return self.__consume_single_char_token(TokenType.NOT)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.NOT.name, set())
                    return self.__return_illegal_token("!", valid_delims=valid_delims)

            # LOGICAL OPERATORS

            # Token Creation for AND (&&)
            case '&':
                if self.__peek_char() == '&':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.AND):
                        self.__read_char()
                        return self.__new_token(TokenType.AND, "&&")
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.AND.name, set())
                        return self.__return_illegal_token("&&", valid_delims=valid_delims)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.AND.name, set())
                    return self.__return_illegal_token("&", valid_delims=valid_delims)

            # Token Creation for OR (||)
            case '|':
                if self.__peek_char() == '|':
                    self.__read_char()
                    if self.__is_valid_delimiter(TokenType.OR):
                        self.__read_char()
                        return self.__new_token(TokenType.OR, "||")   
                    else:
                        valid_delims = KEYWORD_DELIMITERS.get(TokenType.OR.name, set())
                        return self.__return_illegal_token("||", valid_delims=valid_delims)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.OR.name, set())
                    return self.__return_illegal_token("|", valid_delims=valid_delims)
                
            # Token Creation NEGATIVE OP/TILDE
            case '~':
                if self.__is_valid_delimiter(TokenType.TILDE):
                    return self.__consume_single_char_token(TokenType.TILDE)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.TILDE.name, set())
                    return self.__return_illegal_token("~", valid_delims=valid_delims)
                
            # Parentheses, Brackets, Braces, and Punctuation
            case '(':
                if self.__is_valid_delimiter(TokenType.LPAREN):
                    return self.__consume_single_char_token(TokenType.LPAREN)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.LPAREN.name, set())
                    return self.__return_illegal_token("(", valid_delims=valid_delims)
            case ')':
                if self.__is_valid_delimiter(TokenType.RPAREN):
                    return self.__consume_single_char_token(TokenType.RPAREN)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.RPAREN.name, set())
                    return self.__return_illegal_token(")", valid_delims=valid_delims)
            case '[':
                if self.__is_valid_delimiter(TokenType.LBRACKET):
                    return self.__consume_single_char_token(TokenType.LBRACKET)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.LBRACKET.name, set())
                    return self.__return_illegal_token("[", valid_delims=valid_delims)
            case ']':
                if self.__is_valid_delimiter(TokenType.RBRACKET):
                    return self.__consume_single_char_token(TokenType.RBRACKET)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.RBRACKET.name, set())
                    return self.__return_illegal_token("]", valid_delims=valid_delims)
            case '{':
                if self.__is_valid_delimiter(TokenType.LBRACE):
                    return self.__consume_single_char_token(TokenType.LBRACE)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.LBRACE.name, set())
                    return self.__return_illegal_token("{", valid_delims=valid_delims)
            case '}':
                if self.__is_valid_delimiter(TokenType.RBRACE):
                    return self.__consume_single_char_token(TokenType.RBRACE)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.RBRACE.name, set())
                    return self.__return_illegal_token("}", valid_delims=valid_delims)
            case ',':
                if self.__is_valid_delimiter(TokenType.COMMA):
                    return self.__consume_single_char_token(TokenType.COMMA)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.COMMA.name, set())
                    return self.__return_illegal_token(",", valid_delims=valid_delims)
            case ';':
                if self.__is_valid_delimiter(TokenType.SEMICOLON):
                    return self.__consume_single_char_token(TokenType.SEMICOLON)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.SEMICOLON.name, set())
                    return self.__return_illegal_token(";", valid_delims=valid_delims)
            case ':':
                if self.__is_valid_delimiter(TokenType.COLON):
                    return self.__consume_single_char_token(TokenType.COLON)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.COLON.name, set())
                    return self.__return_illegal_token(":", valid_delims=valid_delims)
            case '.':
             
                if self.__is_valid_delimiter(TokenType.DOT):
                    return self.__consume_single_char_token(TokenType.DOT)
                else:
                    valid_delims = KEYWORD_DELIMITERS.get(TokenType.DOT.name, set())
                    return self.__return_illegal_token(".", valid_delims=valid_delims)
            case _:
                return self.__return_illegal_token()

    
 
    def __read_illegal_token(self) -> Token:
        """
        Reads characters starting from an illegal token and groups all subsequent
        characters on the same line into a single ILLEGAL token.
        """
        start_pos = self.position  # Record the starting position of the illegal sequence

        # Continue reading characters until a newline or end of input
        while self.current_char and self.current_char != ' ':
            self.__read_char()

        # Create an ILLEGAL token for the entire invalid sequence
        illegal_literal = self.source[start_pos:self.position]
    
        return self.__new_token(TokenType.ILLEGAL, illegal_literal)

    def __consume_single_char_token(self, token_type: TokenType) -> Token:
        """Helper to return a token for a single character."""
        tok = self.__new_token(token_type, self.current_char)
        self.__read_char()
        return tok    
    
    def __checkIDforAfterBracketsError(self) -> bool:
        """Checks if an identifier with brackets contains more characters after it. Example: $A[]B, if identifier is in this form, it returns True"""
        #Lim-D:
        #Save the original self variables, to make this function act like a look-ahead-function
        original_self_position = self.position
        original_read_position = self.read_position
        original_line_no = self.line_no
        original_current_char = self.current_char

        if self.current_char == '[':
            #i think we need to test this while loop a lot.
            while self.current_char and self.current_char != ']':
                self.__read_char()
            if self.current_char == ']':
                self.__read_char()
                # If may continuation pa yung ']' mo, then make the whole sequence illegal.
                #Recommended change sa IF: mas maganda all characters excluded sa valid delimiters ng ']' para goods.
                if Delimiters.is_valid_identifier_char(self.current_char) or self.current_char == '$':
                    while self.current_char and (self.current_char != ' ' or self.current_char != '\n'): #or current delimiters for identifiers, stop na rin dun.
                        self.__read_char()
                    # make the whole identifier illegal (True condition)
                    return True
                else:
                    self.position = original_self_position
                    self.read_position = original_read_position
                    self.line_no = original_line_no
                    self.current_char = original_current_char
                    return False
            else: #If it cannot find a ']' after everything. Then, revert back the self variables to their original form.
                self.position = original_self_position
                self.read_position = original_read_position
                self.line_no = original_line_no
                self.current_char = original_current_char
                return False
        return False

    def token(self):
        """Returns the next valid token for PLY, skipping ILLEGAL tokens"""
        while True:
            tok = self.next_token()
            if tok.type == TokenType.EOF:
                return None

            # If it's a comment or an ILLEGAL token, just skip it
            if tok.type == TokenType.COMMENT or tok.type == TokenType.ILLEGAL:
                continue

            # Otherwise, it's a valid token for the parser
            tok.type = tok.type.name  # PLY requires token type as a string
            tok.value = tok.literal
            tok.lineno = tok.line_no
            return tok

