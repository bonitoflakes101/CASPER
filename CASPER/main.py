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
    
    
    if request.method == "GET":
        current_generator = None
        program_output = ""

    
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
    else:
        # For GET requests, use our default code to test logical operators
        code = ""

    # Reset global state
    current_generator = None
    program_output = ""

    # 1. LEXICAL ANALYSIS
    lexer = Lexer(source=code)
    all_tokens = []  # Changed from lexer_results
    illegal_tokens = []
    while lexer.current_char is not None:
        token = lexer.next_token()
        all_tokens.append(token) # Store all tokens
        token_type = str(token.type).split(".")[-1]
        if token_type == "ILLEGAL":
            illegal_tokens.append(str(token))
            
    # Prepare lexer results for display, perhaps just the token type and literal
    lexer_display_results = [(str(t.type).split(".")[-1], t.literal) for t in all_tokens]

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
        lexer_results=lexer_display_results, # Pass all tokens info
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
    
    # Default response for idle program
    if not current_generator:
        return jsonify({
            "status": "idle",
            "output": program_output
        })
    
    # Filter out debug messages
    filtered_output = '\n'.join([line for line in program_output.split('\n') 
                              if not line.startswith('DEBUG:') and 
                                 not 'EXECUTE_INPUT_STATEMENT CALLED' in line and
                                 not 'is_waiting_for_input called' in line])
    
    # If program is stopped or completed
    if current_generator.stopped or current_generator.completed:
        status = "program_finished" if current_generator.stopped else "idle"
        print(f"DEBUG: /program_status - Program stopped={current_generator.stopped} or completed={current_generator.completed}, status={status}")
        
        # Reset generator if program completed normally
        if current_generator.completed and not current_generator.waiting_for_input:
            current_generator = None
        
        return jsonify({
            "status": status,
            "output": filtered_output
        })
    
    # Check if waiting for input
    if current_generator.is_waiting_for_input():
        prompt = current_generator.get_input_prompt()
        print(f"DEBUG: /program_status - Waiting for input, prompt='{prompt}'")
        
        return jsonify({
            "status": "waiting_for_input",
            "prompt": prompt,
            "output": filtered_output
        })
    
    # Program is running but not waiting for input
    print("DEBUG: /program_status - Program running but not waiting for input")
    return jsonify({
        "status": "running",
        "output": filtered_output
    })

@app.route('/provide_input', methods=['POST'])
def provide_input():
    """Handle user input for a running program."""
    global current_generator, program_output
    
    if not current_generator:
        
        return jsonify({"error": "No program running"}), 400
        
    if not current_generator.is_waiting_for_input():
      
        return jsonify({"error": "Program is not waiting for input"}), 400
        
    if current_generator.stopped:
      
        return jsonify({"error": "Program has been stopped"}), 400
    
    user_input = request.json.get('input', '')
  
    
    # Add the user input to the output
    program_output += f"\n> {user_input}"
    
    # Capture standard output during execution
    backup_stdout = sys.stdout
    output_buffer = io.StringIO()
    sys.stdout = output_buffer
    
    try:
        # Process the input and continue execution
        current_generator.provide_input(user_input)
        
        # Instead of just one generate call, ensure execution continues until either:
        # 1. We hit another input request, or
        # 2. The program completes
        execution_count = 0
        while not current_generator.waiting_for_input and not current_generator.stopped and not current_generator.completed:
          
            current_generator.generate(None)
            execution_count += 1
            if execution_count > 100:  # Safety limit
               
                break
        
    except Exception as e:
        import traceback
 
        traceback.print_exc()
    finally:
        sys.stdout = backup_stdout
    
    # Capture the new output and append it to the existing output
    new_output = output_buffer.getvalue().strip()
    if new_output:
        program_output += f"\n{new_output}"
    
    # Filter debug messages from the final output
    final_output = '\n'.join([line for line in program_output.split('\n') 
                          if not line.startswith('DEBUG:') and 
                           not 'EXECUTE_INPUT_STATEMENT CALLED' in line and
                           not 'Waiting for input...' in line and
                           not 'is_waiting_for_input called' in line])
    
    # Determine the current program status
    is_validation_failed = current_generator.stopped and not current_generator.waiting_for_input
    is_waiting_for_more = current_generator.is_waiting_for_input()
    
    
    
    status_info = {
        "status": "program_finished" if is_validation_failed else "input_processed",
        "waiting_for_more": is_waiting_for_more,
        "output": final_output,
        "prompt": current_generator.get_input_prompt() if is_waiting_for_more else ""
    }
    
    return jsonify(status_info)

@app.route('/stop_program', methods=['POST'])
def stop_program():
    """Stop the currently running program."""
    global current_generator, program_output
    
    if not current_generator:
        return jsonify({"status": "error", "message": "No program running"}), 400
    
    # Set the stopped flag to true and ensure it's not waiting for input
    current_generator.stopped = True
    current_generator.waiting_for_input = False
    
    # Add message to output
    program_output += "\nProgram execution stopped."
    
    return jsonify({
        "status": "success",
        "output": program_output
    })

if __name__ == "__main__":
    app.run(debug=True)