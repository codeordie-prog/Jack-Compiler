import os
from tokenizer import Tokenizer
from vm_writer import VM_Writer
from symboltable import SymbolTable, VariableNotFoundError

class CompilationEngine:

   
    def __init__(self, input_file):

        """
        Initializes the compilation engine

        Args:

        input_file (str): Path to the input.jack file.
        output_file (str): Path to the output XML file.
        
        """

        self.output_file = os.path.splitext(input_file)[0] + ".XML"
        self.input_file = input_file
        self.tokenizer = Tokenizer(input_file=input_file)
        self.vm_writer = VM_Writer(input_file.replace(".jack", ".vm"))
        self.built_in_classes = ["Math", "String", "Array", "Output", "Screen", "Keyboard", "Memory", "Sys"]
        self.symbol_table = SymbolTable()
        self.class_name = ""
        self.tokenizer.index = 0
        self.indent_level = 0
        self._label_num=0
        self.output = open(self.output_file, "w")

        if self.tokenizer.tokens and len(self.tokenizer.tokens) > 0:
            self.tokenizer.current_token = self.tokenizer.tokens[0]
            
        

    
    def _write(self, line):
        """
        Writes a line to the output file with indentation
        
        """

        indent = " " * self.indent_level
        self.output.write(indent + line + "\n")

    def _write_token(self, token):
        """
        Writes the current token in XML format
        """
        token_type = self.tokenizer.tokenType()

        if token_type == "KEYWORD":
            xml_line = f"<keyword>{token}</keyword>"
        elif token_type == "SYMBOL":
            # Escape symbols for XML
            if token == "<":
                token = "&lt;"
            elif token == ">":
                token = "&gt;"
            elif token == "&":
                token = "&amp;"
            xml_line = f"<symbol>{token}</symbol>"
        elif token_type == "INT_CONST":
            xml_line = f"<integerConstant>{token}</integerConstant>"
        elif token_type == "STRING_CONST":
            xml_line = f"<stringConstant>{self.tokenizer.stringVal()}</stringConstant>"
        elif token_type == "IDENTIFIER":
            xml_line = f"<identifier>{token}</identifier>"
        else:
            xml_line = token

        self._write(xml_line)


    def _expect_token(self, expected_token:list):
        """
        Checks if the current token matches the expected token.
        Raises a SyntaxError with a line number if it does not match.
        """
        # Assuming tokens_with_line_numbers is a list of (token, line_number) pairs:
        current = self.tokenizer.current_token
        # Retrieve the line number for the current token
        line_number = self.tokenizer.tokens_with_line_numbers[self.tokenizer.index][1] #get line number from the tuple
        
        if current not in expected_token:
            raise SyntaxError(f"Error on line {line_number}: expected either '{", ".join(map(str, expected_token))}' but received '{current}'")
        


    #generate label helper
    def _generate_label(self, prefix: str) -> str:
        self._label_num += 1
        return f"{prefix}_{self._label_num}"

    #mapping vm segments
    def _get_vm_segment(self, kind:str)->str:
        return "this" if kind == "field"  else kind

    def _compileClass(self):
        #compiles a complete class - its the first method to be called by the engine
        #rule class: 'class' className '{' classVarDec* subroutineDec* '}'

        #write all tokens
        #print(self.tokenizer.tokens)

       # self._write("<class>")

        #increase identation level for the class
        #self.indent_level += 1

        #---------------------------------
        #process the 'class' keyword
        #-------------------------------
        self.tokenizer.advance() #advance from class keyword

        self.class_name = self.tokenizer.current_token #save class name
        self.tokenizer.advance()



        #process the opening bracket '{'
        #self._expect_token(['{'])
       # self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance() # move to the first classVarDec or subroutines if it lacks the classVar


        #process classVar
        while self.tokenizer.current_token in ["static", "field"]:
            self._compileClassVarDec() #compile the variables


        # process subroutines
        while self.tokenizer.current_token in ["constructor","method","function"]:
            self._compileSubroutineDec() #compile subroutines

        
        #process the '}' of the class
        #self._expect_token(expected_token=["}"])
        #self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()  #advance from '}'


        #reduce indent level when closing the class node
        #self.indent_level-=1

        #write closing tag
        #self._write("</class>")


    def _compileClassVarDec(self):
        """
        compile the class variable declarations

        Grammar : classVarDec : ('static'|'field') type varName (',' varName)* ';'
        
        """

        #get kind
        kind = self.tokenizer.current_token #either static|field
        self.tokenizer.advance()

        #get type
        type_ = self.tokenizer.current_token
        self.tokenizer.advance()


        #get name
        name = self.tokenizer.current_token
        self.tokenizer.advance()

        #append symbol table
        self.symbol_table._define(
            name=name,
            type=type_,
            kind=kind
        )


        #next token - there might be 0 or more occurences
        while self.tokenizer.current_token == ",":

            #advance from the comma
            self.tokenizer.advance()

            #get name
            name = self.tokenizer.current_token
            self.tokenizer.advance()

            #append symbol table
            self.symbol_table._define(
                name=name,
                type=type_,
                kind=kind
            )

            #advance to next variable if any
            self.tokenizer.advance()



        #process the terminating ";"
        
        self.tokenizer.advance()



    def _compileSubroutineDec(self):

        """
        compiles the subroutine declarations

        Grammar: subroutineDec : ("constructor"|"method"|"function") ("void"|"type") subroutineName '(' parameterList ')' subRoutineBody

        
        """

        #handle keyword function, method, constructor
        subroutine_type = self.tokenizer.current_token
        self.tokenizer.advance() #advance from the keyword

        #process return type or void
        self.tokenizer.advance()

        #process full subroutinename(identifier)
        subroutine_name = self.tokenizer.current_token
        full_name = f"{self.class_name}.{subroutine_name}"
        self.tokenizer.advance()


        #process '('
        self.tokenizer.advance()


        #reset symbol table
        self.symbol_table._startSubroutine()
        self._label_num = 0  # Reset label counter for each subroutine


        #remember methods you have to handle this
        if subroutine_type == "method":
            self.symbol_table._define(
                name="this",
                type=self.class_name,
                kind="argument"
            )

        

        #parameter list ? (optional)
        self._compileParameterList()


        # handle ')'
        self.tokenizer.advance()


        #process subroutine body
        self._compileSubroutineBody(full_name, subroutine_type)




    def _compileSubroutineBody(self, full_function_name:str, subroutine_type):
        """
        compiles the subroutine body

        Grammar : subroutineBody: '{' varDec* statements '}'

        """

        #handle '{'
        self.tokenizer.advance()

        #handle varDec*
        while self.tokenizer.current_token == "var":
            self._compilevarDec()


        #local variables number 
        num_locals = self.symbol_table._varCount(kind="local")

        #write VM function decl command
        self.vm_writer.writeFunction(name=full_function_name, nLocals=num_locals)


        #handle constructors
        if subroutine_type == "constructor":

            #get fields for object size - OS memory.alloc
            num_fields = self.symbol_table._varCount(kind="field")
            self.vm_writer.writePush(memory_segment="constant", index=num_fields)

            #allocate memory
            self.vm_writer.writeCall(name="Memory.alloc",nArgs=1)

            self.vm_writer.writePop(memory_segment="pointer", index=0) #align THIS to the base address


        elif subroutine_type == "method":
            self.vm_writer.writePush(memory_segment="argument", index=0)
            self.vm_writer.writePop(memory_segment="pointer", index=0)



        #process statements
        self._compileStatements()


        #process '}'  
        self.tokenizer.advance()




    def _compileStatements(self):
        """
        compiles Statements
        Grammar: statements: statement*

        where statement can be letStatement|ifStatement|whileStatement| returnStatement
        
        """


        #handle statements
        while self.tokenizer.current_token in ["let","if","while","do","return"]:

            if self.tokenizer.current_token == "let":
                self._compileLet()

            elif self.tokenizer.current_token == "if":
                self._compileIf()

            elif self.tokenizer.current_token == "while":
                self._compileWhile()

            elif self.tokenizer.current_token == "do":
                self._compileDo()

            elif self.tokenizer.current_token == "return":
                self._compileReturn()



    def _compileParameterList(self):

        """
        Compiles a (possibly empty) parameter list
        Grammar : parameterList: ((type varName)(',' varName)*)?

        
        """

        self._write("<parameterList>")
        self.indent_level+=1


        #check if its empty
        if self.tokenizer.current_token != ")":

            #process first param
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #varName
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()


            #additional arguments if ',' is present
            while self.tokenizer.current_token == ',':
                #write the comma
                self._write_token(self.tokenizer.current_token)
                self.tokenizer.advance()

                #write type of the var
                self._write_token(self.tokenizer.current_token)
                self.tokenizer.advance()

                #handle varName
                self._write_token(self.tokenizer.current_token)
                self.tokenizer.advance()


        #indent
        self.indent_level-=1

        #closing tag
        self._write("</parameterList>")
        

    def _compilevarDec(self):

        """
        compiles variable declarations

        Grammar : varDec: 'var' type varName (',' varName)* ';'
        
        """

        #process var
        #self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance() #proceed from var

        #get type
        type_ = self.tokenizer.current_token
        self.tokenizer.advance()


        #get varName
        name = self.tokenizer.current_token
        self.tokenizer.advance() # move next 


        #update symbol table
        self.symbol_table._define(
            name=name,
            type=type_,
            kind="local"
        )


        #process more varName
        while self.tokenizer.current_token == ",":
            #escape the comma
            self.tokenizer.advance()

            name = self.tokenizer.current_token

            #update symbol table
            self.symbol_table._define(
                name=name,
                type=type_,
                kind="local"
            )

            self.tokenizer.advance()

        #terminating ';'
      
        self.tokenizer.advance()


        


    def _compileLet(self):
        """
        Compiles a let statement
        Grammar: letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
        
        """
       
        #process let keyword
        self.tokenizer.advance()

        #get variable name
        var_name = self.tokenizer.current_token
        memory_segment = self._get_vm_segment(self.symbol_table._kindof(name=var_name))
        index = self.symbol_table._indexof(name=var_name)
        self.tokenizer.advance()

        is_array = False

        #move either to '[' if an array or '='
        if self.tokenizer.current_token == "[":

            is_array = True
            self.tokenizer.advance()


            #compile the expression inside thearray
            self._compileExpression() #push i on the stack

            #push array base address
            self.vm_writer.writePush(memory_segment, index)
            self.vm_writer.writeArithmetic("add") #to get the offset arr+i
            
            #process ']'
            self.tokenizer.advance() #advance from the ']'


        #else process '='
        self.tokenizer.advance()


        #compile expression after '='
        self._compileExpression()  #pushes the second part onto thestack


        #process terminating ';'
    
        self.tokenizer.advance()


        if is_array:

            """
            remember the algorithm that solves the crash problem
            arr[exp1] = exp2

            push arr
            push exp1
            add
            push exp2
            pop temp 0
            pop pointer 1
            push temp 0
            pop that 0
            
            """

            #pop to temp
            self.vm_writer.writePop("temp", 0) #store the value of exp2 to temp

            #pop pointer 1
            self.vm_writer.writePop("pointer", 1)

            #push temp 0
            self.vm_writer.writePush("temp", 0)

            #pop that 0
            self.vm_writer.writePop("that", 0)

        else:

            #pop to segment of the var
            self.vm_writer.writePop(memory_segment, index)



    def _compileIf(self):

        """
        compiles if Statement
        Grammar: ifStatement: 'if' '('expression')' '{' statements '}' ('else' '{'statements '}')?

        """
       
        #generate unique labels
        label_true = self._generate_label("IF_TRUE")
        label_false = self._generate_label("IF_FALSE")
        label_end = self._generate_label("IF_END")
     
        #process if
        self.tokenizer.advance()

        #process '('
        self.tokenizer.advance()

        #process expression
        self._compileExpression() #pushes valueto the stack

        #process ')'
        self.tokenizer.advance()


        #negate value
        self.vm_writer.writeArithmetic("not")
        self.vm_writer.writeIf(label_false)



        #process '{'
        self.tokenizer.advance()

        #statements
        self._compileStatements() #pushes onto the stack

        #process '}'
        self.tokenizer.advance()

        self.vm_writer.writeGoto(label_end)
        self.vm_writer.writeLabel(label_false)

        #optional else clause
        if self.tokenizer.current_token == "else":
            #skip else
            self.tokenizer.advance()

            #handle '{'
            self.tokenizer.advance()

            #statements
            self._compileStatements()

            #'}'
            self.tokenizer.advance()


        self.vm_writer.writeLabel(label_end)
  

    def _compileWhile(self):
        """
        Compiles a while statement.
        Grammar: whileStatement: 'while' '(' expression ')' '{' statements '}'
        """
        # Generate sequential labels instead of using object IDs
        while_exp_label = f"WHILE_EXP{self._label_num}"
        while_end_label = f"WHILE_END{self._label_num}"
        self._label_num += 1  # Increment for next label
        
        # Write the WHILE_EXP label before evaluating the condition
        self.vm_writer.writeLabel(while_exp_label)
        
        # Process the 'while' keyword
        self.tokenizer.advance()  # Advance to the '(' symbol
        
        # Process the '(' symbol
        self.tokenizer.advance()  # Advance to the expression
        
        # Compile the expression inside the parentheses
        self._compileExpression()
        
        # Process the ')' symbol
        self.tokenizer.advance()  # Advance to the '{' symbol
        
        # Negate the condition and if true, exit the loop
        self.vm_writer.writeArithmetic("not")
        self.vm_writer.writeIf(while_end_label)
        
        # Process the '{' symbol that starts the while loop body
        self.tokenizer.advance()  # Advance to the statements inside the while loop
        
        # Compile the statements inside the while loop
        self._compileStatements()
        
        # Process the closing '}' symbol
        self.tokenizer.advance()  # Move past the '}'
        
        # Go back to evaluate the condition again
        self.vm_writer.writeGoto(while_exp_label)
        
        # End loop label
        self.vm_writer.writeLabel(while_end_label)

    def _compileExpression(self):
        """
        compiles expression

        Grammar: expression: term (op term)*
        """

      
        #handle first term
        self._compileTerm()

        #define operators
        operators = ["+","-","|","&","<",">","/","*","="]

        while self.tokenizer.current_token in operators:

            #write the op
            op = self.tokenizer.current_token
            self.tokenizer.advance()

            #process next term
            self._compileTerm()

            if op == "+":
                self.vm_writer.writeArithmetic("add")

            elif op == "-":
                self.vm_writer.writeArithmetic("sub")

            elif op == "*":
                self.vm_writer.writeCall("Math.multiply", 2)

            elif op == "/":
                self.vm_writer.writeCall("Math.divide", 2)

            elif op == "=":
                self.vm_writer.writeArithmetic("eq")

            elif op == "&":
                self.vm_writer.writeArithmetic("and")

            elif op == "|":
                self.vm_writer.writeArithmetic("or")

            elif op == "<":
                self.vm_writer.writeArithmetic("lt")

            elif op == ">":
                self.vm_writer.writeArithmetic("gt")

            else:
                pass


    def _compileTerm(self):
        """
        compiles Term
        Grammar: term:integerConstant|stringConstant|keywordConstant|varName|varName'['expression ']'|subroutineCall|'('expression')' | unaryOp term

        """
        token = self.tokenizer.current_token

        # Debugging: Print the variable being accessed
        print(f"DEBUG: Accessing variable `{token}` in scope `{self.symbol_table._current_scope}`")


        #1. integer constant eg 1,2,3...
        #case 1
        if token.isdigit():
            self.vm_writer.writePush("constant", int(token))
            self.tokenizer.advance()

        #case 2. string constant
        elif token.startswith('"') :
            string_content = self.tokenizer.stringVal()
            length = len(string_content)
            self.vm_writer.writePush("constant", length)
            self.vm_writer.writeCall("String.new", 1)


            for char in string_content:
                self.vm_writer.writePush("constant", ord(char))
                self.vm_writer.writeCall("String.appendChar", 2)


            
            self.tokenizer.advance()

        #case 3. keyword constant - null, true, false, this
        elif token in ["true", "false", "null","this"]:
            if token == "true":
                self.vm_writer.writePush("constant", 1)
                

            elif token == "false":
                self.vm_writer.writePush("constant", 0)

            elif token == "null":
                self.vm_writer.writePush("constant",0)

            elif token == "this":
                self.vm_writer.writePush("pointer",0)

            self.tokenizer.advance()

        #case 4.paranthesized expressions
        elif token == "(":
            #write the '('
            self.tokenizer.advance()

            #handle expression
            self._compileExpression()

            #handle ')'
            self.tokenizer.advance()


        #case 5. unary op
        elif token in ["-", "~"]:
            self.tokenizer.advance()

            self._compileTerm()

            self.vm_writer.writeArithmetic("neg" if token == "-" else "not")


        #case 6. identifier based term (varName, array, or subroutine call)
        else:
            var_name = token
           
            #process first term
            self.tokenizer.advance()

            #check if array- case 6a
            if self.tokenizer.current_token == '[':
                #write the bracket
                self.tokenizer.advance()

                self._compileExpression() #push i
                #process ']'
                self.tokenizer.advance()

                segment = self._get_vm_segment(self.symbol_table._kindof(var_name))
                index = self.symbol_table._indexof(var_name)

                self.vm_writer.writePush(segment, index) #arr+i
                self.vm_writer.writeArithmetic("add")


                #set that
                self.vm_writer.writePop("pointer",1)
                self.vm_writer.writePush("that",0) #load arr[index]


            #case 6b
            elif self.tokenizer.current_token in ['(', '.']:

                full_fxn_name = var_name
                n_args = 0

                if self.tokenizer.current_token == '.':
                    #write the dot
                    self.tokenizer.advance()

                    method_name = self.tokenizer.current_token
                    self.tokenizer.advance()

                    #check if var name in built in classes
                    if var_name in self.built_in_classes:

                        full_fxn_name = f"{var_name}.{method_name}"

                    else:

                        #check if var_name is a valid variable(field/local)
                        try:
                            if var_name in self.built_in_classes:
                                # It's a built-in class, no need to look it up in the symbol table
                                pass
                            elif self.symbol_table._kindof(var_name) in ["field","local"]:
                                segment = self._get_vm_segment(self.symbol_table._kindof(var_name))
                                index = self.symbol_table._indexof(var_name)
                                self.vm_writer.writePush(segment,index)
                                n_args+=1
                                var_name = self.symbol_table._typeof(var_name)
                                full_fxn_name = f"{var_name}.{method_name}"

                            else:
                                full_fxn_name = f"{var_name}.{method_name}"

                        except VariableNotFoundError:
                            full_fxn_name = f"{var_name}.{method_name}"

                    #check if its calling instance
                    try:
                        if var_name in self.built_in_classes:
                            # It's a built-in class, no need to look it up in the symbol table
                            pass
                        elif self.symbol_table._kindof(var_name) in ["field","local"]:
                            segment = self._get_vm_segment(self.symbol_table._kindof(var_name))
                            index = self.symbol_table._indexof(var_name)
                            self.vm_writer.writePush(segment,index) #push this
                            var_name = self.symbol_table._typeof(var_name)
                            n_args+=1 #first argument this
                    except VariableNotFoundError:
                        # If it's not in the symbol table, assume it's a class name
                        pass

                    full_fxn_name = f"{var_name}.{method_name}"


                #process '('
                self.tokenizer.advance()

                #compile expressionlist
                n_args += self._compileExpressionList()


                #process ')'
                
                self.tokenizer.advance()


                #gen vm call
                self.vm_writer.writeCall(full_fxn_name, n_args)

            #case 6c
            else:
                segment = self._get_vm_segment(self.symbol_table._kindof(var_name))
                index = self.symbol_table._indexof(var_name)

                self.vm_writer.writePush(segment,index)





    def _compileDo(self):
        # Process 'do' keyword
        self.tokenizer.advance()

        # Process subroutine call
        identifier = self.tokenizer.current_token
        self.tokenizer.advance()

        n_args = 0
        is_method = False

        if self.tokenizer.current_token == '.':
            self.tokenizer.advance()  # Consume '.'
            method_name = self.tokenizer.current_token
            self.tokenizer.advance()

            # Check if identifier is a built-in class
            if identifier in self.built_in_classes:
                # Static call (e.g., Output.printString)
                full_fxn_name = f"{identifier}.{method_name}"
            else:
                # Check if identifier is a variable (field/local)
                try:
                    kind = self.symbol_table._kindof(identifier)
                    if kind in ["field", "local"]:
                        segment = self._get_vm_segment(kind)
                        index = self.symbol_table._indexof(identifier)
                        self.vm_writer.writePush(segment, index)
                        n_args += 1
                        class_name = self.symbol_table._typeof(identifier)
                        full_fxn_name = f"{class_name}.{method_name}"
                    else:
                        # Static call (e.g., Main.helper)
                        full_fxn_name = f"{identifier}.{method_name}"
                except VariableNotFoundError:
                    # Assume it's a class name (e.g., Main.doSomething)
                    full_fxn_name = f"{identifier}.{method_name}"
        else:
            # Method of THIS class (e.g., do foo())
            full_fxn_name = f"{self.class_name}.{identifier}"
            self.vm_writer.writePush("pointer", 0)
            is_method = True
            n_args += 1

        # Process '(' and expression list
        self.tokenizer.advance()  # Consume '('
        n_args += self._compileExpressionList()
        self.tokenizer.advance()  # Consume ')'

        # Generate VM call
        self.vm_writer.writeCall(full_fxn_name, n_args)

        # Discard return value
        self.vm_writer.writePop("temp", 0)

        # Process ';'
        self.tokenizer.advance()
        

    def _compileReturn(self):
        """
        Compiles return statement
        Grammar : returnStatement 'return' expression? ';'

        """
   
        #process 'return'
        self.tokenizer.advance()


        #process expression if any
        if self.tokenizer.current_token == ";":
            #void
            self.vm_writer.writePush("constant", 0)
            self.vm_writer.writeReturn()
            self.tokenizer.advance()
            return
        

        #compile exp
        self._compileExpression()
        self.vm_writer.writeReturn()
            


        #process ';'
        self.tokenizer.advance()


    def _compileExpressionList(self):
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        Grammar: expressionList: (expression (',' expression)*)?
        """

        count = 0
        # If the next token is not ')', then there is at least one expression.
        if self.tokenizer.current_token != ')':

            count+=1
            # Process the first expression.
            self._compileExpression()
            
            # Process any additional expressions separated by commas.
            while self.tokenizer.current_token == ',':
                count+=1
                self._write_token(self.tokenizer.current_token)  # Write the comma.
                self.tokenizer.advance()
                self._compileExpression()

        return count

    def _close(self):
        "close output file"
        self.output.close()




input_file = r"C:\Users\LENOVO\Documents\nand_2_tetris_2\nand2tetris\projects\10\ArrayTest\Main.jack"
   

engine = CompilationEngine(input_file)
engine._compileClass()



    

