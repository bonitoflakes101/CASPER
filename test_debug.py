from Parser import build_parser, ASTNode
from CodeGen import run_code_generation, CodeGenerator

# Create a small test program
test_program = "birth { display Day && Night }"

# Parse the program
parser = build_parser()
ast = parser.parse(test_program)

# Run the code generation
generator = run_code_generation(ast)

# Check the debug log
print("Execution complete. Check casper_debug.log for debug output.") 