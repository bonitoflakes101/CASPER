# CONSTANTS
DIGITS = '0123456789'

# Token type: Value

# Reserved keywords 
RESERVED_KEYWORDS = {
    # Start and Finish
    'birth': 'birth',
    'ghost': 'ghost',

    # Data Types
    'int': 'int',
    'flt': 'float',
    'bln': 'boolean',
    'chr': 'character',
    'str': 'string',

    # Input/Output
    'input': 'input',
    'display': 'display',

    # Conditionals
    'check': 'if',
    'otherwise': 'else',
    'otherwise_check': 'elseif',

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
        errors = []
        print(f"{'Index':<6}{'Char':<6}{'Action':<30}{'Token (if any)':<20}")
        print('-' * 70)

        while self.current_char is not None:
            index = self.pos.idx
            char = self.current_char
            action = ""
            token = None

            if char in ' \t':
                action = "Skipped whitespace"
                self.advance()
            elif char in DIGITS:
                start_pos = self.pos.idx
                token = self.make_number()
                action = f"Tokenized number [{start_pos}-{self.pos.idx - 1}]"
                tokens.append(token)
            elif char == '$':
                start_pos = self.pos.idx
                token = self.make_identifier()
                action = f"Tokenized identifier [{start_pos}-{self.pos.idx - 1}]"
                tokens.append(token)
            elif char.isalpha():
                token = self.make_keyword_or_identifier()
                if token.type == 'ERROR':
                    errors.append(token.value)
                    action = f"Error: {token.value}"
                else:
                    action = f"Tokenized keyword/identifier [{index}-{self.pos.idx - 1}]"
                    tokens.append(token)
            elif char in RESERVED_SYMBOLS:
                start_pos = self.pos.idx
                token = self.make_operator()
                action = f"Tokenized operator/symbol [{start_pos}-{self.pos.idx - 1}]"
                tokens.append(token)
            else:
                pos_start = self.pos.copy()
                action = "Illegal character"
                errors.append(f"Illegal character '{char}' at position {index}")
                self.advance()

            for i in range(index, self.pos.idx):
                token_display = repr(token) if i == index else ""
                print(f"{i:<6}{self.text[i]:<6}{action:<30}{token_display:<20}")

        print('-' * 70)
        print("Tokenization complete.")
        return tokens, errors


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
        pos_start = self.pos.copy()

        while self.current_char is not None and self.current_char.isalnum():
            word += self.current_char
            self.advance()

        if word in RESERVED_KEYWORDS:
            return Token(RESERVED_KEYWORDS[word], word)

        if not word.startswith('$'):
            return Token('ERROR', f"Invalid identifier '{word}' (must start with '$')")

        return Token('IDENTIFIER', word)




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
    tokens, errors = lexer.make_tokens()

    if errors:
        print("\nErrors encountered during tokenization:")
        for error in errors:
            print(f" - {error}")

    return tokens, None

