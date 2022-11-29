# Pyomo example for the course "Modellering inden for Prescriptive Analytics" at Aarhus University, Fall 2022
# Author: Jesper Bang Mikkelsen
# Implementation of a electric vehicle routing problem (EVRP) with n-customers nodes and a depot (labeled 0) and r-chargers labeled (n+1,...,r+n)
# The implementation ensures that no vehicle runs empty during the route, the workday of the workers are respected, and no vehicle capacities are violated.
# The  IP solved is given by
# min   sum ( i in 0..n ) sum( j in 0..n) c[i][j]*x[i][j] + sum ( i in 0..n ) sum (r in n+1..n+r) sum( j in 0..n) (c[r][i] + c[r][j])*y[i][r][j]
# s.t.  sum ( i in 0..n) (x[i][j] + sum ( r in n+1..n+r ) y[i][r][j] )== 1,         for all j=1,..,n
#       sum ( j in 0..n : i!=j ) (x[i][j] + sum ( r in n+1..n+r ) y[i][r][j] ) == 1,            for all i=1,..,n
#       sum ( j in 1..n ) (x[0][j] + sum (r in n+1..n+r) y[0][r][j])== m,
#       sum ( i in 1..n ) (x[i][0] + sum (r in n+1..n+r) y[i][r][0]) == m,
#       f[i][j] <= (Q - q[j])*x[i][j] + (Q - q[j])*sum (r in n+1..n+r) y[i][r][j],          for all i,j =0,...,n for all r=n+1,...,n+r
#       sum ( j in 0..n) f[i][j] = sum ( j in 0..n ) f[i][j] + q[i],            for all i=1,...,n
#       b[0] = B
#       epsilon[i][j] - B*sum( r in n+1..n+r ) y[i][r][j] <= 0,         for all i,j=0,...,n
#       epsilon[i][j] + b[i] - B*(1-sum( r in n+1..n+r ) y[i][r][j]) - sum( r in n+1..n+r ) e[i][j]*y[i][r][j] <= B,            for all i,j=0,...,n
#       b[j] - b[i] - epsilon[i][j] + (B + e[i][j])*x[i][j] + (B+e[i][r]+e[r][j])*y[i][r][j] <= B,          for all i,j =0,...,n for all r=n+1,...,n+r
#       b[i] - e[i][r] >= 0,            for all i =1,...,n for all j =0,...,n for all r=n+1,...,n+r
#       b[i] - e[i][0]*x[i][0] - (e[i][r] + e[r][0])*y[i][r][0] >= 0,           for all i =1,...,n for all r=n+1,...,n+r
#       tau[i] - tau[j] + (T + s[i] + t[i][j])*x[i][j] + sum( r in n+1..n+r ) (T + s[i] + t[i][r] + t[r][j])*y[i][r][j] + g*epsilon[i][j] <= T,         for all i,j=1,...,n
#       tau[i] + (s[i] + t[i][0])*x[i][0] + sum( r in n+1..n+r ) (s[i] + t[i][r] + t[r][j])*y[i][r][j] + g*epsilon[i][0] <= T,          for all i=1,...,0
#       x[i][j], y[i][r][j] are all binary
# where c[i][j] is the distance between location i and location j and f[i][j] is an upper bound on the amount of demand
# serviced on the route from the depot to the customer node i.
# Q is the maximum capacity on a vehicle and q[i] is the demand at node i (we assume, that q[0]=0)
# m is the number of vehicles available for dispatching.
# B is the battery capacity of a vehicle and e[i][j] is the energy required for travelling between node i and j.
# b[i] is a lower bound for the battery level of a vehicle upon arriving at a node i, while epsilon[i][j] is the energy recharged while between two node i,j.
# T is the maximum allowed route duration, t[i][j] is the travel time between two nodes i,j, and s[i] is the service time for a node i.
# Finally, tau[i] is the arrival time at node i and g is the time it takes to recharge one unit of energy.

# The readData(...) function uses the readAndWriteJson file to read data from a Json file
import pyomo.environ as pyomo       # Used to model the IP
import readAndWriteJson as rwJson   # Used for reading the data file in Json format
import matplotlib.pyplot as plt     # Used for plotting the result
import math

