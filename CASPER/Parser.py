from Lexer import Lexer
from Token import Token, TokenType
from typing import Callable
from enum import Enum, auto

from AST import Statement, Expression, Program
from AST import ExpressionStatement, LetStatement, FunctionStatement, ReturnStatement, BlockStatement, AssignStatement, IfStatement, WhileStatement, BreakStatement, ContinueStatement, ForStatement, ImportStatement
from AST import InfixExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral, StringLiteral
from AST import FunctionParameter


# Precedence Types
class PrecedenceType(Enum):
    P_LOWEST = 0
    P_EQUALS = auto()
    P_LESSGREATER = auto()
    P_SUM = auto()
    P_PRODUCT = auto()
    P_EXPONENT = auto()
    P_PREFIX = auto()
    P_CALL = auto()
    P_INDEX = auto()

#Precedence Mapping
PRECEDENCES: dict[TokenType, int] = {
    TokenType.PLUS: PrecedenceType.P_SUM,
    TokenType.MINUS: PrecedenceType.P_SUM,
    TokenType.SLASH: PrecedenceType.P_PRODUCT,
    TokenType.ASTERISK: PrecedenceType.P_PRODUCT,
    TokenType.MODULUS: PrecedenceType.P_PRODUCT,
    TokenType.POW: PrecedenceType.P_EXPONENT,
    }

