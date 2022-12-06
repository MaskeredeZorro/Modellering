def readData(clusterData: str) -> dict():
    data = rwJson.readJsonFileToDictionary(clusterData)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Create model
    model = pyomo.ConcreteModel()
    # Copy data to model object
    model.nrPoints = len(data['punkter'])
    model.points = range(0, len(data['punkter']))
    model.x=data["xCoordinates"]
    model.y=data["yCoordinates"]
    model.n=data["n"]
    model.Q = data['Q']
    model.L = data['L']
    model.B = data['B']
    model.Prob = data['Prob']
    model.demands=data["demands"]
    # Define variables
    model.y=pyomo.Var(model.points, within=pyomo.Binary)
    model.x=pyomo.Var(model.points, model.points, within=pyomo.Binary)
    model.rhoMax = pyomo.Var(within=pyomo.NonNegativeReals)

    #Add objective funktion
    model.obj=pyomo.Objective(expr=model.rhoMax,sense=pyomo.minimize)