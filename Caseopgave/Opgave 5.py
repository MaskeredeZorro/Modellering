# Pyomo example for the course "Modellering inden for Prescriptive Analytics" at Aarhus University, Fall 2022
# Implementation of a capacitated facility location problem where a set of potential facility
# sites {0,1,2,..,n-1} is given along with a set of customers {0,1,2,..,m-1}.
# A cost for servicing customer j from facility site i is given by c_ij and a cost for opening a facility at site i
# is given by f_i
# In addition, each customer has a demand of d_j units of a product and each facility can supply s_i units of the
# product
# The IP solved is given by
# min   sum ( i in 0..n-1 ) sum( i in 0..m-1 ) c[i][j]*x[i][j] + sum ( i in 0..n-1 ) f[i]*y[i]
# s.t.  sum ( i in 0..n-1 ) x[i][j] == 1,               for all j=0..m-1
#       sum ( j in 0..m-1 ) d[j]*x[i][j] <= s[i]*y[i],  for all i=0..n-1
#       x[i][j] <= y[i],                                for all i in 0..n-1 and all j in 0..m-1
#       y[i] in {0,1}                                   for all i in 0..n-1
#       x[i][j] >= 0                                    for all i in 0..n-1 and j in 0..m-1
# Here y[i]=1 means a facility is opened at site i. x[i][j] gives the proportion of customer j's demand serviced from
# site i
# The readData(...) function uses the readAndWriteJson file to read data from a Json file in the form
# "antallokationer": [list of strings with labels for the sites. One for each site must be provided if any]
# "antalkunder": [list of strings with labels for the customers. One for each site must be provided if any]
# "v_costs": [list of lists with the variable costs matrix]
# "f_costs": [list of fixed opening costs]
# "demand": [list of demands - one for each customer]
# "capacity": [list of capacities - one for each facility]


import pyomo.environ as pyomo  # Used for modelling the IP
import readAndWriteJson as rwJson  # Used to read data from Json file


#Vi har her løst opgave 5. Ved simulationsstudie ligesom før, pr. tavle, ses det at ved 99% jamen så er der 0% sandsynlighed for, at der ikke er nok kapacitet.
#
#
#
#

def readData(filename: str) -> dict:
    data = rwJson.readJsonFileToDictionary(filename)
    return data


def buildModel(data: dict, reduction:float) -> pyomo.ConcreteModel():
    # Define the model
    model = pyomo.ConcreteModel()
    # Copy data to the model
    model.antallokationer = data['n']
    model.antalkunder = data['m']
    model.c = data['c']
    model.f = data['f']
    model.d = data['d']
    model.s = data['s']
    model.antallokationerlen = range(0, len(model.f))
    model.antalkunderlen = range(0, len(model.c[0]))
    # Define x and y variables for the model
    model.x = pyomo.Var(model.antallokationerlen, model.antalkunderlen, within=pyomo.Binary) #Ved NonNegativeReals og bounds er det kontinuert. Ved NonNegativeIntegers er det kun binær
    model.y = pyomo.Var(model.antallokationerlen, within=pyomo.Binary)
    # Add the objective function to the model
    model.obj = pyomo.Objective(
        expr=sum(model.c[i][j] * model.d[j] * model.x[i, j] for i in model.antallokationerlen for j in model.antalkunderlen)
                    + sum(model.f[i]*model.y[i] for i in model.antallokationerlen))
    # Add the "sum to one"-constraints
    model.sumToOne = pyomo.ConstraintList()
    for j in model.antalkunderlen:
        model.sumToOne.add(expr=sum(model.x[i, j] for i in model.antallokationerlen) == 1)
    # Add the capacity constraints
    model.capacities = pyomo.ConstraintList()
    for i in model.antallokationerlen:
        model.capacities.add(expr=sum(model.d[j]*model.x[i,j] for j in model.antalkunderlen) <= reduction*model.s[i]*model.y[i])

    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Define a solver
    solver = pyomo.SolverFactory('gurobi')
    # Solve the model
    solver.solve(model, tee=True)

def displaySolution(model: pyomo.ConcreteModel()):
    # Print optimal objective function value
    print('Optimal objective function value is', pyomo.value(model.obj))
    # Print the open facilities
    for i in model.antallokationerlen:
        if pyomo.value(model.y[i]) >=0.99:
            print(model.antallokationerlen[i], 'is open and the following customers are serviced:')
            for j in model.antalkunderlen:
                if pyomo.value(model.x[i, j]) >=0.99:
                    print(model.antalkunderlen[j], "(", pyomo.value(model.x[i, j])*100, "%)", end=',')
            print('\n')


def main(instance_file_name, reduction: float):
    data = readData(instance_file_name)
    model = buildModel(data, reduction)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    instance_file_name = 'SSCFLP_deterministic_data'
    main(instance_file_name,0.99)