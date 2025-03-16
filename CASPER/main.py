# main.py

from flask import Flask, request, render_template, jsonify
from Lexer import Lexer
from Parser import parse  
from Token import TokenType
from Semantics import run_semantic_analysis  

app = Flask(__name__)

LEXER_DEBUG = True
PARSER_DEBUG = True
SEMANTICS_DEBUG = True  # Only used if we do semantic checks

@app.route("/", methods=["GET", "POST"])
def home():
    code = ""
    lexer_results = []
    illegal_tokens = []
    parser_output = ""
    semantic_output = ""

    if request.method == "POST":
        code = request.form.get("code_input", "")

        # 1) Lexical checks
        if LEXER_DEBUG:
            lexer = Lexer(source=code)
            while lexer.current_char is not None:
                token = lexer.next_token()
                token_type = str(token.type.name)
                if token_type == "ILLEGAL":
                    illegal_tokens.append(str(token))
                else:
                    lexer_results.append((token.literal, token_type))

        # 2) If no lexical errors, parse
        if PARSER_DEBUG and not illegal_tokens:
            # NEW: parse() returns a dict: {"ast": <ASTNode>, "error": <str or None>}
            result = parse(code)

            if result["error"]:
                parser_output = result["error"]
            else:
                ast = result["ast"]
                parser_output = "No Syntax Error"

                # Now run semantics
                errors = run_semantic_analysis(ast)
                if errors:
                    semantic_output = "Semantic Errors:\n" + "\n".join(errors)
                else:
                    semantic_output = "No lexical, syntax, or semantic errors!"
    # 3) Decide final output
    if illegal_tokens:
        output = "\n".join(illegal_tokens)
    elif parser_output and parser_output != "No Syntax Error" and not parser_output.startswith("Compilation successful"):
        output = parser_output
    else:
        output = semantic_output if semantic_output else "No lexical or syntax errors detected."

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

    # 1) Lexical
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

    # 2) Parse with the dictionary approach
    result = parse(code)

    if result["error"]:
        parse_result = result["error"]

        import re
        match_line = re.search(r'line\s+(\d+)', parse_result, re.IGNORECASE)
        match_col = re.search(r'column\s+(\d+)', parse_result, re.IGNORECASE)

        line_no = int(match_line.group(1)) if match_line else 1
        col_no = int(match_col.group(1)) if match_col else 1

        error_info = {
            "message": parse_result,
            "line": line_no,
            "startColumn": col_no,
            "endColumn": col_no + 1
        }
        return jsonify({"errors": [error_info]})
    else:
        # No syntax error
        return jsonify({"errors": []})

if __name__ == "__main__":
    app.run(debug=True)
