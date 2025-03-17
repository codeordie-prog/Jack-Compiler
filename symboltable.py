
from pydantic import BaseModel, Field



class Kind(BaseModel):
    #pydantic validation model
    static:str = Field("static")
    field:str = Field("field")
    argument:str = Field("argument")
    local:str=Field("local")


class VariableNotFoundError(Exception):
    def __init__(self, variableName:str, scope:str, message:str):
        self.variable_name = variableName
        self.scope = scope
        self.message = message or f"Variable '{variableName}' not found"

        if scope:
            self.message += f" in scope '{scope}'"

        super().__init__(self.message)




class SymbolTable:

    #constructor
    def __init__(self):

        #constructs a new symbol table
        self._current_scope = "class" #start at class level

        self._symbol_table = {

            "class": [],

            "subroutine": []

                            }

    def _startSubroutine(self):
        #starts a new subroutine scope i.e resets the subroutine table
        self._symbol_table["subroutine"] = []

        #update scope
        self._current_scope = "subroutine"
        

    def _define(self, name:str, type:str, kind):
        #defines a new identifier of the given params
        scope = "class" if kind in ["static", "field"] else "subroutine"

        index = self._varCount(kind)


        self._symbol_table[scope].append(

            {
                "name":name,
                "type":type,
                "kind":kind,
                "index":index,
            }
        )

    def _varCount(self,kind)->int:
        #returns no. of variables of the given kind already defined inthe scope
        
        return sum(1 for var in self._symbol_table[self._current_scope] if var['kind']==kind)
    


    def _kindof(self, name:str)->str:
        #returns kind of the named identifier in the current scope
        scope = self._current_scope

        for variable in self._symbol_table[scope]:

            if variable["name"] == name:
                return variable["kind"]
                
        raise VariableNotFoundError(name, self._current_scope)    

    def _typeof(self, name:str)->str:
        #returns type of

        scope = self._current_scope

        for variable in self._symbol_table[scope]:

            if variable["name"] == name:

                return variable["type"]

        raise VariableNotFoundError(name, self._current_scope)

    def _indexof(self, name:str)->int:
        #return index assigned
        
        scope = self._current_scope

        for variable in self._symbol_table[scope]:

            if variable["name"]==name:

               return variable["index"]
            
        raise VariableNotFoundError(name, self._current_scope)
            

    
        