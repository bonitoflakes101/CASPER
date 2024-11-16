# CONSTANTS
DIGITS = '0123456789'

# Reserved keywords (language constructs)
RESERVED_KEYWORDS = {
    'birth': 'birth',
    'ghost': 'ghost',
    'global': 'GLOBAL',
    'int': 'integer',
    'flt': 'float',
    'bln': 'boolean',
    'chr': 'character',
    'str': 'string'
}

# Reserved symbols (operators and parentheses)
RESERVED_SYMBOLS = {
    '+': 'PLUS',
    '-': 'MINUS',
    '*': 'MUL',
    '/': 'DIV',
    '(': 'LPAREN',
    ')': 'RPAREN',
}

# ERRORS

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
    
    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

# POSITION
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


# TOKENS
TT_INT = 'INT'
TT_FLOAT = 'FLOAT'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_IDENTIFIER = 'IDENTIFIER'

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        if self.value:
            return f'{self.type}:{self.value}'
        return f'{self.type}'
class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':  # Skip whitespace
                self.advance()
            elif self.current_char in DIGITS:  # Handle numbers
                tokens.append(self.make_number())
            elif self.current_char == '$':  # Handle '$' as part of the identifier
                tokens.append(self.make_identifier())
            elif self.current_char.isalpha():  # Handle keywords or regular identifiers (without $)
                tokens.append(self.make_keyword_or_identifier())
            elif self.current_char in RESERVED_SYMBOLS:  # Handle reserved symbols (operators, parentheses)
                tokens.append(Token(RESERVED_SYMBOLS[self.current_char], self.current_char))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        return tokens, None

    def make_number(self):
        num_str = ''
        dot_count = 0

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))

    def make_identifier(self):
        # $ is mandatory for the identifier
        identifier_str = '$'
        self.advance()  # Skip the '$'

        while self.current_char != None and (self.current_char.isalnum() or self.current_char == '_'):
            identifier_str += self.current_char
            self.advance()

        return Token(TT_IDENTIFIER, identifier_str)

    def make_keyword_or_identifier(self):
        word = ''
        while self.current_char != None and self.current_char.isalpha():
            word += self.current_char
            self.advance()

        # Ensure the word has a $ in it, otherwise it is not an identifier
        if '$' in word:  # Only treat as identifier if $ is present
            return Token(TT_IDENTIFIER, word)

        # If it is a reserved keyword, return that token
        if word in RESERVED_KEYWORDS:
            return Token(RESERVED_KEYWORDS[word], word)
        else:
            # Word is neither a keyword nor a valid identifier, return it as a non-identifier
            return None  # Returning None here indicates it's neither an identifier nor a keyword.

# RUN
def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    # If any token is None (invalid identifier/word), remove it from the token list
    tokens = [token for token in tokens if token is not None]

    return tokens, error