# Function, taking a dict as argument, and returns a list of lists storing a distance matrix
# "data" must have keys "xCoord" and "yCoord". No error handling at the moment!
def makeDistanceMatrix(data: dict) -> list:
    numNodes = len(data['xCoord'])
    dist = []
    for i in range(numNodes):
        dist.append([])
        for j in range(numNodes):
            tmpDist = (data['xCoord'][i] - data['xCoord'][j]) ** 2 + (data['yCoord'][i] - data['yCoord'][j]) ** 2
            dist[i].append(round(math.sqrt(tmpDist)))
    return dist


# Reads the data from a data file in Json format. Must include
# n = number of customers as an int
# r = number of chargers as an int
# m = number of vehicles as an int
# Q = capacity of the vehicles as an int
# q = list of demands of length n+1
# B = battery capacity of the vehicles as an int
# T = maximum allowed duration of route
# s = list of service times of length n+1
# g = the time it takes for recharging one unit of energy
# e = list of lists containing a energy consumption matrix of size (n+r+1) x (n+r+1).
# t = list of lists containing a travel time matrix of size (n+r+1) x (n+r+1).
# The data file must include either
#   xCoord = list of x-coordinates of length n+r+1
#   yCoord = list of y-coordinates of length n+r+1
# or
#   c = list of lists containing a distance matrix of size (n+r+1) x (n+r+1).
# or both
def readData(filename: str) -> dict:
    data = rwJson.readJsonFileToDictionary(filename)
    if 'c' not in data:
        data['c'] = makeDistanceMatrix(data)
        newFileName = filename + '_new'
        rwJson.saveDictToJsonFile(data, newFileName)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Create model object
    model = pyomo.ConcreteModel()
    # Add some data to the model object
    model.numOfVNodes = data['n']+1
    model.numOfRNodes = data['r']
    model.nodes = range(0, model.numOfVNodes) #Range of dept and customers
    model.customers = range(1, model.numOfVNodes) #Range of customers
    model.chargers= range(model.numOfVNodes,model.numOfVNodes+model.numOfRNodes) #Range of chargers
    # Define the variables
    model.x = pyomo.Var(model.nodes, model.nodes, within=pyomo.Binary) # 1, if vehicle travels directly from node i to j
    model.y = pyomo.Var(model.nodes, model.chargers, model.nodes, within=pyomo.Binary) #1, if vehicle travels from node i to j through charger r
    model.f = pyomo.Var(model.nodes, model.nodes, within=pyomo.NonNegativeReals) # Total quantity to delivered from the depot to customer i
    model.b = pyomo.Var(model.nodes, within=pyomo.NonNegativeReals, bounds=(0, data['B'])) # Battery level of vehicle when reaching node i
    model.epsilon = pyomo.Var(model.nodes, model.nodes, within=pyomo.NonNegativeReals, bounds=(0, data['B'])) # # Energy recharged while travelling from node i to j
    model.tau = pyomo.Var(model.nodes, within=pyomo.NonNegativeReals, bounds=(0, data['T'])) # Arrival time at node i

    # Add the objective function
    model.obj = pyomo.Objective(
        expr=sum(data['c'][i][j]*model.x[i, j] for i in model.nodes for j in model.nodes)+ sum((data['c'][i][r]+data['c'][r][j])*model.y[i,r, j] for i in model.nodes for r in model.chargers for j in model.nodes )
    )

    # Add both the in- and out-degree constraints for the customers
    model.sumToOne = pyomo.ConstraintList()
    for i in model.customers:
        # Out of node i
        model.sumToOne.add(expr=sum(model.x[i, j] for j in model.nodes) + sum(model.y[i,r, j] for r in model.chargers for j in model.nodes) == 1)
        # Into node i
        model.sumToOne.add(expr=sum(model.x[j, i] for j in model.nodes ) + sum(model.y[j,r, i] for r in model.chargers for j in model.nodes )== 1)

    # Add the in- and out-degree constraints for the depot
    model.depotOut = pyomo.Constraint(expr=sum(model.x[0, j] for j in model.nodes) + sum(model.y[0,r,j] for r in model.chargers for j in model.nodes) <= data['m'])
    model.depotIn = pyomo.Constraint(expr=sum(model.x[i, 0] for i in model.nodes) + sum(model.y[i,r,0] for i in model.nodes for r in model.chargers ) <= data['m'])

    # Add capacity constraints
    model.cap = pyomo.ConstraintList()
    for i in model.nodes:
        for j in model.nodes:
            model.cap.add(expr=(data["Q"]-data["q"][j])*model.x[i,j] + sum((data["Q"]-data["q"][j])*model.y[i,r,j] for r in model.chargers) - model.f[i,j] >= 0)

    # Add flow constraints for customers
    model.flow = pyomo.ConstraintList()
    for i in model.customers:
        model.flow.add(expr=sum(model.f[i,j] for j in model.nodes) - sum(model.f[j,i] for j in model.nodes) - data["q"][i] == 0)


    ### EXERCISE: ADD ALL 6 CONSTRAINTS NEEDED TO ENSURE THAT NO VEHICLE BATTERY IS DEPLETED DURING A ROUTE:
    # All vehicles start with a full battery
        # Constraint formulation -->  b[0] = B
    model.b[0].fix(data["B"])

    # Allow only recharging to happen when a charger is visited
        # Constraint formulation --> epsilon[i][j] - B*sum( r in n+1..n+r ) y[i][r][j] <= 0,         for all i,j=0,...,n
    model.chargeAtChargers=pyomo.ConstraintList()
    for i in model.nodes:
        for j in model.nodes:
            model.chargeAtChargers.add(expr=(model.epsilon[i][j]-data["B"]*sum(model.y[i,r,j] for r in model.chargers)))


    # Add constraint ensuring that we do not recharge more than what's possible upon visiting a recharging station
        # Constraint formulation --> epsilon[i][j] + b[i] - B*(1-sum( r in n+1..n+r ) y[i][r][j]) - sum( r in n+1..n+r ) e[i][r]*y[i][r][j] <= B,            for all i,j=0,...,n
    model.maxCharge=pyomo.ConstraintList()
    for i in model.nodes:
        for j in model.nodes:
            model.maxCharge.add(expr=(model.epsilon[i][j]+model.b[i]-data["B"]*(1-sum(model.y[i,r,j] for r in model.chargers))-sum(data["e"][i][r]*model.y[i,r,j] for r in model.chargers)) <=data["B"] )

    # Add constraints for regulating battery levels during a route:
        # Constraint format --> b[j] - b[i] - epsilon[i][j] + (B + e[i][j])*x[i][j] + (B+e[i][r]+e[r][j])*y[i][r][j] <= B,          for all i =0,...,n for all j =1,...,n for all r=n+1,...,n+r
    model.regulateBatteryLevel = pyomo.ConstraintList()
    for i in model.nodes:
        for j in model.customers:
            for r in model.chargers:
                model.regulateBatteryLevel.add(expr=(model.b[j]-model.b[i]-model.epsilon[i][j]+(data["B"]+data["e"][i][j])*model.x[i,j]+(data["B"]+data["e"][i][r]+data["e"][r][j]))<=data["B"])
    # Add constraint for ensuring that we have enough energy to reach a charger
        # Constraint formulation --> b[i] - e[i][r] >= 0,            for all i =1,...,n for all j =0,...,n for all r=n+1,...,n+r
    model.energyForReachingCharger=pyomo.ConstraintList()
    for i in model.customers:
        for j in model.nodes:
            for r in model.chargers:
                model.energyForReachingCharger.add(expr=(model.b[i]-data["e"][i][r]*model.y[i,r,j])>=0)
    # Add constraint for ensuring that we have enough energy to return to depot
        # Constraint formulation --> b[i] - e[i][0]*x[i][0] - (e[i][r] + e[r][0])*y[i][r][0] + epsilon[i][0]>= 0,           for all i =1,...,n for all r=n+1,...,n+r
    model.energyForDepotReturn = pyomo.ConstraintList()
    #sidste begrænsning jeg mangler
    ## TIME CONSTRAINTS:
    # Add constraint for regulating time
    model.regulateTime = pyomo.ConstraintList()
    for i in model.customers:
        for j in model.customers:
            model.regulateTime.add(model.tau[i]-model.tau[j]+(data["T"]+data["s"][i]+data["t"][i][j])*model.x[i,j] + sum((data["T"]+data["s"][i]+data["t"][i][r] +data["t"][r][j])*model.y[i,r,j] for r in model.chargers) + data["g"]*model.epsilon[i,j] <= data["T"])

    # Add constraint for ensuring that we can reach the depot before the end of the workday
    model.returnBeforeT = pyomo.ConstraintList()
    for i in model.customers:
        model.returnBeforeT.add(expr= model.tau[i] + (data["s"][i]+data["t"][i][0])*model.x[i,0] + sum((data["s"][i]+data["t"][i][r]+data["t"][r][0])*model.y[i,r,0] for r in model.chargers) <= data["T"])

    # return the model object
    return model


