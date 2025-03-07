from flask import Flask, request, render_template, jsonify
from Lexer import Lexer
from Parser import build_parser
from Token import TokenType

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

