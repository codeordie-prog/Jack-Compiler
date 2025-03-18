from compilation_engine import CompilationEngine
import sys
import os

class JackAnalyzer:
    
    def __init__(self, input_path):
        # Check if path exists
        if os.path.exists(input_path):
            try:
                if os.path.isdir(input_path):
                    # Process all .jack files in the directory
                    jack_files = [file for file in os.listdir(input_path) if file.endswith(".jack")]

                    print(jack_files)
                    
                    for file in jack_files:
                        # Create full path by joining directory and filename
                        full_file_path = os.path.join(input_path, file)
                        print(f"Processing file: {full_file_path}")
                        
                        # Pass the full path to the CompilationEngine
                        engine = CompilationEngine(input_file=full_file_path)
                        engine._compileClass()  # Start compilation
                        engine._close()
                else:
                    # Process a single file
                    print(f"Processing file: {input_path}")
                    engine = CompilationEngine(input_file=input_path)
                    engine._compileClass()  # Start compilation
                    engine._close()
            except Exception as e:
                print(f"Error compiling {input_path}: {e}")
                import traceback
                traceback.print_exc()  # This will print the full stack trace
        else:
            raise FileNotFoundError(f"Path not found: {input_path}")

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print("Usage: python jackanalyzer.py <input_file_or_directory>")
            sys.exit(1)
            
        input_path = sys.argv[1]
        JackAnalyzer(input_path)
    except Exception as e:
        print(f"Error: {e}")

    
