# Pyomo example for the course "Modellering inden for Prescriptive Analytics" at Aarhus University, Fall 2022
# Implementation of a minimum cost covering location problem where a set of potential facility
# sites {0,1,2,..,n-1} is given along with a set of customers {0,1,2,..,m-1}.
# A cost for opening a facility at site i is given by f_i. Furthermore, a binary matrix (a_ij) is given where
# a_ij = 1 if and only if a facility at site i can cover customer j. In this particular example, an integer p
# specifies the number of open facilities allowed in a fasible solution.
# Finally, for each customer an integer b_j specifies how many facilities should be "within reach" for customer j
# to be fully covered
#
# The IP solved is given by
# min   sum ( i in 0..n-1 ) f[i]*y[i]
# s.t.  sum ( i in 0..n-1 ) a[i][j]*y[i] >= b[j],   for all j=0..m-1
#       sum ( i in 0..n-1 ) y[i] <= p,
#       y[i] all binary
# Here y[i]=1 means a facility is opened at site i.
# The readData(...) function uses the readAndWriteJson file to read data from a Json file
# in the form
# "site_labels": [list of strings with labels for the sites. One for each site must be provided if any]
# "customer_labels": [list of strings with labels for the customers. One for each site must be provided if any]
# "cover_matrix": [list of list. cover_maxtrix[i][j]=1 if and only if facility i can cover customer j. 0 otherwise]
# "fixed_costs": [list of fixed opening costs]
# "b": [list of integers. b[j] specifies the number of facilities needed to cover customer j]
# "p": integer specifying the maximum number of facilities to open in an optimal solution

import pyomo.environ as pyomo  # Used for modelling the IP
import readAndWriteJson as rwJson  # Used to read data from Json file



#--------Maximum cost covering location problem---------------#
#Her ønsker vi at maksimere dækningen af kunder. Det vil sige at vi her finder den optimale lokation af faciliteter for at dække flest mulige kunder.
#   Her kan der eksempelvis være tale om, at dække flest mulige kunder indenfor 45 minutters kørsel.

#Her specificerer vi også HVORNÅR en kunde antages for værende COVERED/dækket. Det kan være at der kun er brug for 1 sygehus for at en kunde er dækket. Kan være det er 3.
#   b er hvad der specificerer hvornår en kunde er dækket
#   p er det maksimale antal faciliteter som vi kan åbne
#--------------------------------------------------------#




def readData(filename: str) -> dict:
    data=rwJson.readJsonFileToDictionary(filename)
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    # create model object
    model=pyomo.ConcreteModel()

    # copy data to model:
    model.site_labels=data["site_labels"]
    model.customer_labels=data["customer_labels"]
    model.a=data["cover_matrix"] #a er for a_ij variablen fra slides. Om en kunde bliver mødt af en facilitet eller ej
    model.f=data["fixed_costs"] #f er for fixed costs fra slides. f_i
    model.b=data["b"] #b er for b fra slides b_j
    model.p=data["p"] #p er for p center fra slides. p

    model.siteRange=range(0,len(model.site_labels)) #der er lige så mange labels som der er faciliteter. Husk at 0 starter som den første. Dette er vores store I
    model.customerRange=range(0,len(model.customer_labels)) #længden af antallet af kunder. Dette er vores store J



    #Define variables:
    model.y=pyomo.Var(model.siteRange, within=pyomo.Binary) #Antallet af variabler er antallet af faciliteter. Vi har her lavet y variablen bineær, som er en af de 3 begrænsninger

    #Add objective function:
    model.obj = pyomo.Objective(expr=sum(model.f[i]*model.y[i] for i in model.siteRange), sense=pyomo.minimize)

    #Add constraints:
    #Covering begrænsning:
    model.coverConstraints=pyomo.ConstraintList()
    for j in model.customerRange: #for hver j'ne kunde af alle kunder
        model.coverConstraints.add(expr=sum(model.a[i][j]*model.y[i] for i in model.siteRange)>=model.b[j])
    #Add cardinality constraint:
    model.cardinality=pyomo.Constraint(expr=sum(model.y[i] for i in model.siteRange)<=model.p)

    return buildModel
def solveModel(model: pyomo.ConcreteModel()):
    #set the solver
    solver=pyomo.SolverFactory("cplex")
    #solve the model
    solver.solve(model, tee=True)

def displaySolution(model: pyomo.ConcreteModel()):
    print("optimal objective function value:", pyomo.value(model.obj))
    for i in model.siteRange:
        if pyomo.value(model.y[i])==1:
            print("Site", model.site_labels[i], "is open")

def main(instance_file_name: str):
    data=readData(instance_file_name)
    model=buildModel(data)
    solveModel(model)
    #displaySolution(model)

if __name__ == '__main__':
    instance_file_name = 'minCostCoveringData'
    main(instance_file_name)
