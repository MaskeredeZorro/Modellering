import pyomo.environ as pyomo       # Used for modelling the IP
import matplotlib.pyplot as plt     # Used to plot the instance
import numpy as np                  # Used for calculating distances
import readAndWriteJson as rwJson   # Used to read data from Json file


#----------------------------------------------#
#MinMax Lokationsbaseret Clustering
#Her ønsker vi at minimere den maksimale afstand fra et dataobjekt til en (dens) repræsentant

def makeLpNormDistanceMatrix(data: dict, p: int) -> list:
    points = np.column_stack((data['Murder'], data['Assault'],data["UrbanPop"],data["Rape"]))
    nrPoints = len(data['State'])
    dist = []
    for i in range(0, nrPoints):
        dist.append([])
        for j in range(0, nrPoints):
            dist[i].append(np.linalg.norm(points[i] - points[j], p))
    return dist


def readData(clusterData: str) -> dict():
    data = rwJson.readJsonFileToDictionary(clusterData)
    data['nrPoints'] = len(data['State'])
    # data['dist'] = makeEuclideanDistanceMatrix(data)
     data['dist'] = makeLpNormDistanceMatrix(data,2)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Create model
    model = pyomo.ConcreteModel()
    # Copy data to model object
    model.nrPoints = data['nrPoints']
    model.points = range(0, data['nrPoints'])
    model.xCoordinates = data['Murder']
    model.yCoordinates = data['Assault']
    model.zCoordinates = data['UrbanPop']
    model.wCoordinates = data['Rape']
    model.dist = data['dist']
    model.k=data["k"]
    # Define variables
    model.y=pyomo.Var(model.points, within=pyomo.Binary)
    model.x=pyomo.Var(model.points, model.points, within=pyomo.Binary)
    model.rhoMax = pyomo.Var(within=pyomo.NonNegativeReals)

    # Find den maksimale længde mellem dataobjektet og dets repræsentant
    model.maxdist = pyomo.ConstraintList()
    for j in model.points:
        model.maxdist.add(expr=sum(model.dist[i][j] * model.x[i, j] for i in model.points) <= model.rhoMax)

    model.ekstracon2=pyomo.ConstraintList()
    for i in model.points:
            model.ekstracon2.add(expr=model.x[i,i]==model.y[i])

    #Add objective funktion
    model.obj=pyomo.Objective(expr=model.rhoMax,sense=pyomo.minimize)

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
    # Add cardinality constraint on number of groups (begrænser antallet af clustre)
    model.cardinality=pyomo.Constraint(expr=sum(model.y[i] for i in model.points)==model.k) #tilføjer en enkelt begrænsning
    return model

def solveModel(model: pyomo.ConcreteModel()):
    # Set the solver
    solver = pyomo.SolverFactory('gurobi')
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
    theDataFile = "USarrests.json"
    main(theDataFile)