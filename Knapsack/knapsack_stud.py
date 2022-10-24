# Pyomo example for the course "Modellering inden for Prescriptive Analytics" at Aarhus University, Fall 2022
# Implementation of a knapsack problem where data is read from a Json file
# The IP solved is given by
# max   sum ( i in 0..9 ) p[i]*x[i]
# s.t.  sum ( i in 0..9 ) c[i]*x[i] <= B
#       x[i] in {0,1} for all i=0,...,9
# where p[i] is the prize for packing item i, c[i] is the cost of item i, and B is budget available
# The readData(...) functions has an argument for a file name - remember to specify this in the main


import readAndWriteJson as rwJson
import pyomo.environ as pyomo


def readData(filename: str) -> dict:
    # Reading the data for the KP from a Json file
    data = rwJson.readJsonFileToDictionary(filename)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Create the model object
    model = pyomo.ConcreteModel()
    #Copy data to model - Her klargører vi vores parametre. Vi klargører dem for programmering
    model.p=data["p"]
    model.c=data["c"]
    model.B=data["B"]
    model.numOfItems=range(0,len(model.p))
    model.items=range(0,len(model.p))
    #Define variables for alle vores items i ovenstående range
    model.x=pyomo.Var(model.items,within=pyomo.Binary)
    #Add objective function. En objektfunktion er et udtryk og derfor expr=
    model.obj = pyomo.Objective(expr=sum(model.p[i]*model.x[i] for i in model.items),sense=pyomo.maximize)
    #Tilføj budget begrænsning:
    model.budget=pyomo.Constraint(expr=sum(model.c[i]*model.x[i] for i in model.items)<=model.B)
    return model

def solveModel(model: pyomo.ConcreteModel()):
    # Set the solver
    solver = pyomo.SolverFactory('cbc')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    # Print solution information to prompt - delete "pass" yourself
    print("The optimal objective function value is: ",pyomo.value(model.obj))
    print("The following items were chosen:")
    for i in model.items:
        if pyomo.value(model.x[i])==1:
            print("item",i,"is chosen")
def main():
    KP_dataFileName = "KP_100"
    data = readData(KP_dataFileName)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    main()
