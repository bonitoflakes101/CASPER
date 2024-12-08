from Lexer import Lexer
from Token import Token, TokenType
from typing import Callable
from enum import Enum, auto

from AST import Statement, Expression, Program
from AST import ExpressionStatement, LetStatement
from AST import InfixExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral, StringLiteral


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
            TokenType.FLOAT: self.__parse_float_literal,
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

    # # region Statament Methods
    # def __parse_statement(self) -> Statement:
    #     match self.current_token.type:
    #         case TokenType.LET:
    #             return self.__parse_let_statement()
    #         # case TokenType.FN:
    #         #     return self.__parse_function_statement()
    #         # case TokenType.RETURN:
    #         #     return self.__parse_return_statement()
    #         # case TokenType.WHILE:
    #         #     return self.__parse_while_statement()
    #         # case TokenType.BREAK:
    #         #     return self.__parse_break_statement()
    #         # case TokenType.CONTINUE:
    #         #     return self.__parse_continue_statement()
    #         # case TokenType.FOR:
    #         #     return self.__parse_for_statement()
    #         # case TokenType.IMPORT:
    #         #     return self.__parse_import_statement()
    #         case _:
    #             return self.__parse_expression_statement()
            
# Handle Variable Declarations (instead of `LET` keyword)
    def __parse_variable_declaration(self) -> LetStatement:
        stmt: LetStatement = LetStatement()

        # Check for the variable's data type (e.g., `int`, `float`)
        if not self.__expect_peek(TokenType.INT) and not self.__expect_peek(TokenType.FLOAT):
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
            case TokenType.INT | TokenType.FLOAT | TokenType.STR | TokenType.BLN:
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
    
    def __parse_let_statement(self) -> LetStatement:
        stmt: LetStatement = LetStatement()

        # let a: int = 10;

        if not self.__expect_peek(TokenType.IDENT):
            return None
        
        stmt.name = IdentifierLiteral(value=self.current_token.literal)

        if not self.__expect_peek(TokenType.COLON):
            return None
        
        if not self.__expect_peek(TokenType.TYPE):
            return None
        
        stmt.value_type = self.current_token.literal

        if not self.__expect_peek(TokenType.EQ):
            return None
        
        self.__next_token()

        stmt.value = self.__parse_expression(PrecedenceType.P_LOWEST)

        while not self.__current_token_is(TokenType.SEMICOLON) and not self.__current_token_is(TokenType.EOF):
            self.__next_token()

        return stmt
    
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
    