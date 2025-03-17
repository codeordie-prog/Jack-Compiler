import os

class VM_Writer:

    def __init__(self, output_file:str):

        self.output_file_name = os.path.splitext(output_file)[0] + ".vm"

        #open file
        self.output_file = open(self.output_file_name, "w")


        

    def writePush(self, memory_segment:str, index:int):
        #write push command
        self.output_file.write(f"push {memory_segment} {index}\n")


    def writePop(self, memory_segment:str, index:int):
        #write pop command
        self.output_file.write(f"pop {memory_segment} {index}\n")


    def writeArithmetic(self, command:str):
        #write command
        self.output_file.write(f"{command}\n")


    def writeLabel(self, label:str):
        #write label
        self.output_file.write(f"label {label}\n")

    def writeGoto(self, label:str):
        #write Goto
        self.output_file.write(f"goto {label}\n")


    def writeIf(self, label:str):
        #write if
        self.output_file.write(f"if-goto {label}\n")

    def writeCall(self, name:str, nArgs:int):
        #write call
        self.output_file.write(f"call {name} {nArgs}\n")

    def writeFunction(self, name:str, nLocals:int):
        #write function
        self.output_file.write(f"function {name} {nLocals}\n")
    
    def writeReturn(self):
        #write return
        self.output_file.write(f"return\n")

    def close(self):
        self.output_file.close()

    