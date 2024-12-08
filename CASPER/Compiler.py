from llvmlite import ir

from AST import Node, NodeType, Program, Expression
from AST import ExpressionStatement, LetStatement
from AST import InfixExpression
from AST import IntegerLiteral, FloatLiteral, IdentifierLiteral, BooleanLiteral, StringLiteral

from Environment import Environment

# from Lexer import Lexer
# from Parser import Parser

# import os

class Compiler:
    def __init__(self) -> None:
        self.type_map: dict[str, ir.Type] = {
            'int': ir.IntType(32),
            'float': ir.FloatType()
        }

        # Initialize the main module
        self.module: ir.Module = ir.Module('main')

        # Current Builder
        self.builder: ir.IRBuilder = ir.IRBuilder()

        self.env: Environment = Environment()

        # # Counter for unique block names
        # self.counter: int = 0

        # # Environment reference for the currently compiling scope
        # self.env: Environment = env if env is not None else Environment()

        # # Temporary keeping track of errors
        # self.errors: list[str] = []

        # # Initialize Builtin functions and values
        # self.__initialize_builtins()

        # # Keeps a reference to the compiling loop blocks
        # self.breakpoints: list[ir.Block] = []
        # self.continues: list[ir.Block] = []

        # # Keeps a reference to parsed pallets
        # self.global_parsed_pallets: dict[str, Program] = {}

    def __initialize_builtins(self) -> None:
        def __init_print() -> ir.Function:
            fnty: ir.FunctionType = ir.FunctionType(
                self.type_map['int'],
                [ir.IntType(8).as_pointer()],
                var_arg=True
            )
            return ir.Function(self.module, fnty, 'printf')

        def __init_booleans() -> tuple[ir.GlobalVariable, ir.GlobalVariable]:
            bool_type: ir.Type = self.type_map['bool']

            true_var = ir.GlobalVariable(self.module, bool_type, 'true')
            true_var.initializer = ir.Constant(bool_type, 1)
            true_var.global_constant = True

            false_var = ir.GlobalVariable(self.module, bool_type, 'false')
            false_var.initializer = ir.Constant(bool_type, 0)
            false_var.global_constant = True

            return true_var, false_var
        
        # def __init_c_std_library() -> None:
        #     strlen_ty = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=False)
        #     strlen_func = ir.Function(self.module, strlen_ty, name="strlen")

        #     malloc_ty = ir.FunctionType(ir.IntType(8).as_pointer(), [ir.IntType(32)], var_arg=False)
        #     malloc_func = ir.Function(self.module, malloc_ty, name="malloc")

        #     strcpy_ty = ir.FunctionType(ir.IntType(8).as_pointer(), [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()], var_arg=False)
        #     strcpy_func = ir.Function(self.module, strcpy_ty, name="strcpy")

        #     self.env.define('strlen', strlen_func, ir.IntType(32))
        #     self.env.define('malloc', malloc_func, ir.IntType(8).as_pointer())
        #     self.env.define('strcpy', strcpy_func, ir.IntType(8).as_pointer())
        
        self.env.define('printf', __init_print(), ir.IntType(32))
        
        true_var, false_var = __init_booleans()
        self.env.define('true', true_var, true_var.type)
        self.env.define('false', false_var, false_var.type)

        # __init_c_std_library()

    def __increment_counter(self) -> int:
        self.counter += 1
        return self.counter

    def compile(self, node: Node) -> None:
        """ Main Recursive loop for compiling the AST """
        match node.type():
            case NodeType.Program:
                self.__visit_program(node)

            # Statements
            case NodeType.ExpressionStatement:
                self.__visit_expression_statement(node)
            case NodeType.LetStatement:
                self.__visit_let_statement(node)
            # case NodeType.FunctionStatement:
            #     self.__visit_function_statement(node)
            # case NodeType.BlockStatement:
            #     self.__visit_block_statement(node)
            # case NodeType.ReturnStatement:
            #     self.__visit_return_statement(node)
            # case NodeType.AssignStatement:
            #     self.__visit_assign_statement(node)
            # case NodeType.IfStatement:
            #     self.__visit_if_statement(node)
            # case NodeType.WhileStatement:
            #     self.__visit_while_statement(node)
            # case NodeType.BreakStatement:
            #     self.__visit_break_statement(node)
            # case NodeType.ContinueStatement:
            #     self.__visit_continue_statement(node)
            # case NodeType.ForStatement:
            #     self.__visit_for_statement(node)
            # case NodeType.ImportStatement:
            #     self.__visit_import_statement(node)

            # # Expressions
            case NodeType.InfixExpression:
                self.__visit_infix_expression(node)
            # case NodeType.CallExpression:
            #     self.__visit_call_expression(node)
            # case NodeType.PostfixExpression:
            #     self.__visit_postfix_expression(node)

    # region Visit Methods
    def __visit_program(self, node: Program) -> None:
        # Compile the body
        # for stmt in node.statements:
        #     self.compile(stmt)
        func_name: str ="main"
        param_types: list[ir.Type] = []
        return_type: ir.Type = self.type_map["int"]

        fnty = ir.FunctionType(return_type, param_types)
        func = ir.Function(self.module, fnty, name=func_name)

        block = func.append_basic_block(f"{func_name}_entry")

        self.builder = ir.IRBuilder(block)

        for stmt in node.statements:
            self.compile(stmt)

        return_value: ir.Constant = ir.Constant(self.type_map["int"], 69)
        self.builder.ret(return_value)
        

    # region Statements
    def __visit_expression_statement(self, node: ExpressionStatement) -> None:
        self.compile(node.expr)

    def __visit_let_statement(self, node: LetStatement) -> None:
        name: str = node.name.value
        value: Expression = node.value
        value_type: str  = node.value_type 

        value, Type = self.__resolve_value(node=value)

        if self.env.lookup(name) is None:
            # Define and allocate the variable
            ptr = self.builder.alloca(Type)

            # Storing the value to the pointer
            self.builder.store(value, ptr)

            # Add the variable to the environment
            self.env.define(name, ptr, Type)
        else:
            ptr, _ = self.env.lookup(name)
            self.builder.store(value, ptr)
        
    # region Expressions
    def __visit_infix_expression(self, node: InfixExpression) -> None:
        operator: str = node.operator
        left_value, left_type = self.__resolve_value(node.left_node)
        right_value, right_type = self.__resolve_value(node.right_node)

    
        # if isinstance(left_type, ir.IntType) and isinstance(right_type, ir.FloatType):
        #     left_value = self.builder.sitofp(left_value, ir.FloatType())
        #     left_type = ir.FloatType()
        # if isinstance(left_type, ir.FloatType) and isinstance(right_type, ir.IntType):
        #     right_value = self.builder.sitofp(right_value, ir.FloatType())
        #     right_type = ir.FloatType()

        value = None
        Type = None
        if isinstance(right_type, ir.IntType) and isinstance(left_type, ir.IntType):
            Type = self.type_map['int']
            match operator:
                case '+':
                    value = self.builder.add(left_value, right_value)
                case '-':
                    value = self.builder.sub(left_value, right_value)
                case '*':
                    value = self.builder.mul(left_value, right_value)
                case '/':
                    value = self.builder.sdiv(left_value, right_value)
                case '%':
                    value = self.builder.srem(left_value, right_value)
                case '^':
                    pass
        #         case '<':
        #             value = self.builder.icmp_signed('<', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '<=':
        #             value = self.builder.icmp_signed('<=', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '>':
        #             value = self.builder.icmp_signed('>', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '>=':
        #             value = self.builder.icmp_signed('>=', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '==':
        #             value = self.builder.icmp_signed('==', left_value, right_value)
        #             Type = ir.IntType(1)
                
        elif isinstance(right_type, ir.FloatType) and isinstance(left_type, ir.FloatType):
            Type = ir.FloatType()
            match operator:
                case '+':
                    value = self.builder.fadd(left_value, right_value)
                case '-':
                    value = self.builder.fsub(left_value, right_value)
                case '*':
                    value = self.builder.fmul(left_value, right_value)
                case '/':
                    value = self.builder.fdiv(left_value, right_value)
                case '%':
                    value = self.builder.frem(left_value, right_value)
                case '^':
                   
                    pass
        #         case '<':
        #             value = self.builder.fcmp_ordered('<', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '<=':
        #             value = self.builder.fcmp_ordered('<=', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '>':
        #             value = self.builder.fcmp_ordered('>', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '>=':
        #             value = self.builder.fcmp_ordered('>=', left_value, right_value)
        #             Type = ir.IntType(1)
        #         case '==':
        #             value = self.builder.fcmp_ordered('==', left_value, right_value)
        #             Type = ir.IntType(1)

        # Strings
        # elif isinstance(right_type, ir.PointerType) and isinstance(left_type, ir.PointerType):
        #     # Type = ir.PointerType()
            
        #     str_ptr1 = self.builder.gep(left_value, [ir.IntType(32)(0), ir.IntType(32)(0)], name="str_ptr1")
        #     str_ptr2 = self.builder.gep(right_value, [ir.IntType(32)(0), ir.IntType(32)(0)], name="str_ptr2")

        #     len1 = self.builder.call(
        #         self.builder.function.module.globals.get("strlen"),
        #         [str_ptr1],
        #         name="len1"
        #     )

        #     len2 = self.builder.call(
        #         self.builder.function.module.globals.get("strlen"),
        #         [str_ptr2],
        #         name="len2"
        #     )

        #     # Allocate Memory
        #     total_length = self.builder.add(len1, len2)
        #     concat_ptr = self.builder.call(
        #         self.builder.function.module.globals.get("malloc"),
        #         [total_length],
        #         name="concat_ptr"
        #     )

        #     # Copy the first string (left_value) into the allocated memory
        #     self.builder.call(
        #         self.builder.function.module.globals.get("strcpy"),
        #         [concat_ptr, str_ptr1],
        #         name="copy_ptr1"
        #     )

        #     # Calculate the offset for appending the second string (right_value)
        #     offset_ptr2 = self.builder.gep(concat_ptr, [len1], name="offset_ptr2")

        #     # Copy the second string (right_value) into the allocated memory at the offset position
        #     self.builder.call(
        #         self.builder.function.module.globals.get("strcpy"),
        #         [offset_ptr2, str_ptr2],
        #         name="copy_ptr1"
        #     )

        #     value = concat_ptr

        #     Type = ir.ArrayType(ir.IntType(8).as_pointer(), int(total_length.constant))

        return value, Type
    
    # def __visit_call_expression(self, node: CallExpression) -> tuple[ir.Instruction, ir.Type]:
    #     name: str = node.function.value
    #     params: list[Expression] = node.arguments

    #     args = []
    #     types = []
    #     if len(params) > 0:
    #         for x in params:
    #             p_val, p_type = self.__resolve_value(x)
    #             args.append(p_val)
    #             types.append(p_type)

    #     match name:
    #         case 'printf':
    #             ret = self.builtin_printf(params=args, return_type=types[0])
    #             ret_type = self.type_map['int']
    #         case _:
    #             func, ret_type = self.env.lookup(name)
    #             ret = self.builder.call(func, args)
        
    #     return ret, ret_type
    
    # def __visit_prefix_expression(self, node: PrefixExpression) -> tuple[ir.Value, ir.Type]:
    #     operator: str = node.operator
    #     right_node: Expression = node.right_node

    #     right_value, right_type = self.__resolve_value(right_node)

    #     Type = None
    #     value = None
    #     if isinstance(right_type, ir.FloatType):
    #         Type = ir.FloatType()
    #         match operator:
    #             case '-':
    #                 value = self.builder.fmul(right_value, ir.Constant(ir.FloatType(), -1.0))
    #             case '!':
    #                 value = ir.Constant(ir.IntType(1), 0)
    #     elif isinstance(right_type, ir.IntType):
    #         Type = ir.IntType(32)
    #         match operator:
    #             case '-':
    #                 value = self.builder.mul(right_value, ir.Constant(ir.IntType(32), -1))
    #             case '!':
    #                 value = self.builder.not_(right_value)

    #     return value, Type
    
    # def __visit_postfix_expression(self, node: PostfixExpression) -> None:
    #     left_node: IdentifierLiteral = node.left_node
    #     operator: str = node.operator

    #     if self.env.lookup(left_node.value) is None:
    #         self.errors.append(f"COMPILE ERROR: Identifier {left_node.value} has not been declared before it was used in a PostfixExpression.")
    #         return

    #     var_ptr, _ = self.env.lookup(left_node.value)
    #     orig_value = self.builder.load(var_ptr)

    #     value = None
    #     match operator:
    #         case "++":
    #             if isinstance(orig_value.type, ir.IntType):
    #                 value = self.builder.add(orig_value, ir.Constant(ir.IntType(32), 1))
    #             elif isinstance(orig_value.type, ir.FloatType):
    #                 value = self.builder.fadd(orig_value, ir.Constant(ir.FloatType(), 1.0))
    #         case "--":
    #             if isinstance(orig_value.type, ir.IntType):
    #                 value = self.builder.sub(orig_value, ir.Constant(ir.IntType(32), 1))
    #             elif isinstance(orig_value.type, ir.FloatType):
    #                 value = self.builder.fsub(orig_value, ir.Constant(ir.FloatType(), 1.0))

    #     self.builder.store(value, var_ptr)

    # endregion
    
    # endregion
        
    # region Helper Methods
    def __resolve_value(self, node: Expression) -> tuple[ir.Value, ir.Type]:
        """ Resolves a value and returns a tuple (ir_value, ir_type) """
        match node.type():
            # Literals
            case NodeType.IntegerLiteral:
                node: IntegerLiteral = node
                value, Type = node.value, self.type_map['int']
                return ir.Constant(Type, value), Type
            case NodeType.FloatLiteral:
                node: FloatLiteral = node
                value, Type = node.value, self.type_map['float']
                return ir.Constant(Type, value), Type
            case NodeType.IdentifierLiteral:
                node: IdentifierLiteral = node
                ptr, Type = self.env.lookup(node.value)
                return self.builder.load(ptr), Type
            # case NodeType.BooleanLiteral:
            #     node: BooleanLiteral = node
            #     return ir.Constant(ir.IntType(1), 1 if node.value else 0), ir.IntType(1)
            # case NodeType.StringLiteral:
            #     node: StringLiteral = node
            #     string, Type = self.__convert_string(node.value)
            #     return string, Type
            
            # Expression Values
            case NodeType.InfixExpression:
                return self.__visit_infix_expression(node)
            # case NodeType.CallExpression:
            #     return self.__visit_call_expression(node)
            # case NodeType.PrefixExpression:
            #     return self.__visit_prefix_expression(node)

    def __convert_string(self, string: str) -> tuple[ir.Constant, ir.ArrayType]:
        string = string.replace('\\n', '\n\0')
        
        fmt: str = f"{string}\0"
        c_fmt: ir.Constant = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)), bytearray(fmt.encode("utf8")))

        # Make the global variable for the string
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f'__str_{self.__increment_counter()}')
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt

        return global_fmt, global_fmt.type
    # endregion
        
    # region
    def builtin_printf(self, params: list[ir.Instruction], return_type: ir.Type) -> None:
        """ Basic C builtin printf """
        func, _ = self.env.lookup('printf')

        c_str = self.builder.alloca(return_type)
        self.builder.store(params[0], c_str)

        rest_params = params[1:]

        if isinstance(params[0], ir.LoadInstr):
            """ Printing from a variable load instruction """
            # let a: str = "yeet";
            # print(a)
            c_fmt: ir.LoadInstr = params[0]
            g_var_ptr = c_fmt.operands[0]
            string_val = self.builder.load(g_var_ptr)
            fmt_arg = self.builder.bitcast(string_val, ir.IntType(8).as_pointer())
            return self.builder.call(func, [fmt_arg, *rest_params])
        else:
            """ Printing from a normal string declared within printf """
            # print("yeet %i", 23)
            # TODO: HANDLE PRINTING FLOATS
            fmt_arg = self.builder.bitcast(self.module.get_global(f"__str_{self.counter}"), ir.IntType(8).as_pointer())

            return self.builder.call(func, [fmt_arg, *rest_params])