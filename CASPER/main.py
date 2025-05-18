from flask import Flask, request, render_template, jsonify
import io
import sys
from enum import Enum

from Lexer import Lexer
from Parser import build_parser
from Token import TokenType, Token
from Semantics import run_semantic_analysis
from CodeGen import run_code_generation, CodeGenerator

app = Flask(__name__)

class ListBasedLexer: # bridge between the lexer and the parser
    def __init__(self, raw_tokens_list):
        self.tokens_iterator = iter(raw_tokens_list) # iter = bookmark for the tokens_list

    def token(self): # called on demand by the parser
        while True:
            try:
                tok = next(self.tokens_iterator) # fetches the next token from the tokens_iterator
            except StopIteration:
                return None 

            if tok.type == TokenType.EOF: 
                return None 

            if tok.type == TokenType.ILLEGAL or tok.type == TokenType.COMMENT:
                continue # Parser skips these, loop to get next raw token

            ply_token_obj = type('PlyToken', (), {})() # creates a generic empty object

            if isinstance(tok.type, Enum):
                ply_token_obj.type = tok.type.name # tok.type.name = string representation of the tok.type = "BIRTH" or "IDENT"
            else:
                ply_token_obj.type = tok.type # tok.type =  TokenType.BIRTH or TokenType.IDENT

            ply_token_obj.value = tok.literal # tok.literal = "birth" or "$name"
            ply_token_obj.lineno = tok.line_no # tok.line_no = 1
            ply_token_obj.lexpos = tok.position # tok.position = 0
            
            return ply_token_obj

# --- Default Toggle States --- 
# Used for GET requests or if not specified in POST
DEFAULT_DISPLAY_LEXER = True
DEFAULT_EXECUTE_PARSER = True
DEFAULT_EXECUTE_SEMANTICS = True
DEFAULT_EXECUTE_CODEGEN = True
# --- End Default Toggle States ---

# Global state to store the running program
current_generator = None
program_output = ""

