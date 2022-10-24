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
    model.k = data["k"]
    model.groups = range(0, model.k)
    #Add variable
    model.y = pyomo.Var(model.points, within=pyomo.Binary)
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
    theDataFile = "USarrests.json"
    main(theDataFile)