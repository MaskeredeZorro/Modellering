# Pyomo example for the course "Modellering inden for Prescriptive Analytics" at Aarhus University, Fall 2022
# Implementation of a p-median based clustering problem on n points numbered 0,1,...,n-1
# The IP solved is given by
# min   sum ( i in 0..n-1 ) sum( j in 0..n-1) d[i][j]*x[i][j]
# s.t.  sum ( i in 0..n-1 ) x[i][j] == 1,   for all j=0,..,n-1
#       x[i][j] <= y[i],                    for all i,j in 0,...,n-1
#       sum ( i in 0..n-1 ) y[i] <= k
#       x[i][j] and y[i] are all binary
# where d[i][j] is the distance between point i and point j
# The readData(...) function uses the readAndWriteJson file to read data from a Json file
# in the form of x coordinates and y coordinates
# Read data function also computes the distance matrix

import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import numpy as np                  # Used for calculating distances
import readAndWriteJson as rwJson   # Used to read data from Json file



#-------------------------------------------#
#
#
#Dette er vist den samme fil som ovenstående MinSum
#
#
#
#-------------------------------------------#





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
    # data['dist'] = makeEuclideanDistanceMatrix(data)
    data['dist'] = makeLpNormDistanceMatrix(data,2)
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
    # Define variables
    model.y=pyomo.Var(model.points, within=pyomo.Binary)
    model.x=pyomo.Var(model.points, model.points, within=pyomo.Binary)
    model.rhoMax = pyomo.Var(within=pyomo.NonNegativeReals)
    #Find den maksimale længde

    model.maxdist=pyomo.ConstraintList()
    for j in model.points:
        model.maxdist.add(expr=sum(model.dist[i][j]*model.x[i,j] for i in model.points) <= model.rhoMax)


    # Add objective function
    model.obj = pyomo.Objective(expr=model.rhoMax, sense=pyomo.minimize)
    #ovenstående svarer til at skrive "sum i tilhørende points" og så med en sum inde i sig som siger "sum j tilhørende points" hvor indmaden til dette er c_ij*x_ij


    # Add "all must be represented" constraints
    #for at lave for all j skal vi lave et "forloop" da vi ønsker at tilføje en begrænsning for alle vores j'er
    model.sumToOne=pyomo.ConstraintList()
    for j in model.points:
        model.sumToOne.add(expr=sum(model.x[i,j] for i in model.points)==1) #vi har tilføjet at summen for alle x_ij variablerne skal være lig med 1. Vi gør dette lige så mange gange som der er punkter. Dvs. j starter med at være 0 og så 1 og så 2, osv.

    # Add only represent if y[i]=1 (x[i][j]=1 => y[i]=1)
    model.indicators=pyomo.ConstraintList()
    for i in model.points: #vi sætter i for et model.points
            for j in model.points: #vi sætter nu j lig med alle punkterne for i=1... Dette fortsætter så først i=1 og så alle j punkterne. Dernæst i=2 og så alle j-punkterne igen. Osv osv indtil "loopet" er færdigt.
                model.indicators.add(expr=model.x[i,j]<=model.y[i])
    # Add cardinality constraint on number of groups
    model.cardinality=pyomo.Constraint(expr=sum(model.y[i] for i in model.points)==model.k) #tilføjer en enkelt begrænsning

    #tilføjer den anden sidste nye begrænsning.
    model.ekstracon1=pyomo.ConstraintList()
    for j in model.points:
        model.ekstracon1.add(expr=sum(model.dist[i][j]*model.x[i,j] for i in model.points)<=model.rhoMax)


    #add X_ii=y_i for all i=1 to n. Vi skal bruge et forloop. Dette er den sidste nye begrænsning
    model.ekstracon2=pyomo.ConstraintList()
    for i in model.points: #her tilføjer vi vores "for alle" begrænsning ved at lave et loop. Vi laver et loop fordi så kører den jo igennem for alle j'erne.
            model.ekstracon2.add(expr=model.x[i,i]==model.y[i])
    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Set the solver
    solver = pyomo.SolverFactory('cplex')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    print('Optimal sum of distances in clusters:', pyomo.value(model.obj))
    labels = [0] * model.nrPoints
    ptNumber = list(model.points)
    # Print the groups to promt and save coordinates for plotting
    for i in model.points:
        if pyomo.value(model.y[i]) == 1:
            print('Point', i, 'represents points:')
            for j in model.points:
                if pyomo.value(model.x[i, j]) == 1:
                    print(j, ",", end='')
                    labels[j] = i
            print('\n')
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
    theDataFile = "clusteringData_34_point"
    main(theDataFile)
