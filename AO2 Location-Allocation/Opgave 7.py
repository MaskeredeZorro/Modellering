import importlib

import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import numpy as np                  # Used for calculating distances
import readAndWriteJson as rwJson   # Used to read data from Json file
from termcolor import colored


#-----------------------------------------------#
#Location allocation med single sourcing.
#Vi har her at gøre med UFLP: Unconstrainted facility location problem.
#   Det er unconstrainted/ubegrænset da vi jo netop INGEN begrænsning har på, hvor mange indbyggere et givent sygehus kan imødekomme.

#Derudover kan vi læse, at vi ønsker at "placere sygehusene således at FLEST mulige kan nå et sygehus INGEN FOR 45 minutter".
#   Vi har altså at gøre med et covering location problem, da vi jo netop ønsker at COVER så mange kommuner som muligt!!!!!

#For at kunne løse et covering location problem skal vi jo vide hvor langt hvem har til hvem. Det vil altså sige, at vi skal bruge en covering-matrix som vi kender den.
#   En covering matrix kan laves ved enten at lave en afstandsmatrix mellem to fikseret punkter i et koordinatsystem.
#       Denne afstand kan enten beregne euklidisk (pythagoras) eller på manhatten/texas metoden
#Vi har her allerede en covering matrix over hvor langt der er mellem hver kommune. Det er vores data["distances"] eller data["travel_times"]

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
    model.travel = data['distances']
    model.basis_capacity=data["basis_capacity"]
    model.kommune = range(0, len(model.kommune_labels))
    model.p = data["p"]
    model.maxbudget=data["maxbudget"]
    model.w=data["weight"]
    model.a = data['cover_matrix']
    model.b=data["b"]
    # Define x and y variables for the model
    model.y = pyomo.Var(model.kommune, within= pyomo.Binary)
    model.z=pyomo.Var(model.kommune,within=pyomo.Binary)
    # Add the objective function to the model
    model.obj = pyomo.Objective(expr=sum(model.z[j] for j in model.kommune), sense=pyomo.maximize)


###-----------------------Vi laver en max afstand fra kommune til sygehus (Coverin max location model-------------------------###

    # antal sygehuse
    model.sygehus = pyomo.Constraint(expr=sum(model.y[i] for i in model.kommune) == model.p)

    # Add covering constraints
    model.coveringCsts = pyomo.ConstraintList()
    for j in model.kommune:
        model.coveringCsts.add(
            expr=sum(model.a[i][j] * model.y[i] for i in model.kommune) >= model.b * model.z[j])

    # Add cardinality constraint
    model.cardinality = pyomo.Constraint(expr=sum(model.y[i] for i in model.kommune) <= model.p)


###--------------------------------------------------------------------------------------------###
    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Define a solver
    solver = pyomo.SolverFactory('cplex')
    GAP_VALUE = 0.025
    solver.options['mipgap'] = GAP_VALUE
    # Solve the model
    solver.solve(model, tee=True)




def displaySolution(model: pyomo.ConcreteModel()):
    # Print optimal objective function value
    print('Optimal objective function value is', pyomo.value(model.obj))
    print('The following facilities are open:')
    for i in model.kommune:
        if pyomo.value(model.y[i]) == 1:
            print(model.kommune_labels[i], end=',')
    print('\nCustomers are covered as follows:')
    for j in model.kommune:
        if pyomo.value(model.z[j]) == 1:
            print(colored(model.kommune_labels[j], 'green'),end='->\t')
        else:
            print(colored(model.kommune_labels[j], 'red'), end='->\t')
        for i in model.kommune:
            if model.a[i][j] == 1 and pyomo.value(model.y[i])==1:
                print(model.kommune_labels[i], end=',')
        print('')
    # Print the open facilities

def main(instance_file_name):
    data = readData(instance_file_name)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)

if __name__ == '__main__':
    instance_file_name = 'Stortdata'
    main(instance_file_name)
