import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import numpy as np                  # Used for calculating distances
import readAndWriteJson as rwJson   # Used to read data from Json file


def readData(filename: str) -> dict:
    data=rwJson.readJsonFileToDictionary(filename)
    return data

def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Define the model
    model = pyomo.ConcreteModel()
    # Copy data to the model
    model.kommune_labels = data['municipalities']
    model.inhab_labels = data['inhab2022']
    model.ekstra = data['ext_price']
    model.etaberling = data['basis_price']
    model.travel = data['travel_times']
    model.basis_capacity=data["basis_capacity"]
    model.kommune = range(0, len(model.kommune_labels))
    model.inhab = range(0, len(model.travel[0]))
    model.p = data["p"]
    # Define x and y variables for the model
    model.x = pyomo.Var(model.kommune, model.inhab, within= pyomo.Binary)
    model.y = pyomo.Var(model.kommune, within= pyomo.Binary)
    model.z=pyomo.Var(model.kommune,within=pyomo.NonNegativeIntegers)
    # Add the objective function to the model
    model.obj = pyomo.Objective(expr=sum(model.travel[i][j]*model.x[i,j] for i in model.kommune for j in model.kommune) + sum(model.etaberling[i]*model.y[i] for i in model.kommune), sense=pyomo.minimize)
    # Add the "sum to one"-constraints
    model.SumToOne = pyomo. ConstraintList()
    for j in model.inhab:
        model.SumToOne.add(expr=sum(model.x[i,j] for i in model.kommune) == 1)
    # Add the "if x[i,j]==1 then y[i]=1" constraints
    model.service = pyomo.ConstraintList()
    for i in model.kommune:
        for j in model.inhab:
             model.service.add(expr=model.x[i, j] <= model.y[i])
    # antal sygehuse
    model.sygehus = pyomo.Constraint(expr=sum(model.y[i] for i in model.kommune) == model.p)

    # Add extra efterspørgsel til sygehusets basis efterpøsrgsel
    model.extracap=pyomo.ConstraintList()
    for i in model.kommune:
        model.extracap.add(expr=model.z[i]<=model.kommune[i]*model.y[i])

    # Add the capacity constraints
    model.capacities = pyomo.ConstraintList()
    for i in model.kommune:
        model.capacities.add(expr=sum(model.inhab_labels[j] * model.x[i,j] for j in model.inhab) <= model.basis_capacity[i] * model.y[i]+1000*model.z[i]) #+1000*z_1
    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Define a solver
    solver = pyomo.SolverFactory('cplex')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    #print optimal objektfunktions værdi
    print('optimal objektfunktions værdi er', pyomo.value(model.obj))
    # Print the open facilities
    for i in model.kommune:
        if pyomo.value(model.y[i]) == 1:
            print(model.kommune_labels[i], 'is open and the following customers are serviced:')
            for j in model.inhab:
                if pyomo.value(model.x[i,j]) == 1:
                    print(model.inhab_labels[j],end=',')
            print('\n')


def main(instance_file_name):
    data = readData(instance_file_name)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)

if __name__ == '__main__':
    instance_file_name = 'dataFileSmall'
    main(instance_file_name)
