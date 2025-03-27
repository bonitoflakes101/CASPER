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
@app.route("/", methods=["GET", "POST"])
def home():
    code = ""
    lexer_results = []
    illegal_tokens = []
    parser_output = ""
    semantic_output = ""
    errors = ""            # Content for the Errors tab
    generated_code = ""    # Placeholder for generated code
    show_error_tab = False  # Flag to indicate whether to show Errors tab

    if request.method == "POST":
        code = request.form.get("code_input", "")

        # 1. Lexical Analysis
        if LEXER_DEBUG:
            lexer = Lexer(source=code)
            while lexer.current_char is not None:
                token = lexer.next_token()
                token_type = str(token.type).split(".")[-1]

                if token_type == "ILLEGAL":
                    illegal_tokens.append(str(token))
                else:
                    lexer_results.append((token.literal, token_type))

        semantic_errors = []  # to store semantic error messages

        # 2. Parsing and Semantic Analysis (if no lexical errors)
        if PARSER_DEBUG and not illegal_tokens:
            parser = build_parser()
            try:
                ast = parser.parse(lexer=Lexer(code))
                parser_output = "No Syntax Error"

                semantic_errors = run_semantic_analysis(ast)
                if semantic_errors:
                    semantic_output = "Semantic Errors:\n" + "\n".join(semantic_errors)
                else:
                    semantic_output = "Compilation successful: no lexical, syntax, or semantic errors detected."

                # Placeholder for generated code
                generated_code = "PLACEHOLDER: SUCCESS"
            except SyntaxError as e:
                parser_output = str(e)
            except Exception as e:
                parser_output = f"Unexpected Error: {str(e)}"

        # 3. Set error content and decide which tab should be active.
        if illegal_tokens:
            errors = "\n".join(illegal_tokens)
            show_error_tab = True
        elif parser_output != "No Syntax Error":
            errors = parser_output
            show_error_tab = True
        elif semantic_errors:
            errors = semantic_output
            show_error_tab = True
        else:
            errors = ""
            show_error_tab = False

        output = semantic_output if semantic_output else "WIP WIP WIP"

    return render_template(
        "index.html",
        code=code,
        lexer_results=lexer_results,
        output=output,
        errors=errors,
        generated_code=generated_code,
        show_error_tab=show_error_tab
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
                "line": token.line_no,
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
        import re
        full_msg = str(e)
        match = re.search(r'line\s+(\d+)', full_msg)
        if match:
            line_no = int(match.group(1))
        else:
            line_no = 1
        error_info = {
            "message": full_msg,
            "line": line_no,
            "startColumn": 0,
            "endColumn": 9999
        }
        return jsonify({"errors": [error_info]})
    
if __name__ == "__main__":
    app.run(debug=True)
