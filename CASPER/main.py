from flask import Flask, request, render_template, jsonify
import io
import sys

from Lexer import Lexer
from Parser import build_parser
from Token import TokenType
from Semantics import run_semantic_analysis
from CodeGen import run_code_generation, CodeGenerator

app = Flask(__name__)


LEXER_DEBUG = True
PARSER_DEBUG = True
SEMANTICS_DEBUG = True

# Global state to store the running program
current_generator = None
program_output = ""

@app.route("/", methods=["GET", "POST"])
def home():
    global current_generator, program_output
    
    code = ""
    lexer_results = []
    illegal_tokens = []
    parser_output = ""
    semantic_output = ""
    errors = ""
    generated_code = ""
    show_error_tab = False
    error_count = 0
    output = ""  # Will hold the final text shown in "Output Terminal"

    if request.method == "POST":
        code = request.form.get("code_input", "")

        # Reset global state
        current_generator = None
        program_output = ""

        # 1. LEXICAL ANALYSIS
        lexer = Lexer(source=code)
        while lexer.current_char is not None:
            token = lexer.next_token()
            token_type = str(token.type).split(".")[-1]
            if token_type == "ILLEGAL":
                illegal_tokens.append(str(token))

        if illegal_tokens:
            error_count += len(illegal_tokens)

        if not illegal_tokens:
            # 2. PARSING
            parser = build_parser()
            try:
                ast = parser.parse(lexer=Lexer(code))
                parser_output = "No Syntax Error"

                # 3. SEMANTIC ANALYSIS
                semantic_errors = run_semantic_analysis(ast)
                if semantic_errors:
                    semantic_output = "Semantic Errors:\n" + "\n".join(semantic_errors)
                    error_count += len(semantic_errors)
                else:
                    # If no semantic errors, set success message
                    semantic_output = "Compilation successful: no lexical, syntax, or semantic errors detected."
                    generated_code = "Code Generation Executed Successfully."

                    # 4. CAPTURE CODE GENERATION OUTPUT
                    backup_stdout = sys.stdout
                    codegen_buffer = io.StringIO()
                    try:
                        sys.stdout = codegen_buffer
                        current_generator = run_code_generation(ast)
                    finally:
                        sys.stdout = backup_stdout

                    # The codegen_buffer now holds whatever the code generator printed
                    program_output = codegen_buffer.getvalue()

                    # We'll combine the success message and the codegen prints
                    output = f"{semantic_output}\n{program_output}"

            except SyntaxError as e:
                parser_output = str(e)
                error_count += 1
            except Exception as e:
                parser_output = f"Unexpected Error: {str(e)}"
                error_count += 1

        # 5. SET ERRORS AND OUTPUT
        if illegal_tokens:
            errors = "\n".join(illegal_tokens)
            show_error_tab = True
        elif parser_output != "No Syntax Error":
            errors = parser_output
            show_error_tab = True
        elif semantic_output.startswith("Semantic Errors"):
            errors = semantic_output
            show_error_tab = True

        # If we never set 'output' above (like in an error case), default it now:
        if not output:
            output = semantic_output or "WIP WIP WIP"

    return render_template(
        "index.html",
        code=code,
        lexer_results=[(t, "") for t in illegal_tokens],
        output=output,               # This shows in the "Output Terminal"
        errors=errors,
        generated_code=generated_code,
        show_error_tab=show_error_tab,
        error_count=error_count
    )


@app.route('/check_errors', methods=['POST'])
def check_errors():
    """Provides quick error-checking for the Monaco editor (AJAX)."""
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

@app.route('/program_status', methods=['GET'])
def program_status():
    """Check if the program is waiting for input."""
    global current_generator, program_output
    
    filtered_output = '\n'.join([line for line in program_output.split('\n') 
                             if not line.startswith('DEBUG:') and 
                                not 'EXECUTE_INPUT_STATEMENT CALLED' in line and
                                not 'Waiting for input...' in line and
                                not 'is_waiting_for_input called' in line])
    
    if current_generator and current_generator.is_waiting_for_input():
        prompt = current_generator.get_input_prompt()
        
        return jsonify({
            "status": "waiting_for_input",
            "prompt": prompt,
            "output": filtered_output  
        })
    else:
        status = "running" if current_generator else "idle"
        
        return jsonify({
            "status": status,
            "output": filtered_output  
        })

@app.route('/provide_input', methods=['POST'])
def provide_input():
    """Handle user input for a running program."""
    global current_generator, program_output
    
    if not current_generator or not current_generator.is_waiting_for_input():
        return jsonify({"error": "Program is not waiting for input"}), 400
    
    user_input = request.json.get('input', '')
    
    filtered_output = '\n'.join([line for line in program_output.split('\n') 
                               if not line.startswith('DEBUG:') and 
                                  not 'EXECUTE_INPUT_STATEMENT CALLED' in line and
                                  not 'Waiting for input...' in line and
                                  not 'is_waiting_for_input called' in line])
    
    program_output = filtered_output + f"\n> {user_input}"
    
    backup_stdout = sys.stdout
    output_buffer = io.StringIO()
    sys.stdout = output_buffer
    
    try:
        fresh_generator = CodeGenerator()
        
        fresh_generator.global_vars = current_generator.global_vars.copy()
        fresh_generator.env_stack = [fresh_generator.global_vars]
        fresh_generator.ast = current_generator.ast
        fresh_generator.debug = False
        

        fresh_generator.input_value = int(user_input) if user_input.isdigit() else user_input
        fresh_generator.waiting_for_input = False
        
        already_got_input = True
        
        backup_stdout2 = sys.stdout
        temp_buffer = io.StringIO()
        sys.stdout = temp_buffer
        
        fresh_generator.generate(fresh_generator.ast)
        
        temp_output = temp_buffer.getvalue()
        
        sys.stdout = backup_stdout2
        
        lines = temp_output.split('\n')
        output_after_input = []
        found_prompt = False
        
        for line in lines:
            if (line.startswith('DEBUG:') or 
                'EXECUTE_INPUT_STATEMENT CALLED' in line or 
                'Waiting for input...' in line or 
                'is_waiting_for_input called' in line):
                continue
            
    
            if "Enter a Number" in line:
                found_prompt = True
                continue
                
        
            if found_prompt:
                output_after_input.append(line)
        
   
        print('\n'.join(output_after_input))
        
     
        current_generator = fresh_generator
        
    except Exception as e:
        print(f"Error processing input: {str(e)}")
    finally:
        sys.stdout = backup_stdout
    
 
    new_output = output_buffer.getvalue().strip()
    if new_output:
        program_output += f"\n{new_output}"
    
    final_output = '\n'.join([line for line in program_output.split('\n') 
                            if not line.startswith('DEBUG:') and 
                               not 'EXECUTE_INPUT_STATEMENT CALLED' in line and
                               not 'Waiting for input...' in line and
                               not 'is_waiting_for_input called' in line])
    
    return jsonify({
        "status": "input_processed",
        "waiting_for_more": current_generator.is_waiting_for_input(),
        "output": final_output
    })

if __name__ == "__main__":
    app.run(debug=True)