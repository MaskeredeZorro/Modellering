import importlib

import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import numpy as np                  # Used for calculating distances
import readAndWriteJson as rwJson   # Used to read data from Json file

#-----------------------------------------------#
#Location allocation med single sourcing.
#Vi har her at gøre med CFLP: Constrainted facility location problem.
#   Det er constrainted/begrænset da vi jo netop har en begrænsning på, hvor mange indbyggere et givent sygehus kan imødekomme.

#Vi ønsker at minimere de totale faste omkotninger + extra omkostninger til udvidelse af et sygehus' kapacitet (udbud)
#Vi skal imødekomme to efterspørgsler afhængigt af hvilket år vi befinder os i. 2022 vs 2030.

#Når vi har med singlesourcing at gøre, skal vi blot ændre vores model.x variabel til at være Binary.
#   Så kan den kun antage 0 eller 1 og dermed enten allokere en kommune 0% eller 100% til et sygehus.
#-----------------------------------------------#



def readData(filename: str) -> dict:
    data=rwJson.readJsonFileToDictionary(filename)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Define the model
    model = pyomo.ConcreteModel()
    # Copy data to the model
    model.kommune_labels = data['municipalities']
    model.inhab_labels = data['inhab2022']
    model.inhab_labels30 = data['inhab2030']
    model.extra = data['ext_price']
    model.etablering = data['basis_price']
    model.travel = data['travel_times']
    model.basis_capacity=data["basis_capacity"]
    model.kommune = range(0, len(model.kommune_labels))
    model.p = data["p"]

    # Define x and y variables for the model
    model.x = pyomo.Var(model.kommune, model.kommune, within= pyomo.Binary)
    model.y = pyomo.Var(model.kommune, within= pyomo.Binary)
    model.z=pyomo.Var(model.kommune,within=pyomo.NonNegativeIntegers)

    # Add the objective function to the model
    model.obj = pyomo.Objective(expr=sum(model.etablering[i] * model.y[i]+model.extra[i] * model.z[i] for i in model.kommune))

    # Add the "sum to one"-constraints
    model.SumToOne = pyomo. ConstraintList()
    for j in model.kommune:
        model.SumToOne.add(expr=sum(model.x[i,j] for i in model.kommune) == 1)

    # Add the "if x[i,j]==1 then y[i]=1" constraints
    model.service = pyomo.ConstraintList()
    for i in model.kommune:
        for j in model.kommune:
             model.service.add(expr=model.x[i, j] <= model.y[i])

    # antal sygehuse
    model.sygehus = pyomo.Constraint(expr=sum(model.y[i] for i in model.kommune) == model.p)

    # Add extra efterspørgsel til sygehusets basis efterspørgsel
    model.extracap=pyomo.ConstraintList()
    for i in model.kommune:
        model.extracap.add(expr=model.z[i]<=50*model.y[i])

    #Capacity constraint: Alle kommuners efterspørgsel/indbyggertal i 2022 skal mødes
    model.capacities = pyomo.ConstraintList()
    for i in model.kommune:
        model.capacities.add(expr=sum(model.inhab_labels[j] * model.x[i,j] for j in model.kommune) <= model.basis_capacity[i] * model.y[i]+1000*model.z[i]) #+1000*model.z_1

    #Capacity constraint: Alle kommuners efterspørgsel/indbyggertal i 2030 skal mødes
    model.capacities2 = pyomo.ConstraintList()
    for i in model.kommune:
        model.capacities2.add(expr=sum(model.inhab_labels30[j] * model.x[i,j] for j in model.kommune) <= model.basis_capacity[i] * model.y[i]+1000*model.z[i]) #+1000*model.z_1


    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Define a solver
    solver = pyomo.SolverFactory('cplex')
    GAP_VALUE = 0.025
    solver.options['mipgap'] = GAP_VALUE
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    #print optimal objektfunktions værdi
    print('optimal objektfunktions værdi er', pyomo.value(model.obj))
    # Print the open facilities
    for i in model.kommune:
        if pyomo.value(model.y[i]) == 1:
            print(model.kommune_labels[i], 'is open and the following customers are serviced:')
            for j in model.kommune:
                if pyomo.value(model.x[i,j]) == 1:
                    print(model.kommune_labels[j],end=',')
            print('\n')


def main(instance_file_name):
    data = readData(instance_file_name)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)

if __name__ == '__main__':
    instance_file_name = 'Stortdata'
    main(instance_file_name)
