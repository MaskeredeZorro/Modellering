# In this document, a two stage stochastic optimization problem is formulated where in the first stage, the number of
# vehicles in a fleet (m) must be decided.
# The second stage is cencerned with routing the vehicles.
# It is assumed, that there is a fixed known leasing price for each vehicle, and that the demand at each customer
# is a stochastic variable. Hence, we need to take care of servicing customers in a way that does not violate the
# capacities of the vehicles.
# As input for the model, we have the folling:
# n : number of customers to serve - We will let N = {1,2,3,...,n} for ease of notation
# {0} : a depot from which the vehicles should leave and return to
# V : {0,1,2,3,...,n} set of all nodes
# c[i][j]: Cost of traveling directly from node i to node j
# Q : the capacity of the identical vehicles
# S : a set of potential demand scenarios
# d[s][j] : demand of node j in scenario s
# p[s] : probability of scenario s
# L : leasing price for a vehicle
# The variables used in the model are
# m : number of vehicles used
# x[i, j, s] : Binary variable equalling 1 iff a vehicle travels directly from node i to node j in scenario s
# f[i, j, s] : Continuous variable. If x[i, j, s] = 1 then f[i, j, s]=amount of goods collected on the tour when leaving
#               node i. Otherwise f[i, j, s] = 0
import readAndWriteJson as rwJson
import pyomo.environ as pyomo
import math


def makeDistanceMatrix(data: dict) -> list:
    numNodes = len(data['xCoordinates'])
    dist = []
    for i in range(numNodes):
        dist.append([])
        for j in range(numNodes):
            tmpDist = (data['xCoordinates'][i] - data['xCoordinates'][j]) ** 2 + (
                    data['yCoordinates'][i] - data['yCoordinates'][j]) ** 2
            dist[i].append(round(math.sqrt(tmpDist), 2))  # round to two decimals
    return dist


def readData(filename: str) -> dict:
    data = rwJson.readJsonFileToDictionary(filename)
    data['dist'] = makeDistanceMatrix(data)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Create model object
    model = pyomo.ConcreteModel()
    # Create ranges
    model.customers = range(1, data['n'] + 1)
    model.nodes = range(0, data['n'] + 1)
    model.scenarios = range(0, len(data['demands']))
    # Create variables
    model.x = pyomo.Var(model.nodes, model.nodes, model.scenarios, within=pyomo.Binary)
    model.y = pyomo.Var(model.customers, model.scenarios, within=pyomo.Binary)
    model.f = pyomo.Var(model.nodes, model.nodes, model.scenarios, within=pyomo.NonNegativeReals)
    model.m = pyomo.Var(within=pyomo.NonNegativeIntegers)
    # Create the objective function
    model.obj = pyomo.Objective(
        expr=data['L']* model.m + sum(
            data['Prob'][s]*data['dist'][i][j] * model.x[i, j, s] for i in model.nodes for j in model.nodes for s in model.scenarios)
            + sum(data['Prob'][s]*data['B']*(1-model.y[i, s]) for i in model.customers for s in model.scenarios)
    )
    #Remove the diagonal
    for s in model.scenarios:
        for i in model.nodes:
            model.x[i, i, s].fix(0)
    # Ensure the right number of vehicles in and out of the depot
    model.degreeDepot = pyomo.ConstraintList()
    for s in model.scenarios:
        model.degreeDepot.add(expr=sum(model.x[0,j,s] for j in model.customers)<=model.m)
        model.degreeDepot.add(expr=sum(model.x[i,0,s] for i in model.customers)<=sum(model.x[0,j,s] for j in model.customers))

    # Ensure that each customer is visited exactly once in each scenario
    model.inDegree = pyomo.ConstraintList()
    model.outDegree = pyomo.ConstraintList()

    # Ensure, that if x[i, j, s] = 0 then f[i, j, s]=0 and otherwise f[i, j, s]<=Q
    model.GUB = pyomo.ConstraintList()
    for i in model.customers:
        for j in model.customers:
            for s in model.scenarios:
                model.GUB.add(model.f[i,j,s]<=(data["Q"]*model.x[i,j,s]))
    # Ensure the right flow in each scenario
    model.flow = pyomo.ConstraintList()

    return model


def solveModel(model: pyomo.ConcreteModel()):
    solver = pyomo.SolverFactory('gurobi')
    solver.options['MIPGap'] = 0.05
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel(), data: dict):
    numVehicles = pyomo.value(model.m)
    print(f'We need to lease {numVehicles} vehicles')
    # Here goes the rest of the display function


def main(filename: str):
    data = readData(filename)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model, data)


if __name__ == '__main__':
    main('TS-SP-CVRP-Data.json')
