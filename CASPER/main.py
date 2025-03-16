# main.py

from flask import Flask, request, render_template, jsonify
from Lexer import Lexer
from Parser import parse  # <-- New Lark-based parse() function
from Token import TokenType
# from Semantics import run_semantic_analysis  # Only re-enable if you have an AST from the new parser

app = Flask(__name__)

LEXER_DEBUG = True
PARSER_DEBUG = True
SEMANTICS_DEBUG = True  # Would be used only if we can do semantics

@app.route("/", methods=["GET", "POST"])
def home():
    code = ""
    lexer_results = []
    illegal_tokens = []
    parser_output = ""
    semantic_output = ""

    if request.method == "POST":
        code = request.form.get("code_input", "")

        # 1) Run the old Casper lexer if you'd like to highlight tokens or detect "ILLEGAL" tokens
        if LEXER_DEBUG:
            lexer = Lexer(source=code)
            while lexer.current_char is not None:
                token = lexer.next_token()
                token_type = str(token.type.name)

                if token_type == "ILLEGAL":
                    illegal_tokens.append(str(token))
                else:
                    lexer_results.append((token.literal, token_type))

        # 2) If no illegal tokens, we parse the code using the new Lark-based parser
        if PARSER_DEBUG and not illegal_tokens:
            parse_result = parse(code)  # parse() returns either "No Syntax Errors" or an error string

            # Check if parse_result indicates an error
            if parse_result.startswith("Syntax error") or parse_result.startswith("Unexpected error"):
                parser_output = parse_result
            else:
                # No syntax error
                parser_output = parse_result  # Typically "No Syntax Errors"
                
                # -------------------------------------------
                # (Optional) If you want to run semantic analysis,
                # you must have an AST or parse-tree from the new parser.
                # Your current parse(code) function does NOT return an AST;
                # it only returns a string. So for now, we comment out:
                #
                # ast = ???  # You'd need to modify Parser.py to return a parse tree or AST
                # errors = run_semantic_analysis(ast)
                # if errors:
                #     semantic_output = "Semantic Errors:\n" + "\n".join(errors)
                # else:
                #     semantic_output = "Compilation successful."
                #
                # For demonstration, let's just say no errors from semantics:
                semantic_output = "Compilation successful: no lexical or syntax errors (semantic checks disabled)."
                # -------------------------------------------

    # 3) Decide which output message to display
    if illegal_tokens:
        output = "\n".join(illegal_tokens)
    elif parser_output != "No Syntax Errors" and not parser_output.startswith("Compilation successful"):
        # If there's a specific syntax error
        output = parser_output
    else:
        # If everything is fine, show semantic result or a success message
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

    # 1) Lexical checks
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

    # 2) If no lexical errors, do a parse check
    parse_result = parse(code)
    if parse_result.startswith("Syntax error") or parse_result.startswith("Unexpected error"):
        # We can parse out line # from the error string if needed
        import re
        match = re.search(r'line\s+(\d+)', parse_result)
        if match:
            line_no = int(match.group(1))
        else:
            line_no = 1  # fallback

        error_info = {
            "message": parse_result,
            "line": line_no,
            "startColumn": 0,
            "endColumn": 9999
        }
        return jsonify({"errors": [error_info]})

    # 3) Otherwise, no errors found
    return jsonify({"errors": []})

if __name__ == "__main__":
    app.run(debug=True)
