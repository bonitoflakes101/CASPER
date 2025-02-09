from flask import Flask, request, render_template
from Lexer import Lexer
from Parser import Parser

app = Flask(__name__)

LEXER_DEBUG: bool = True
PARSER_DEBUG: bool = True  # Enable Parser Debugging

@app.route('/', methods=['GET', 'POST'])
def home():
    code = ""
    output = ""
    lexer_results = []  
    parser_output = ""
    symbol_table_output = ""

    if request.method == 'POST':
        code = request.form.get('code_input', '')

        # 1. Run the Lexer
        if LEXER_DEBUG:
            output_lines = []
            debug_lex = Lexer(source=code)
            tokens = []
            
            while debug_lex.current_char is not None:
                token = debug_lex.next_token()
                token_type = str(token.type).split(".")[-1]

                if token_type == "ILLEGAL":
                    output_lines.append(str(token))  # Capture illegal tokens
                else:
                    lexer_results.append((token.literal, token_type))
                    tokens.append(token)  # Store tokens for parsing

            output = "\n".join(output_lines).strip()

        # 2. Run the Parser (Without Removing Lexer)
        if PARSER_DEBUG and tokens:
            parser = Parser(tokens)  # Pass the list of tokens to the parser
            parse_result = parser.parse_program()  # Parse and get results

            if isinstance(parse_result, list):
                parser_output = "\n".join(parse_result)  # Show errors if any
            else:
                parser_output = parse_result
                symbol_table_output = str(parser.symbol_table)  # Display symbol table

    return render_template('index.html', 
                           code=code, 
                           output=output, 
                           lexer_results=lexer_results, 
                           parser_output=parser_output,
                           symbol_table_output=symbol_table_output)

if __name__ == '__main__':
    app.run(debug=True)