class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self.lexer: Lexer = lexer
        
        # Just a list of errors caught during parsing
        self.errors: list[str] = []

        self.current_token: Token = None
        self.peek_token: Token = None

        self.prefix_parse_fns: dict[TokenType, Callable] = {
            # TokenType.IDENT: self.__parse_identifier,
            TokenType.INT: self.__parse_int_literal,
            TokenType.FLT: self.__parse_float_literal,
            TokenType.LPAREN: self.__parse_grouped_expression,
        }
        self.infix_parse_fns: dict[TokenType, Callable] = {
            TokenType.PLUS: self.__parse_infix_expression,
            TokenType.MINUS: self.__parse_infix_expression,
            TokenType.SLASH: self.__parse_infix_expression,
            TokenType.ASTERISK: self.__parse_infix_expression,
            TokenType.POW: self.__parse_infix_expression,
            TokenType.MODULUS: self.__parse_infix_expression,

        }

        # Populate the current_token and peek_token
        self.__next_token()
        self.__next_token()
    
    # region Parser Helpers
    def __next_token(self) -> None:
        """ Advances the lexer to retrieve the next token """
        self.current_token = self.peek_token
        self.peek_token = self.lexer.next_token()

    def __current_token_is(self, tt: TokenType) -> bool:
        return self.current_token.type == tt

    def __peek_token_is(self, tt: TokenType) -> bool:
        """ Peeks one token ahead and checks the type """
        return self.peek_token.type == tt
    
    # def __peek_token_is_assignment(self) -> bool:
    #     assignment_operators: list[TokenType] = [
    #         TokenType.EQ,
    #         TokenType.PLUS_EQ,
    #         TokenType.MINUS_EQ,
    #         TokenType.MUL_EQ,
    #         TokenType.DIV_EQ
    #     ]
    #     return self.peek_token.type in assignment_operators
    
    def __expect_peek(self, tt: TokenType) -> bool:
        if self.__peek_token_is(tt):
            self.__next_token()
            return True
        else:
            self.__peek_error(tt)
            return False
    
    def __current_precedence(self) -> PrecedenceType:
        prec: int | None = PRECEDENCES.get(self.current_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec
    
    def __peek_precedence(self) -> PrecedenceType:
        prec: int | None = PRECEDENCES.get(self.peek_token.type)
        if prec is None:
            return PrecedenceType.P_LOWEST
        return prec
    
    def __peek_error(self, tt: TokenType) -> None:
        self.errors.append(f"Expected next token to be {tt}, got {self.peek_token.type} instead.")

    def __no_prefix_parse_fn_error(self, tt: TokenType):
        self.errors.append(f"No Prefix Parse Function for {tt} found")
    # endregion
    
    def parse_program(self) -> None:
        """ Main execution entry to the Parser """
        program: Program = Program()

        while self.current_token.type != TokenType.EOF:
            stmt: Statement = self.__parse_statement()
            if stmt is not None:
                program.statements.append(stmt)
            
            self.__next_token()

        return program
            
# Handle Variable Declarations (instead of `LET` keyword)
    def __parse_variable_declaration(self) -> LetStatement:
        stmt: LetStatement = LetStatement()

        # Check for the variable's data type (e.g., `int`, `float`)
        if not self.__expect_peek(TokenType.INT) and not self.__expect_peek(TokenType.FLT):
            return None

        stmt.value_type = self.current_token.literal  # Store the type (int, float)

        if not self.__expect_peek(TokenType.IDENT):  # Expect variable name
            return None

        stmt.name = IdentifierLiteral(value=self.current_token.literal)  # Store the variable name (e.g., `$num`)

        if not self.__expect_peek(TokenType.EQ):  # Expect assignment operator '='
            return None

        self.__next_token()  # Move to the value after '='

        stmt.value = self.__parse_expression(PrecedenceType.P_LOWEST)  # Parse the value of the variable

        while not self.__current_token_is(TokenType.SEMICOLON) and not self.__current_token_is(TokenType.EOF):
            self.__next_token()

        return stmt

    def __parse_statement(self) -> Statement:
        match self.current_token.type:
            case TokenType.INT | TokenType.FLT | TokenType.STR | TokenType.BLN:
                return self.__parse_variable_declaration()  # Handle declarations
            case TokenType.FUNCTION:
                return self.__parse_function_statement()
            case TokenType.REVIVE: # return = revive
                return self.__parse_return_statement()
            case TokenType.UNTIL: # while = until
                return self.__parse_while_statement()
            case TokenType.STOP: # break = stop
                return self.__parse_break_statement()
            case TokenType.SKIP: # continue = skip
                return self.__parse_continue_statement()
            case TokenType.FOR:
                return self.__parse_for_statement()
            case _:
                return self.__parse_expression_statement()

    
    def __parse_expression_statement(self) -> ExpressionStatement:
        expr = self.__parse_expression(PrecedenceType.P_LOWEST)

        if self.__peek_token_is(TokenType.SEMICOLON):
            self.__next_token()

        stmt: ExpressionStatement = ExpressionStatement(expr=expr)

        return stmt
    
    # def __parse_let_statement(self) -> LetStatement:
    #     stmt: LetStatement = LetStatement()

    #     # let a: int = 10;

    #     if not self.__expect_peek(TokenType.IDENT):
    #         return None
        
    #     stmt.name = IdentifierLiteral(value=self.current_token.literal)

    #     if not self.__expect_peek(TokenType.COLON):
    #         return None
        
    #     if not self.__expect_peek(TokenType.TYPE):
    #         return None
        
    #     stmt.value_type = self.current_token.literal

    #     if not self.__expect_peek(TokenType.EQ):
    #         return None
        
    #     self.__next_token()

    #     stmt.value = self.__parse_expression(PrecedenceType.P_LOWEST)

    #     while not self.__current_token_is(TokenType.SEMICOLON) and not self.__current_token_is(TokenType.EOF):
    #         self.__next_token()

    #     return stmt
    
    def __parse_function_statement(self) -> FunctionStatement:
        stmt: FunctionStatement = FunctionStatement()

        # fn name() -> int { return 10; }

        if not self.__expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(value=self.current_token.literal)

        if not self.__expect_peek(TokenType.LPAREN):
            return None
        
        stmt.parameters = self.__parse_function_parameters()

        if not self.__expect_peek(TokenType.ARROW):
            return None
        
        self.__next_token()

        stmt.return_type = self.current_token.literal

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        stmt.body = self.__parse_block_statement()

        return stmt
    
    def __parse_function_parameters(self) -> list[FunctionParameter]:
        params: list[FunctionParameter] = []

        if self.__peek_token_is(TokenType.RPAREN):
            self.__next_token()
            return params
        
        self.__next_token()

        first_param: FunctionParameter = FunctionParameter(name=self.current_token.literal)

        if not self.__expect_peek(TokenType.COLON):
            return None
        
        self.__next_token()

        first_param.value_type = self.current_token.literal
        params.append(first_param)

        while self.__peek_token_is(TokenType.COMMA):
            self.__next_token()
            self.__next_token()

            param: FunctionParameter = FunctionParameter(name=self.current_token.literal)

            if not self.__expect_peek(TokenType.COLON):
                return None
            
            self.__next_token()

            param.value_type = self.current_token.literal

            params.append(param)

        if not self.__expect_peek(TokenType.RPAREN):
            return None
        
        return params

    def __parse_block_statement(self) -> BlockStatement:
        block_stmt: BlockStatement = BlockStatement()

        self.__next_token()

        while not self.__current_token_is(TokenType.RBRACE) and not self.__current_token_is(TokenType.EOF):
            stmt: Statement = self.__parse_statement()
            if stmt is not None:
                block_stmt.statements.append(stmt)

            self.__next_token()

        return block_stmt

    def __parse_return_statement(self) -> ReturnStatement:
        stmt: ReturnStatement = ReturnStatement()

        self.__next_token()

        stmt.return_value = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.SEMICOLON):
            return None
        
        return stmt
    
    def __parse_assignment_statement(self) -> AssignStatement:
        stmt: AssignStatement = AssignStatement()

        stmt.ident = IdentifierLiteral(value=self.current_token.literal)

        self.__next_token() # skips the 'IDENT'
        
        stmt.operator = self.current_token.literal
        self.__next_token() # skips the operator

        stmt.right_value = self.__parse_expression(PrecedenceType.P_LOWEST)

        self.__next_token()

        return stmt
    
    def __parse_if_statement(self) -> IfStatement:
        condition: Expression = None
        consequence: BlockStatement = None
        alternative: BlockStatement = None

        self.__next_token()

        condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        consequence = self.__parse_block_statement()

        if self.__peek_token_is(TokenType.ELSE):
            self.__next_token()

            if not self.__expect_peek(TokenType.LBRACE):
                return None
            
            alternative = self.__parse_block_statement()

        return IfStatement(condition=condition, consequence=consequence, alternative=alternative)
    
    def __parse_while_statement(self) -> WhileStatement:
        condition: Expression = None
        body: BlockStatement = None

        self.__next_token()  # Skip WHILE

        condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        body = self.__parse_block_statement()

        return WhileStatement(condition=condition, body=body)
    
    def __parse_break_statement(self) -> BreakStatement:
        self.__next_token()
        return BreakStatement()
    
    def __parse_continue_statement(self) -> ContinueStatement:
        self.__next_token()
        return ContinueStatement()
    
    def __parse_for_statement(self) -> ForStatement:
        """ for (let i: int = 0; i < 10; i = i + 1) { } """
        stmt: ForStatement = ForStatement()

        if not self.__expect_peek(TokenType.LPAREN):
            return None
        
        if not self.__expect_peek(TokenType.LET):
            return None

        stmt.var_declaration = self.__parse_let_statement()

        self.__next_token()  # Skip ;

        stmt.condition = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.SEMICOLON):
            return None
        
        self.__next_token() # Skip ;

        stmt.action = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.RPAREN):
            return None

        if not self.__expect_peek(TokenType.LBRACE):
            return None
        
        stmt.body = self.__parse_block_statement()

        return stmt
    
    def __parse_import_statement(self) -> ImportStatement:
        if not self.__expect_peek(TokenType.STRING):
            return None
        
        stmt = ImportStatement(file_path=self.current_token.literal)
        
        if not self.__expect_peek(TokenType.SEMICOLON):
            return None
        
        return stmt
    # endregion

    
    # region Expression Methods
    def __parse_expression(self, precedence: PrecedenceType) -> Expression:
        prefix_fn: Callable | None = self.prefix_parse_fns.get(self.current_token.type)
        if prefix_fn is None:
            self.__no_prefix_parse_fn_error(self.current_token.type)
            return None
        
        left_expr: Expression = prefix_fn()
        while not self.__peek_token_is(TokenType.SEMICOLON) and precedence.value < self.__peek_precedence().value:
            infix_fn: Callable | None = self.infix_parse_fns.get(self.peek_token.type)
            if infix_fn is None:
                return left_expr
            
            self.__next_token()

            left_expr = infix_fn(left_expr)
        
        return left_expr
    
    def __parse_infix_expression(self, left_node: Expression) -> Expression:
        """ Parses and returns a normal InfixExpression """
        infix_expr: InfixExpression = InfixExpression(left_node=left_node, operator=self.current_token.literal)

        precedence = self.__current_precedence()

        self.__next_token()

        infix_expr.right_node = self.__parse_expression(precedence)

        return infix_expr
    
    def __parse_grouped_expression(self) -> Expression:
        self.__next_token()

        expr: Expression = self.__parse_expression(PrecedenceType.P_LOWEST)

        if not self.__expect_peek(TokenType.RPAREN):
            return None
        
        return expr
    def __parse_int_literal(self) -> Expression:
        """ Parses an IntegerLiteral Node from the current token """
        int_lit: IntegerLiteral = IntegerLiteral()

        try:
            int_lit.value = int(self.current_token.literal)

        except:
            self.errors.append(f"Could not parse `{self.current_token.literal}` as an integer.")
            return None
        
        return int_lit
    
    def __parse_float_literal(self) -> Expression:
        """ Parses an FloatLiteral Node from the current token """
        float_lit: FloatLiteral = FloatLiteral()

        try:
            float_lit.value = float(self.current_token.literal)
        except:
            self.errors.append(f"Could not parse `{self.current_token.literal}` as an float.")
            return None
        
        return float_lit
    