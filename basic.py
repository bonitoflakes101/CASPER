# CONSTANTS
DIGITS = '0123456789'

# Reserved keywords (language constructs)
RESERVED_KEYWORDS = {
    # Start and Finish
    'birth': 'birth',
    'ghost': 'ghost',

    # Data Types
    'int': 'integer',
    'flt': 'float',
    'bln': 'boolean',
    'chr': 'character',
    'str': 'string',

    # Input/Output
    'input': 'input',
    'display': 'display',

    # Conditionals
    'check': 'check',
    'if': 'if',
    'otherwise': 'otherwise',
    'otherwise_check': 'otherwise_check',
    'elseif': 'elseif',

    # Loop
    'for': 'for',
    'repeat': 'repeat',
    'until': 'until',
    'stop': 'stop',
    'skip': 'skip',
    'swap': 'swap',
    'shift': 'shift',
    'revive': 'revive',

    # Others
    'GLOBAL': 'GLOBAL',
    'function': 'function',
    'structure': 'structure',
    'Day': 'Day',
    'Night': 'Night',
    'measure': 'measure',
    'in': 'in',
}

# Reserved symbols
RESERVED_SYMBOLS = {
    '+': 'PLUS',
    '-': 'MINUS',
    '*': 'MUL',
    '/': 'DIV',
    '%': 'MOD',
    '//': 'DIVIDE_INT',
    '**': 'POWER',
    '~': 'TILDE',
    '=': 'ASSIGN',
    '+=': 'PLUS_ASSIGN',
    '-=': 'MINUS_ASSIGN',
    '*=': 'MULT_ASSIGN',
    '/=': 'DIV_ASSIGN',
    '%=': 'MOD_ASSIGN',
    '==': 'EQUAL',
    '!=': 'NOT_EQUAL',
    '>': 'GREATER',
    '<': 'LESS',
    '>=': 'GREATER_EQUAL',
    '<=': 'LESS_EQUAL',
    '---': 'MULTI_COMMENT',
    '<<': 'SINGLE_COMMENT',
}

# ERRORS
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        return f'{self.error_name}: {self.details}\nFile {self.pos_start.fn}, line {self.pos_start.ln + 1}'


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

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1
        if current_char == '\n':
            self.ln += 1
            self.col = 0
        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


# TOKENS
class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f'{self.type}:{self.value}' if self.value else f'{self.type}'


# LEXER
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
        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == '$':
                tokens.append(self.make_identifier())
            elif self.current_char.isalpha():
                tokens.append(self.make_keyword_or_identifier())
            elif self.current_char in RESERVED_SYMBOLS:
                tokens.append(self.make_operator())
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")
        return tokens, None

    def make_number(self):
        num_str = ''
        dot_count = 0
        while self.current_char is not None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()
        return Token('FLOAT' if dot_count else 'INT', float(num_str) if dot_count else int(num_str))

    def make_identifier(self):
        identifier_str = '$'
        self.advance()
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            identifier_str += self.current_char
            self.advance()
        return Token('IDENTIFIER', identifier_str)

    def make_keyword_or_identifier(self):
        word = ''
        while self.current_char is not None and self.current_char.isalpha():
            word += self.current_char
            self.advance()
        return Token(RESERVED_KEYWORDS.get(word, 'IDENTIFIER'), word)

    def make_operator(self):
        op = self.current_char
        if self.pos.idx + 1 < len(self.text):
            two_char_op = op + self.text[self.pos.idx + 1]
            if two_char_op in RESERVED_SYMBOLS:
                self.advance()
                op = two_char_op
        self.advance()
        return Token(RESERVED_SYMBOLS[op], op)


# RUN FUNCTION
def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    return tokens, error
