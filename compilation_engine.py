import os
from tokenizer import Tokenizer

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
        self.tokenizer.index = 0
        self.indent_level = 0
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
        


    def _compileClass(self):
        #compiles a complete class - its the first method to be called by the engine
        #rule class: 'class' className '{' classVarDec* subroutineDec* '}'

        #write all tokens
        print(self.tokenizer.tokens)

        self._write("<class>")

        #increase identation level for the class
        self.indent_level += 1


        #---------------------------------
        #process the 'class' keyword
        #-------------------------------
        
        self._expect_token(expected_token=["class"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #handle class Name
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

       


        #process the opening bracket '{'
        self._expect_token(['{'])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance() # move to the first classVarDec or subroutines if it lacks the classVar


        #process classVar
        while self.tokenizer.current_token in ["static", "field"]:
            self._compileClassVarDec() #compile the variables


        # process subroutines
        while self.tokenizer.current_token in ["constructor","method","function"]:
            print(f"Current token is : {self.tokenizer.current_token}")
            self._compileSubroutineDec() #compile subroutines

        
        #process the '}' of the class
        self._expect_token(expected_token=["}"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance() 


        #reduce indent level when closing the class node
        self.indent_level-=1

        #write closing tag
        self._write("</class>")


    

    def _compileClassVarDec(self):
        """
        compile the class variable declarations

        Grammar : classVarDec : ('static'|'field') type varName (',' varName)* ';'
        
        """

        #write the opening of the tag
        self._write("<classVarDec>")

        self.indent_level+=1


        #process keywords static|field

        self._write_token(self.tokenizer.current_token) #writes either static or field
        self.tokenizer.advance()

        #process types
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process varName
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #next token - there might be 0 or more occurences
        while self.tokenizer.current_token == ",":

            #write the comma
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #write varName
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()



        #process the terminating ";"
        self._expect_token([";"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #indent --
        self.indent_level-=1


        #write closing tag
        self._write("</classVarDec>")


    def _compileSubroutineDec(self):

        """
        compiles the subroutine declarations

        Grammar: subroutineDec : ("constructor"|"method"|"function") ("void"|"type") subroutineName '(' parameterList ')' subRoutineBody

        
        """
        
        #write tag
        self._write("<subroutineDec>")

        #indent
        self.indent_level +=1

        #handle keyword function, method, constructor
        self._expect_token(["function","method","constructor"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process return type or void
        self._expect_token(["void","int","boolean","char"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process subroutinename(identifier)

        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #process '('
        self._expect_token(["("])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #parameter list ? (optional)
        self._compileParameterList()


        # handle ')'
        self._expect_token(")")
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #process subroutine body

        self._compileSubroutineBody()


        #decrease indentation
        self.indent_level-=1


        #write closing tag
        self._write("</subroutineDec>")




    def _compileSubroutineBody(self):
        """
        compiles the subroutine body

        Grammar : subroutineBody: '{' varDec* statements '}'

        """

        #opening tag
        self._write("<subroutineBody>")

        #indent
        self.indent_level+=1

        #handle '{'
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #handle varDec*
        while self.tokenizer.current_token == "var":
            self._compilevarDec()


        #process statements
        self._compileStatements()


        #process '}'
        self._expect_token(["}"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #indent
        self.indent_level-=1

        #closing tag
        self._write("</subroutineBody>")



    def _compileStatements(self):
        """
        compiles Statements
        Grammar: statements: statement*

        where statement can be letStatement|ifStatement|whileStatement| returnStatement
        
        """

        self._write("<statements>")
        self.indent_level+=1

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


        #indent
        self.indent_level-=1
        
        #close tag
        self._write("</statements>")


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

        self._write("<varDec>")

        self.indent_level+=1


        #process var
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process type
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #process varName
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process more varName
        while self.tokenizer.current_token == ",":
            #write the comma
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #handle varName
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

        #terminating ';'
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #indent
        self.indent_level-=1

        #close tag
        self._write("</varDec>")


        


    def _compileLet(self):
        """
        Compiles a let statement
        Grammar: letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
        
        """
        self._write("<letStatement>")
        self.indent_level+=1

        #process let keyword
        self._expect_token(["let"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process  variable name
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #move either to '[' if an array or '='
        if self.tokenizer.current_token == "[":
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()


            #compile the expression inside thearray
            self._compileExpression()
            
            #process ']'
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()


        #else process '='
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #compile expression after '='
        self._compileExpression()


        #process terminating ';'
        self._expect_token([";"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #indnet
        self.indent_level-=1

        #close tag
        self._write("</letStatement>")

        

    def _compileIf(self):

        """
        compiles if Statement
        Grammar: ifStatement: 'if' '('expression')' '{' statements '}' ('else' '{'statements '}')?

        """
        #open tag
        self._write("<ifStatement>")
        self.indent_level+=1

        #process if
        self._expect_token(["if"])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process '('
        self._expect_token(["("])
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process expression
        self._compileExpression()

        #process ')'
        self._expect_token(")")
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #process '{'
        self._expect_token("{")
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #statements
        self._compileStatements()

        #process '}'
        self._expect_token("}")
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #optional else clause
        if self.tokenizer.current_token == "else":
            #write else
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #handle '{'
            self._expect_token(["{"])
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #statements
            self._compileStatements()

            #'}'
            self._expect_token(["}"])
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()


        #indentation
        self.indent_level-=1

        #close tag
        self._write("</ifStatement>")
        

    def _compileWhile(self):
        """
        Compiles a while statement.
        Grammar: whileStatement: 'while' '(' expression ')' '{' statements '}'
        """
        # Write the opening tag for the while statement.
        self._write("<whileStatement>")
        self.indent_level += 1

        # --------------------------------------------------
        # Process the 'while' keyword.
        # --------------------------------------------------
        self._expect_token(["while"])
        self._write_token(self.tokenizer.current_token)  # Should output 'while'
        self.tokenizer.advance()  # Advance to the '(' symbol

        # --------------------------------------------------
        # Process the '(' symbol.
        # --------------------------------------------------
        self._expect_token("(")
        self._write_token(self.tokenizer.current_token)  # Should output '('
        self.tokenizer.advance()  # Advance to the expression

        # --------------------------------------------------
        # Compile the expression inside the parentheses.
        # --------------------------------------------------
        self._compileExpression()

        # --------------------------------------------------
        # Process the ')' symbol.
        # --------------------------------------------------
        self._expect_token([")"])
        self._write_token(self.tokenizer.current_token)  # Should output ')'
        self.tokenizer.advance()  # Advance to the '{' symbol

        # --------------------------------------------------
        # Process the '{' symbol that starts the while loop body.
        # --------------------------------------------------
        self._expect_token("{")
        self._write_token(self.tokenizer.current_token)  # Should output '{'
        self.tokenizer.advance()  # Advance to the statements inside the while loop

        # --------------------------------------------------
        # Compile the statements inside the while loop.
        # --------------------------------------------------
        self._compileStatements()

        # --------------------------------------------------
        # Process the closing '}' symbol.
        # --------------------------------------------------
        self._expect_token(["}"])
        self._write_token(self.tokenizer.current_token)  # Should output '}'
        self.tokenizer.advance()  # Move past the '}'

        # Decrease the indentation and close the while statement XML tag.
        self.indent_level -= 1
        self._write("</whileStatement>")


    def _compileExpression(self):
        """
        compiles expression

        Grammar: expression: term (op term)*
        """

        self._write("<expression>")
        self.indent_level+=1


        #handle first term
        self._compileTerm()

        #define operators
        operators = ["+","-","|","&","<",">","/","*","="]

        while self.tokenizer.current_token in operators:

            #write the op
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #process next term
            self._compileTerm()


        self.indent_level-=1

        self._write("</expression>")


    def _compileTerm(self):
        """
        compiles Term
        Grammar: term:integerConstant|stringConstant|keywordConstant|varName|varName'['expression ']'|subroutineCall|'('expression')' | unaryOp term

        """
        self._write("<term>")
        self.indent_level+=1

        token = self.tokenizer.current_token

        #1. integer constant eg 1,2,3...
        if token.isdigit():
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

        #2. string constant
        elif token.startswith('"') :
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

        #3. keyword constant - null, true, false, this
        elif token in ["true", "false", "null","this"]:
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

        #4.paranthesized expressions
        elif token == "(":
            #write the '('
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #handle expression
            self._compileExpression()

            #handle ')'
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()


        #5. unary op
        elif token in ["-", "~"]:
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            self._compileTerm() #compile term following the op


        #6. identifier based term (varName, array, or subroutine call)
        else:

            #process first term
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #check if array
            if self.tokenizer.current_token == '[':
                #write the bracket
                self._write_token(self.tokenizer.current_token)
                self.tokenizer.advance()

                #process expression inside array
                self._compileExpression()

                #process ']'
                self._write_token(self.tokenizer.current_token)
                self.tokenizer.advance()

            
            elif self.tokenizer.current_token in ['(', '.']:

                if self.tokenizer.current_token == '.':
                    #write the dot
                    self._write_token(self.tokenizer.current_token)
                    self.tokenizer.advance()

                    #write subroutineName
                    self._write_token(self.tokenizer.current_token)
                    self.tokenizer.advance()

                #process '('
                self._write_token(self.tokenizer.current_token)
                self.tokenizer.advance()

                #compile expressionlist
                self._compileExpressionList()


                #process ')'
                self._write_token(self.tokenizer.current_token)
                self.tokenizer.advance()


        self.indent_level-=1

        #close tag
        self._write("</term>")



    def _compileDo(self):
        """
        Compiles a do statement
        Grammar : doStatement: 'do' subroutineCall

        """

        self._write("<doStatement>")
        self.indent_level+=1

        #process 'do' keyword
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #process subroutine call
        #subroutine may be in 2 forms:
        #1. subroutineName '(' expressionList ')'
        #2. (className|varName) '.' subroutineName '(' expressionlist ')'

        #process the first identifier - subroutineName or className/varName
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #check if next token is a .
        if self.tokenizer.current_token == ".":
            #write the .
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()

            #handle subroutineName
            self._write_token(self.tokenizer.current_token)
            self.tokenizer.advance()


        #process '('
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #expressionlist
        self._compileExpressionList()

        #handle ')'
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()

        #termination colon ';'
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #indent
        self.indent_level-=1

        #close tag
        self._write("</doStatement>")



        

    def _compileReturn(self):
        """
        Compiles return statement
        Grammar : returnStatement 'return' expression? ';'

        """
        self._write("<returnStatement>")
        self.indent_level+=1

        #process 'return'
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #process expression if any
        if self.tokenizer.current_token != ";":
            self._compileExpression()


        #process ';'
        self._write_token(self.tokenizer.current_token)
        self.tokenizer.advance()


        #indent
        self.indent_level-=1

        #close tag
        self._write("</returnStatement>")
        

    def _compileExpressionList(self):
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        Grammar: expressionList: (expression (',' expression)*)?
        """
        self._write("<expressionList>")
        self.indent_level += 1

        # If the next token is not ')', then there is at least one expression.
        if self.tokenizer.current_token != ')':
            # Process the first expression.
            self._compileExpression()
            
            # Process any additional expressions separated by commas.
            while self.tokenizer.current_token == ',':
                self._write_token(self.tokenizer.current_token)  # Write the comma.
                self.tokenizer.advance()
                self._compileExpression()

        self.indent_level -= 1
        self._write("</expressionList>")


    def _close(self):
        "close output file"
        self.output.close()



try:
    input_file = r"C:\Users\LENOVO\Documents\nand_2_tetris_2\nand2tetris\projects\10\ArrayTest\Main.jack"
    output_file = r"C:\Users\LENOVO\Documents\nand_2_tetris_2\nand2tetris\projects\10\ArrayTest\Main4.xml"

    engine = CompilationEngine(input_file)
    engine._compileClass()

except Exception as e:
    print(f"Error occured : {e}")

finally:
    engine._close()


    

