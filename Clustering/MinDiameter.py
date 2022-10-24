# Pyomo example for the course "Modellering inden for Prescriptive Analytics" at Aarhus University, Fall 2022
# Implementation of a p-center based clustering problem on n points numbered 0,1,...,n-1
# The IP solved is given by
# min   Dmax
# s.t.  Dmax >= D[l],   for all l=0,..,k-1
#       D[l] >= c[i][j]*( x[i][l] + x[j][l] -1 ),   for all i,j in 0..n-1, l=0..k
#       sum ( l in 0..k-1 ) x[i][l] == 1,           for all i=0..n-1
#       x[i][l] are all binary
# where c[i][j] is the distance between point i and point j
# The readData(...) function uses the readAndWriteJson file to read data from a Json file
# in the form of x coordinates and y coordinates
# Read data function also computes the distance matrix

import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import numpy as np                  # Used for calculating distances
import readAndWriteJson as rwJson   # Used to read data from Json file


#----------------------------------------------------#
#
#
#Minimering af diameteren - lokationsbaseret clustering
#
#
#Her ønsker vi at minimere diameteren i et cluster. Dette gøres altså for at minimere den længste afstand mellem hvert dataobjekt, i hver cluster.
#----------------------------------------------------#



def makeLpNormDistanceMatrix(data: dict, p: int) -> list:
    points = np.column_stack((data['x'], data['y']))
    nrPoints = len(data['x'])
    dist = []
    for i in range(0, nrPoints):
        dist.append([])
        for j in range(0, nrPoints):
            dist[i].append(np.linalg.norm(points[i] - points[j], p))
    return dist


def readData(clusterData: str) -> dict():
    data = rwJson.readJsonFileToDictionary(clusterData)
    data['nrPoints'] = len(data['x'])
    data['dist'] = makeLpNormDistanceMatrix(data, 2)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Create model
    model = pyomo.ConcreteModel()
    # Copy data to model object
    model.nrPoints = data['nrPoints']
    model.points = range(0, data['nrPoints'])
    model.xCoordinates = data['x']
    model.yCoordinates = data['y']
    model.dist = data['dist']
    model.k = data['k']
    model.groups = range(0, model.k)
    # Define variables
    model.x=pyomo.Var(model.points,model.groups, within=pyomo.Binary)
    model.D=pyomo.Var(model.groups,within=pyomo.NonNegativeReals)
    model.Dmax=pyomo.Var(within=pyomo.NonNegativeReals)
    # Add objective function
    model.obj=pyomo.Objective(expr=model.Dmax,sense=pyomo.minimize)
    # Add definition for Dmax
    model.DmaxDefinition=pyomo.ConstraintList()
    for l in model.groups:
        model.DmaxDefinition.add(expr=model.Dmax>=model.D[l])

    # Add defintion for the D-variables. Her laver vi 3 gange nested forloop.
    model.Ddefinition=pyomo.ConstraintList()
    for i in model.points:
        for j in model.points:
            for l in model.groups:
                model.Ddefinition.add(expr=model.D[l]>=model.dist[i][j]*(model.x[i,l]+model.x[j,l]-1))
            #læg mærke til at vi ved variabler skal skrive [i,l] men hvis en liste ligger i en liste så skal man tilgå det ved [i][j]

    # Make sure that all points a in a group
    model.OneGroup=pyomo.ConstraintList()
    for i in model.points:
        model.OneGroup.add(expr=sum(model.x[i,l] for l in model.groups)==1)





    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Set the solver
    solver = pyomo.SolverFactory('cplex')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    print('Optimal diameter is:',pyomo.value(model.obj))
    labels = [0] * model.nrPoints
    ptNumber = list(model.points)
    # Print the groups to promt and save coordinates for plotting
    for l in model.groups:
        print('Group',l,'consists of:')
        for i in model.points:
            if pyomo.value(model.x[i,l]) == 1:
                print(i,',',end='')
                labels[i] = l
        print('')
    # Plot with different colors
    plt.scatter(model.xCoordinates, model.yCoordinates, c=labels)
    for i, label in enumerate(ptNumber):
        plt.annotate(ptNumber[i], (model.xCoordinates[i], model.yCoordinates[i]))
    plt.show()


def main(clusterDataFile: str):
    data = readData(clusterDataFile)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    theDataFile = "clusteringData_34_point - Copy"
    main(theDataFile)
