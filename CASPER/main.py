from flask import Flask, request, render_template, jsonify
from Lexer import Lexer
from Parser import build_parser
from Token import TokenType
from Semantics import run_semantic_analysis  # Import the semantic analysis helper

app = Flask(__name__)

LEXER_DEBUG = True
PARSER_DEBUG = True
SEMANTICS_DEBUG = True  # New flag for semantic analysis debugging

@app.route("/", methods=["GET", "POST"])
def home():
    code = ""
    lexer_results = []
    illegal_tokens = []
    parser_output = ""
    semantic_output = ""

    if request.method == "POST":
        code = request.form.get("code_input", "")

        if LEXER_DEBUG:
            lexer = Lexer(source=code)
            while lexer.current_char is not None:
                token = lexer.next_token()
                token_type = str(token.type).split(".")[-1]

                if token_type == "ILLEGAL":
                    illegal_tokens.append(str(token))
                else:
                    lexer_results.append((token.literal, token_type))

        if PARSER_DEBUG and not illegal_tokens:
            parser = build_parser()
            try:
                ast = parser.parse(lexer=Lexer(code))
                parser_output = "No Syntax Error"

                # Run semantic analysis on the AST
                errors = run_semantic_analysis(ast)
                if errors:
                    semantic_output = "Semantic Errors:\n" + "\n".join(errors)
                else:
                    semantic_output = "Semantic analysis completed successfully."

                # # If SEMANTICS_DEBUG is enabled, append additional debug info.
                # if SEMANTICS_DEBUG:
                #     semantic_output += "\n[SEMANTICS_DEBUG] AST Root Node: " + repr(ast)

            except SyntaxError as e:
                parser_output = str(e)
            except Exception as e:
                parser_output = f"Unexpected Error: {str(e)}"

    output = ""
    if illegal_tokens:
        output = "\n".join(illegal_tokens)
    elif parser_output != "No Syntax Error":
        output = parser_output
    else:
        output = semantic_output

    return render_template(
        "index.html",
        code=code,
        lexer_results=lexer_results,
        output=output,
    )

if __name__ == "__main__":
    app.run(debug=True)
