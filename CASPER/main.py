# from Lexer import Lexer
# from Parser import Parser
# from AST import Program
# from Compiler import Compiler
# import json


# from llvmlite import ir
# import llvmlite.binding as llvm
# from ctypes import CFUNCTYPE, c_int, c_float

# LEXER_DEBUG: bool = True
# PARSER_DEBUG: bool = False
# COMPILER_DEBUG: bool = False

# if __name__ == '__main__':
#     with open("tests/lexer.lime", "r") as f:
#         code: str = f.read()


#     if LEXER_DEBUG:
#         print("===== LEXER DEBUG =====")
#         debug_lex: Lexer = Lexer(source=code)
#         while debug_lex.current_char is not None:
#             print(debug_lex.next_token())

    # l: Lexer = Lexer(source=code)
    # p: Parser = Parser(lexer=l)

    # program: Program = p.parse_program()
    # if len(p.errors) > 0:
    #     # for parser
    #     # for err in p.errors: 
    #     #     print(err)
    #     exit(1)

    # if PARSER_DEBUG:
    #     print("===== PARSER DEBUG =====")
    

    #     with open("debug/ast.json", "w") as f:
    #         json.dump(program.json(), f, indent=4)
    #     print("Wrote AST to debug/ast.json successfully")

    # c: Compiler = Compiler()
    # c.compile(node=program)

    # # output steps
    # module: ir.Module = c.module
    # module.triple = llvm.get_default_triple()

    # if COMPILER_DEBUG: 
    #     with open("debug/ir.ll", "w") as f:
    #         f.write(str(module))


from flask import Flask, request, render_template
from Lexer import Lexer

app = Flask(__name__)

LEXER_DEBUG: bool = True

@app.route('/', methods=['GET', 'POST'])
def home():
    code = ""
    output = ""
    lexer_results = []  # 

    if request.method == 'POST':
        code = request.form.get('code_input', '') 

        if LEXER_DEBUG:
            output_lines = []
            debug_lex = Lexer(source=code)
            while debug_lex.current_char is not None:
                token = debug_lex.next_token()
                token_type = str(token.type).split(".")[-1]  # token

                if token_type == "ILLEGAL":  # terminal
                    output_lines.append(str(token))
                else:
                    lexer_results.append((token.literal, token_type)) 

            output = "\n".join(output_lines)  # illegal lng sa output
            output = output.strip()  # panlinis lng ng output

    return render_template('index.html', code=code, output=output, lexer_results=lexer_results)

if __name__ == '__main__':
    app.run(debug=True)
