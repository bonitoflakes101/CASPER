from Token import TokenType

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens  # List of tokens from the lexer
        self.current_token = None
        self.position = -1
        self.symbol_table = {}  # Stores variables & functions
        self.errors = []  # Stores syntax errors
        self.next_token()

    def next_token(self):
        """Advance to the next token."""
        self.position += 1
        if self.position < len(self.tokens):
            self.current_token = self.tokens[self.position]
        else:
            self.current_token = TokenType.EOF

    def error(self, message):
        """Log syntax errors."""
        self.errors.append(f"Syntax Error at Line {self.current_token.line_no}: {message}")

    def parse_program(self):
        """Parse the full program by handling multiple statements."""
        while self.current_token != TokenType.EOF:
            self.parse_statement()
        return "Parsing completed successfully!" if not self.errors else self.errors

    def parse_statement(self):
        """Handle different types of statements based on the token."""
        if self.current_token.type in {TokenType.INT, TokenType.FLT, TokenType.STR, TokenType.BLN}:
            self.parse_assignment()
        elif self.current_token.type == TokenType.FUNCTION_NAME:
            self.parse_function_call()
        elif self.current_token.type == TokenType.CHECK:
            self.parse_if_statement()
        elif self.current_token.type in {TokenType.FOR, TokenType.UNTIL}:
            self.parse_loop()
        else:
            self.error(f"Unexpected token: {self.current_token.literal}")
            self.next_token()

    def parse_assignment(self):
        """Parses variable assignment like: int $x = 5;"""
        data_type = self.current_token
        self.next_token()

        if self.current_token.type != TokenType.IDENT:
            self.error("Expected variable name after data type.")
            return

        var_name = self.current_token.literal
        self.next_token()

        if self.current_token.type != TokenType.EQ:
            self.error("Expected '=' in assignment.")
            return
        self.next_token()

        if self.current_token.type not in {TokenType.INT_LIT, TokenType.FLT_LIT, TokenType.STR_LIT, TokenType.BLN_LIT}:
            self.error("Expected a valid value after '='.")
            return

        value = self.current_token.literal
        self.symbol_table[var_name] = value  # Store variable
        self.next_token()

        if self.current_token.type != TokenType.SEMICOLON:
            self.error("Missing semicolon at end of assignment.")
        self.next_token()

    def parse_function_call(self):
        """Parses function calls like @myFunc(5, $var);"""
        func_name = self.current_token.literal
        self.next_token()

        if self.current_token.type != TokenType.LPAREN:
            self.error("Expected '(' after function name.")
            return
        self.next_token()

        args = []
        while self.current_token.type != TokenType.RPAREN:
            if self.current_token.type in {TokenType.IDENT, TokenType.INT_LIT, TokenType.FLT_LIT}:
                args.append(self.current_token.literal)
                self.next_token()
            if self.current_token.type == TokenType.COMMA:
                self.next_token()
            else:
                break

        if self.current_token.type != TokenType.RPAREN:
            self.error("Expected ')' at end of function call.")
            return
        self.next_token()

        if self.current_token.type != TokenType.SEMICOLON:
            self.error("Missing semicolon at end of function call.")
        self.next_token()

    def parse_if_statement(self):
        """Parses IF statements like: CHECK ($x == 5) { ... }"""
        self.next_token()
        if self.current_token.type != TokenType.LPAREN:
            self.error("Expected '(' after CHECK.")
            return
        self.next_token()

        # Parse condition (for now, we assume simple expressions)
        condition = self.current_token.literal
        self.next_token()

        if self.current_token.type != TokenType.RPAREN:
            self.error("Expected ')' after condition.")
            return
        self.next_token()

        if self.current_token.type != TokenType.LBRACE:
            self.error("Expected '{' to start if-block.")
            return
        self.next_token()

        while self.current_token.type != TokenType.RBRACE:
            self.parse_statement()
        self.next_token()

    def parse_loop(self):
        """Parses loops like: FOR ($i = 0; $i < 10; $i++) { ... }"""
        loop_type = self.current_token
        self.next_token()

        if self.current_token.type != TokenType.LPAREN:
            self.error("Expected '(' after loop keyword.")
            return
        self.next_token()

        # Just a simple placeholder check for now
        while self.current_token.type != TokenType.RPAREN:
            self.next_token()

        self.next_token()
        if self.current_token.type != TokenType.LBRACE:
            self.error("Expected '{' to start loop block.")
            return
        self.next_token()

        while self.current_token.type != TokenType.RBRACE:
            self.parse_statement()
        self.next_token()

# Sample usage (for debugging)
if __name__ == "__main__":
    from Lexer import Lexer
    code = """
    int $x = 10
    check ($x > 5) {
        display($x);
    }

    """
    lexer = Lexer(code)
    tokens = []
    while (token := lexer.next_token()).type != TokenType.EOF:
        tokens.append(token)
    
    parser = Parser(tokens)
    result = parser.parse_program()
    print(result)
    print("Symbol Table:", parser.symbol_table)