@app.route("/", methods=["GET", "POST"])
def home():
    global current_generator, program_output
    
    # --- Determine Flag States from Request ---
    if request.method == 'POST':
        # Read from form checkboxes (if checkbox is unchecked, key won't be in form)
        display_lexer = 'display_lexer' in request.form
        execute_parser = 'execute_parser' in request.form
        execute_semantics = 'execute_semantics' in request.form
        execute_codegen = 'execute_codegen' in request.form
    else: # GET request or initial load
        # Use default values from above
        display_lexer = DEFAULT_DISPLAY_LEXER
        execute_parser = DEFAULT_EXECUTE_PARSER
        execute_semantics = DEFAULT_EXECUTE_SEMANTICS
        execute_codegen = DEFAULT_EXECUTE_CODEGEN
    # --- End Flag State Determination ---
    
    # --- Debug Logging: Print flag states ---
    print(f"[DEBUG] Received Flags - Method: {request.method}")
    print(f"  Display Lexer: {display_lexer}")
    print(f"  Execute Parser: {execute_parser}")
    print(f"  Execute Semantics: {execute_semantics}")
    print(f"  Execute CodeGen: {execute_codegen}")
    # --- End Debug Logging ---
    
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
    ast = None # Initialize AST

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
    # Populate all_tokens and illegal_tokens by consuming the lexer once
    temp_lexer_for_all_tokens = Lexer(source=code) # Use a temporary lexer instance for this
    while True:
        token = temp_lexer_for_all_tokens.next_token() # call next_token() from Lexer class
        all_tokens.append(token) # appends whatever token to the all_tokens list
        token_type_str = str(token.type).split(".")[-1]
        if token_type_str == "ILLEGAL":
            illegal_tokens.append(str(token)) # appends the illegal token to the illegal_tokens list
        if token.type == TokenType.EOF: # Stop after appending EOF
            break
            
    # Prepare lexer results for display *only if* flag is set
    lexer_display_results = [(str(t.type).split(".")[-1], t.literal) for t in all_tokens if t.type != TokenType.ILLEGAL] if display_lexer else []
    print(f"[DEBUG] Lexer Results Display Enabled: {display_lexer}, Items: {len(lexer_display_results)}")

    # --- Conditional Execution based on Flags ---
    parser_successful = False
    semantics_successful = False

    if illegal_tokens:
        # Lexical errors: Set errors and skip messages
        error_count += len(illegal_tokens)
        errors = "Lexical Errors:\n" + "\n".join(illegal_tokens)
        show_error_tab = True
        parser_output = "Skipped due to Lexical Errors"
        semantic_output = "Skipped due to Lexical Errors"
        generated_code = "Skipped due to Lexical Errors"
        output = "Processing stopped: Lexical Errors found."
    
    elif not execute_parser:
        # --- Parser Skipped by Toggle ---
        print("[DEBUG] Skipping Parser (execute_parser=False)")
        parser_output = "Skipped by user toggle."
        semantic_output = "Skipped (Parser toggle off)."
        generated_code = "Skipped (Parser toggle off)."
        output = "Processing stopped at Parser stage (toggle)."

    else:
        # --- Attempt Parser Execution --- 
        parser = build_parser() # builds the parser
        try:
            # Use ListBasedLexer with the pre-generated all_tokens list
            parser_lexer = ListBasedLexer(all_tokens)
            ast = parser.parse(lexer=parser_lexer) # parses the code, builds the AST if no errors, repeatedly calls ListBasedLexer.token()
            # ---- ADDED FOR AST PRINTING ----
            if ast:
                print("\n--- Abstract Syntax Tree (AST) ---")
                print(ast)
                print("--------------------------------")
            # ---- END AST PRINTING ----
            parser_output = "No Syntax Errors Found."
            parser_successful = True # Mark parser as successful

            # --- Check Semantics ---
            if not execute_semantics:
                # --- Semantics Skipped by Toggle ---
                print("[DEBUG] Skipping Semantics (execute_semantics=False)")
                semantic_output = "Skipped by user toggle."
                generated_code = "Skipped (Semantics toggle off)."
                output = "Processing stopped at Semantics stage (toggle)."
            else:
                # --- Attempt Semantics Execution ---
                semantic_errors = run_semantic_analysis(ast)
                if semantic_errors:
                    # Semantic errors found
                    semantic_output = "Semantic Errors:\n" + "\n".join(semantic_errors)
                    error_count += len(semantic_errors)
                    errors = semantic_output
                    show_error_tab = True
                    generated_code = "Skipped due to Semantic Errors"
                    output = "Processing stopped: Semantic Errors found."
                else:
                    # Semantics successful
                    semantic_output = "No Semantic Errors Found."
                    semantics_successful = True # Mark semantics as successful

                    # --- Check Code Generation ---
                    if not execute_codegen:
                        # --- CodeGen Skipped by Toggle ---
                        print("[DEBUG] Skipping CodeGen (execute_codegen=False)")
                        generated_code = "Skipped by user toggle."
                        output = "Processing stopped at Code Generation stage (toggle)."
                    else:
                        # --- Attempt CodeGen Execution ---
                        print("[DEBUG] Executing CodeGen")
                        generated_code = "Code Generation Executed."
                        backup_stdout = sys.stdout
                        codegen_buffer = io.StringIO()
                        try:
                            sys.stdout = codegen_buffer
                            current_generator = run_code_generation(ast)
                        finally:
                            sys.stdout = backup_stdout
                        
                        program_output = codegen_buffer.getvalue()
                        # Use the specific semantic success message here for clarity
                        output = f"No Semantic Errors Found.\n{program_output}"

        except SyntaxError as e:
            # Syntax error during parsing
            parser_output = f"Syntax Error: {str(e)}"
            error_count += 1
            errors = parser_output
            show_error_tab = True
            semantic_output = "Skipped due to Syntax Errors"
            generated_code = "Skipped due to Syntax Errors"
            output = "Processing stopped: Syntax Errors found."
        except Exception as e:
            # Unexpected error (likely during parsing or semantics)
            parser_output = f"Unexpected Error: {str(e)}"
            error_count += 1
            errors = parser_output
            show_error_tab = True
            # Determine where the error likely occurred based on success flags
            if not parser_successful:
                semantic_output = "Skipped due to Unexpected Parsing Error"
                generated_code = "Skipped due to Unexpected Parsing Error"
                output = "Processing stopped: Unexpected Parsing Error."
            elif not semantics_successful: # Parser succeeded, error likely in semantics
                semantic_output = "Skipped due to Unexpected Semantic Error"
                generated_code = "Skipped due to Unexpected Semantic Error"
                output = "Processing stopped: Unexpected Semantic Error."
            else: # Error likely during codegen
                 semantic_output = "No Semantic Errors Found."
                 generated_code = "Skipped due to Unexpected Error during CodeGen"
                 output = "Processing stopped: Unexpected Error during CodeGen."


    # --- Final Output Assignment (if not set above) ---
    if not output and not errors:
         # Stages might have been skipped by toggles without errors.
         if execute_parser and parser_successful and execute_semantics and semantics_successful and execute_codegen:
              # Should have been set during codegen, but as a fallback
              output = "Processing completed (all enabled stages successful)."
         elif execute_parser and parser_successful and execute_semantics and semantics_successful:
              output = "Semantic analysis completed. Code generation skipped by toggle."
         elif execute_parser and parser_successful:
              output = "Parsing completed. Semantic analysis skipped by toggle."
         elif display_lexer:
              output = "Lexer display complete. Parsing skipped by toggle."
         else:
              output = "No stages selected for execution or display."
         print(f"[DEBUG] Final Output (no errors, not set earlier): {output}")
    elif not output and errors:
         # Fallback if errors occurred but output wasn't set explicitly
         output = f"Processing failed. Check Errors tab ({error_count} errors)."
         print(f"[DEBUG] Final Output (errors, not set earlier): {output}")


    return render_template(
        "index.html",
        code=code,
        # Pass results and statuses
        lexer_results=lexer_display_results, 
        parser_output=parser_output, 
        semantic_output=semantic_output, 
        generated_code=generated_code, # Status message for codegen
        output=output,                 # Final output for the terminal
        errors=errors,
        show_error_tab=show_error_tab,
        error_count=error_count,
        # Pass flag states to template for checkbox initial state
        display_lexer=display_lexer,
        execute_parser=execute_parser,
        execute_semantics=execute_semantics,
        execute_codegen=execute_codegen
    )


@app.route('/check_errors', methods=['POST'])
def check_errors():
    """Provides quick error-checking for the Monaco editor (AJAX)."""
    code = request.json.get('code', '')
    lexer = Lexer(code)
    illegal_tokens_list_for_ajax = [] # Renamed to avoid conflict
    
    # Lex once to get all tokens for AJAX check
    ajax_lexer_instance = Lexer(code)
    all_ajax_tokens = []
    while True:
        token = ajax_lexer_instance.next_token()
        all_ajax_tokens.append(token)
        if token.type == TokenType.ILLEGAL:
            illegal_tokens_list_for_ajax.append({ # Use the renamed list
                "line": token.line_no,
                "startColumn": token.position,
                "endColumn": token.position + len(token.literal),
                "message": f"Illegal Token: {token.literal}"
            })
        if token.type == TokenType.EOF:
            break

    if illegal_tokens_list_for_ajax: # Check the renamed list
        return jsonify({"errors": illegal_tokens_list_for_ajax})

    parser = build_parser()
    try:
        # Use ListBasedLexer for parsing in AJAX check as well
        ajax_parser_lexer = ListBasedLexer(all_ajax_tokens)
        parser.parse(lexer=ajax_parser_lexer)
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