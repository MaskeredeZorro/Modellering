import importlib

import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import numpy as np                  # Used for calculating distances
import readAndWriteJson as rwJson   # Used to read data from Json file

def readData(filename: str) -> dict:
    data = rwJson.readJsonFileToDictionary(filename)
    return data

def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Definer modellen
    model = pyomo.ConcreteModel()
    # Tilføj data
    model.kommuner = data['municipalities']
    model.mia = 1000000000
    model.Defterspørgsel2022 = data['inhab2022']
    model.Defterspørgsel2030 = data['inhab2030']
    model.ekstraomkostninger = data['ext_price']
    model.fasteomkostninger = data['basis_price']
    model.distances = data['distances']
    model.travel_times = data['travel_times']
    model.basiskapacitet = data['basis_capacity']
    model.RangeAntalKommuner = range(0,len(model.kommuner))
    model.AntalSygehuse = data['p']
    model.maxbudget=data["maxbudget"]

    #Define variables
    model.x = pyomo.Var(model.RangeAntalKommuner, model.RangeAntalKommuner, within= pyomo.Binary)
    model.y = pyomo.Var(model.RangeAntalKommuner, within= pyomo.Binary)
    model.z=pyomo.Var(model.RangeAntalKommuner,within=pyomo.NonNegativeIntegers)

    #Tilføj objektfunktionen
    model.obj=pyomo.Objective(expr=sum(model.distances[i][j]*model.x[i,j] for i in model.RangeAntalKommuner for j in model.RangeAntalKommuner))

    #### ------------- Constraints -------------- ####
    # Alle kommuner skal knyttes til ét sygehus
    model.AlleKommuner = pyomo.ConstraintList()
    for j in model.RangeAntalKommuner:
        model.AlleKommuner.add(expr=sum(model.x[i, j] for i in model.RangeAntalKommuner) == 1)

    #Capacity constraint: Alle kommuners efterspørgsel/indbyggertal i 2022 skal mødes
    model.capacities = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        model.capacities.add(expr=sum(model.Defterspørgsel2022[j] * model.x[i,j] for j in model.RangeAntalKommuner) <= model.basiskapacitet[i] * model.y[i]+1000*model.z[i]) #+1000*model.z_1

    #Capacity constraint: Alle kommuners efterspørgsel/indbyggertal i 2030 skal mødes
    model.capacities2 = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        model.capacities2.add(expr=sum(model.Defterspørgsel2030[j] * model.x[i,j] for j in model.RangeAntalKommuner) <= model.basiskapacitet[i] * model.y[i]+1000*model.z[i]) #+1000*model.z_1

    # Sørg for maksimalt udvidelse på 50(000) patienter for hvert sygehus
    model.MaksimalUdvidelse = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        model.MaksimalUdvidelse.add(expr=model.z[i] <= 50 * model.y[i])
    # Sygehus skal åbnes hvis kommune er tildelt
    model.ÅbenSygehusHvisKommune = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        for j in model.RangeAntalKommuner:
            model.ÅbenSygehusHvisKommune.add(expr=model.x[i, j] <= model.y[i])

    # Budget begrænsning med udgangspunkt i opgave 1 + 5%
    model.BudgetGrænse = pyomo.Constraint(expr=(sum(model.fasteomkostninger[i]*model.y[i]*model.mia for i in model.RangeAntalKommuner)+sum(model.ekstraomkostninger[i]*model.z[i] for i in model.RangeAntalKommuner) <= model.maxbudget))

    # Åben specifikt x antal sygehuse
    model.ÅbenAntalSygehuse = pyomo.Constraint(expr=sum(model.y[i] for i in model.RangeAntalKommuner) == model.AntalSygehuse)
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
    for i in model.RangeAntalKommuner:
        if pyomo.value(model.y[i]) == 1:
            print(model.kommuner[i], 'is open and the following customers are serviced:')
            for j in model.RangeAntalKommuner:
                if pyomo.value(model.x[i,j]) == 1:
                    print(model.kommuner[j],end=',')
            print('\n')


def main(instance_file_name):
    data = readData(instance_file_name)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    instance_file_name = 'StorData'
    main(instance_file_name)
