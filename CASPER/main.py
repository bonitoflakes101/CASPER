from flask import Flask, request, render_template, jsonify
from Lexer import Lexer
from Parser import build_parser

app = Flask(__name__)

LEXER_DEBUG = True
PARSER_DEBUG = True

@app.route("/", methods=["GET", "POST"])
def home():
    code = ""
    lexer_results = []
    illegal_tokens = []
    parser_output = ""

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
                # parser_output = str(ast)
                parser_output = "No Syntax Error"
            except SyntaxError as e:
                parser_output = str(e)  
            except Exception as e:
                parser_output = f"Unexpected Error: {str(e)}"


    return render_template(
        "index.html",
        code=code,
        lexer_results=lexer_results,
        output="\n".join(illegal_tokens) if illegal_tokens else parser_output,
    )

if __name__ == "__main__":
    app.run(debug=True)
