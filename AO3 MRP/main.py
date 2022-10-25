import pyomo.environ as pyomo
import readAndWriteJson as rwJson
import matplotlib.pyplot as plt
import numpy as np


#-------------Materials requirement planning------------#
#I forlængelse af vores ULS model ønsker vi her at planlægge lagrene af vores råvarer til at kunne producere de forskellige færdigvarer.
#Det vil altså sige, at vi ikke blot laver en produktionsplanlægning (ikke produktionsscheduling), men vi
#planlægger rent faktisk også råmaterialerne som vi har brug for, for at kunne fremstille produkterne
#
#Vi vil tage udgangspunkt i at vi kun har en maskine at arbejde på.
#
#Forskellen på ULS og en MRP er således at produktionen af produkter kæmper om ressourcerne i form af råmaterialer.
#Ved en ULS kæmper produktionen af produkter om ressourcerne i form af maskiner (tror jeg 14/10/22)
#
#-------------------------------------------------------#





def readData(filename: str) -> dict:
    data = rwJson.readJsonFileToDictionary(filename)
    print(rwJson.extractKeyNames(data))
    return data


def buildModel(data: dict) -> pyomo.ConcreteModel():
    model = pyomo.ConcreteModel()
    model.period_labels = data['periods']
    model.product_names = data['products']
    model.periods = range(0, len(model.period_labels))
    model.products = range(0, len(model.product_names))
    model.periods_and_zero = range(-1, len(model.period_labels))
    model.periodsIncludingPast = range(-2, len(model.period_labels)) # OBS: Given positive lead time, we need to include knowledge of past orders/productions
    model.demands = data['demands']
    model.p = data['var_cost']
    model.q = data['fixed_cost']
    model.h = data['inv_cost']
    model.batch = data['batch_sizes']
    model.primoInv = data['primoInventory']
    model.leadTime = data['leadTimes']
    model.r = data['r']
    model.maxInv=data["max_inv"]
    model.maxProd=data["max_prod"]
    model.bigM = [model.maxProd/model.batch[k] for k in model.products]
    model.lagerForbrug=data["lager_forbrug"]
    model.prodCapForbrug=data["Produktionskap_forbrug"]
    # Add variables to the model
    model.x = pyomo.Var(model.products, model.periodsIncludingPast, within=pyomo.NonNegativeIntegers)
    model.y = pyomo.Var(model.products, model.periods, within=pyomo.Binary)
    model.s = pyomo.Var(model.products, model.periods_and_zero, within=pyomo.NonNegativeIntegers)

    # Add objective function
    model.obj=pyomo.Objective(expr=sum(model.p[k][t]*model.batch[k]*model.x[k,t]+model.q[k][t]*model.y[k,t]+model.h[k][t]*model.s[k,t] for k in model.products for t in model.periods))
    # Fix past x-variables to zero
    for k in model.products:
        model.x[k, -2].fix(0)
        model.x[k, -1].fix(0)
    # Add flow conservation constraints
    model.flow_constraint=pyomo.ConstraintList()
    for t in model.periods:
        for k in model.products:
            model.flow_constraint.add(expr=model.s[k,t-1]+model.batch[k]*model.x[k,t-model.leadTime[k]]==model.demands[k][t]+sum(model.r[l][k]*model.batch[l]*model.x[l,t] for l in model.products)+model.s[k,t])
    # Add the indicator constraints
    model.indicators=pyomo.ConstraintList()
    for k in model.products:
        for t in model.periods:
            model.indicators.add(expr=model.x[k,t]<=model.bigM[k]*model.y[k,t])
    # Set max size on production and inventory (in one go)
    model.sharedResources = pyomo.ConstraintList()
    for t in model.periods:
        model.sharedResources.add(expr=sum(model.prodCapForbrug[k]*model.batch[k] * model.x[k, t] for k in model.products)<= data['max_prod'])
        model.sharedResources.add(expr=sum(model.lagerForbrug[k]*model.s[k, t] for k in model.products) <= data['max_inv'])
    # Fix the primo inventory
    for k in model.products:
        model.s[k, -1].fix(model.primoInv[k])
    return model

def solveModel(model: pyomo.ConcreteModel()):
    # Define a solver
    solver = pyomo.SolverFactory('cplex')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    print('Optimal cost is:', pyomo.value(model.obj))
    # Number of periods - used to control placement on the x-axis
    numPeriods = len(model.period_labels)
    # Position of bars on x-axis
    pos = np.arange(numPeriods)



    plt.figure(1)
    # For each product, plot the production plan
    for k in model.products:
        plt.subplot(6, 1, k+1)
        # Extract the optimal variable values
        s_values = [pyomo.value(model.s[k,t]) for t in model.periods]
        x_values = [model.batch[k]*pyomo.value(model.x[k,t]) for t in model.periods]
        # Width of a bar
        width = 0.4
        # Add the three plots to the fig-figure
        plt.bar(pos, model.demands[k], width, label='Demands', color='blue')
        plt.bar(pos + width, s_values, width, label='Inventory level', color='grey')
        plt.plot(pos, x_values, color='darkred', label='Production level')
        # Set the ticks on the x-axis
        plt.xticks(pos + width / 2, model.period_labels)
        # Labels on axis
        plt.xlabel('Periods to plan')
        plt.ylabel('Demand')
        plt.legend()


    # Labels on axis
    plt.xlabel('Periods to plan')
    plt.ylabel('Demand')
    plt.legend()


    # Show the figure
    plt.show()


def main(filename: str):
    data = readData(filename)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    filename = 'MRPdatafile'
    main(filename)