def solveModel(model: pyomo.ConcreteModel()):
    solver = pyomo.SolverFactory('gurobi')
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel(), data: dict):
    print('Total length of the', data['m'], 'tours are', pyomo.value(model.obj))
    # Find a tour for each vehicle
    lastRouteStarter = 0
    # Make flag for checking if coordinates are available
    coordinatesPresent = ('xCoord' in data) and ('yCoord' in data)
    # Create a route for each vehicle
    for vehicle in range(1, data['m'] + 1):
        # Each route starts at the depot
        if coordinatesPresent:
            displayX = [data['xCoord'][0]]
            displayY = [data['yCoord'][0]]
            labels = [0]
        # Find the customer, that starts this route
        currentNode = 0
        currentCharger = 0
        for j in model.customers:
            ChargerUsed = False
            for r in model.chargers:
                if j>lastRouteStarter and pyomo.value(model.y[0,r,j])>=0.9999:
                    ChargerUsed=True
                    currentNode=j
                    currentCharger=r
                    displayX.append(data['xCoord'][currentCharger])
                    displayY.append(data['yCoord'][currentCharger])
                    labels.append(currentCharger)
                    displayX.append(data['xCoord'][currentNode])
                    displayY.append(data['yCoord'][currentNode])
                    labels.append(currentNode)
                    break
            if ChargerUsed==True: break
            if j > lastRouteStarter and pyomo.value(model.x[0, j]) >= 0.9999:
                currentNode = j
                if coordinatesPresent:
                    displayX.append(data['xCoord'][currentNode])
                    displayY.append(data['yCoord'][currentNode])
                    labels.append(currentNode)
                break

        print('The route for vehicle', vehicle, 'is:')
        if ChargerUsed==True:
            print('0->', currentCharger,'->', currentNode, end='')
        else:
            print('0->', currentNode, end='')
        lastRouteStarter = currentNode

        # Build the route from currentNode back to the depot
        while currentNode != 0:
            for j in model.nodes:
                ChargerUsed = False
                for r in model.chargers:
                    if currentNode !=j and pyomo.value(model.y[currentNode, r, j]) >= 0.9999:
                        ChargerUsed = True
                        currentNode = j
                        currentCharger = r
                        print('->', r,'->', j,end='')
                        displayX.append(data['xCoord'][currentCharger])
                        displayY.append(data['yCoord'][currentCharger])
                        labels.append(currentCharger)
                        displayX.append(data['xCoord'][currentNode])
                        displayY.append(data['yCoord'][currentNode])
                        labels.append(currentNode)
                if ChargerUsed==True: break
                if currentNode != j and pyomo.value(model.x[currentNode, j]) >= 0.9999:
                    print('->', j, end='')
                    currentNode = j
                    if coordinatesPresent:
                        displayX.append(data['xCoord'][currentNode])
                        displayY.append(data['yCoord'][currentNode])
                        labels.append(currentNode)
                    break

        print('\n')
        if coordinatesPresent:
            # Start plotting the solution to a coordinate system if coordinates are present
            if coordinatesPresent:
                plt.plot(displayX, displayY, '-')

    # Plot all nodes if coordinates are present (We use different shapes for depot, customers, and chargers)
    if coordinatesPresent:
        plt.plot(data["xCoord"][0],data["yCoord"][0],"s")
        plt.plot(data["xCoord"][1:data["n"]],data["yCoord"][1:data["n"]],"o")
        plt.plot(data["xCoord"][data["n"]+2:data["n"]+data["r"]+1], data["yCoord"][data["n"]+2:data["n"]+data["r"]+1], "^")
        for i in model.nodes:
            plt.annotate(i, (data["xCoord"][i], data["yCoord"][i]))
        for i in model.chargers:
            plt.annotate(i, (data["xCoord"][i], data["yCoord"][i]))
    plt.show()


def main(filename: str):
    data = readData(filename)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model, data)



if __name__ == '__main__':
    main('E-n22-k4.evrp')