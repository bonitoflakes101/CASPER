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
                    semantic_output = "Compilation successful: no lexical, syntax, or semantic errors detected."

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

@app.route('/check_errors', methods=['POST'])
def check_errors():
    code = request.json.get('code', '')
    lexer = Lexer(code)
    illegal_tokens = []

    while lexer.current_char is not None:
        token = lexer.next_token()
        if token.type == TokenType.ILLEGAL:
            illegal_tokens.append({
                "line": token.line_no ,
                "startColumn": token.position,
                "endColumn": token.position + len(token.literal),
                "message": f"Illegal Token: {token.literal}"
            })

    if illegal_tokens:
        return jsonify({"errors": illegal_tokens})

    parser = build_parser()
    try:
        parser.parse(lexer=Lexer(code))
        return jsonify({"errors": []})
    except SyntaxError as e:
        # e might look like: "Syntax Error:\nUnexpected token: '@hello' at line 4.\nExpected..."
        full_msg = str(e)
        # 1) Find "line <num>"
        import re
        match = re.search(r'line\s+(\d+)', full_msg)
        if match:
            line_no = int(match.group(1))
        else:
            line_no = 1  # fallback

        error_info = {
            "message": full_msg,
            "line": line_no,
            "startColumn": 0,
            "endColumn": 9999  # or the length of that line
        }
        return jsonify({"errors": [error_info]})
    
if __name__ == "__main__":
    app.run(debug=True)
