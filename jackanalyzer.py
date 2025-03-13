from compilation_engine import CompilationEngine
import sys
import os

class JackAnalyzer:
    
    def __init__(self, input_file):


        #check if path exists
        if os.path.exists(input_file):
            try:
                if os.path.isdir(input_file):
                    
                    myfiles = [file for file in os.listdir(input_file) if file.endswith(".jack")]

                    for file in myfiles:
                        
                        engine = CompilationEngine(input_file=file)
                        engine._close()

                else:
                    engine = CompilationEngine(input_file=input_file)
                    engine._close()
            except Exception as e:
                print(f"An error occured : {e}")

        


        else:
            raise FileNotFoundError
        

    


if __name__ == "__main__":

    try:
        input_file = sys.argv[1]

        if input_file:
            JackAnalyzer(input_file)

        else:
            raise FileNotFoundError("Provide the directory or input file.")
    except IndexError as e:
        print(f"Provide parameter for the input file or directory.")

    
