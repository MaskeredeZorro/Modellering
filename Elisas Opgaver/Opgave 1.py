import pyomo.environ as pyomo  # Used for modelling the IP
import readAndWriteJson as rwJson  # Used to read data from Json file

def readData(filename: str) -> dict:
    data = rwJson.readJsonFileToDictionary(filename)
    data['nrPoints'] = len(data['municipalities'])
    return data

def buildModel(data: dict) -> pyomo.ConcreteModel():
    # Define the model
    model = pyomo.ConcreteModel()
    # Add data
    model.kommuner = data['municipalities']
    model.fasteomkostninger = data['basis_price']
    model.mia = 1000000000
    model.basiskapacitet = data['basis_capacity']
    model.ekstraomkostninger = data['ext_price']
    model.Defterspørgsel2022 = data['inhab2022']
    model.Defterspørgsel2030 = data['inhab2030']
    model.distances = data['distances']
    model.travel_times = data['travel_times']
    model.AntalSygehuse = data['p']
    model.AntalKommuner = data['nrPoints']
    model.RangeAntalKommuner = range(0,len(model.kommuner))
    #Define variables
    model.x=pyomo.Var(model.RangeAntalKommuner,model.RangeAntalKommuner, within=pyomo.Binary)
    model.y=pyomo.Var(model.RangeAntalKommuner, within=pyomo.Binary)
    model.z=pyomo.Var(model.RangeAntalKommuner, within=pyomo.NonNegativeIntegers)
    #Add objective function
    model.obj=pyomo.Objective(expr=(sum(model.fasteomkostninger[i]*model.y[i]*model.mia for i in model.RangeAntalKommuner) +(sum(model.ekstraomkostninger[i]*model.z[i] for i in model.RangeAntalKommuner))), sense=pyomo.minimize)
    #Alle kommuner skal knyttes til ét sygehus
    model.AlleKommuner = pyomo.ConstraintList()
    for j in model.RangeAntalKommuner:
        model.AlleKommuner.add(expr=sum(model.x[i,j] for i in model.RangeAntalKommuner) == 1)
    #Kapacitetsbegrænsning 2022
    model.Kapacitet2022 = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        model.Kapacitet2022.add(expr=(sum(model.Defterspørgsel2022[j] * model.x[i,j] for j in model.RangeAntalKommuner) <= model.basiskapacitet[i] * model.y[i] + 1000 * model.z[i]))
    # Kapacitetsbegrænsning 2030
    model.Kapacitet2030 = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        model.Kapacitet2030.add(expr=(sum(model.Defterspørgsel2030[j] * model.x[i, j] for j in model.RangeAntalKommuner) <= model.basiskapacitet[i] * model.y[i] + 1000 * model.z[i]))
    #Sørg for maksimalt udvidelse på 50(000) patienter for hvert sygehus
    model.MaksimalUdvidelse = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        model.MaksimalUdvidelse.add(expr=model.z[i] <= 50*model.y[i])
    #Sygehus skal åbnes hvis kommune er tildelt
    model.ÅbenSygehusHvisKommune = pyomo.ConstraintList()
    for i in model.RangeAntalKommuner:
        for j in model.RangeAntalKommuner:
            model.ÅbenSygehusHvisKommune.add(expr=model.x[i,j] <= model.y[i])
    #Åben specifikt x antal sygehuse
    model.ÅbenAntalSygehuse = pyomo.Constraint(expr=sum(model.y[i] for i in model.RangeAntalKommuner) == model.AntalSygehuse)
    return model


def solveModel(model: pyomo.ConcreteModel()):
    # Define a solver
    solver = pyomo.SolverFactory('cplex')
    # Solve the model
    solver.solve(model, tee=True)


def displaySolution(model: pyomo.ConcreteModel()):
    # Print optimal objective function value
    print('Optimal objective function value is', pyomo.value(model.obj))
    # Print the open facilities
    for i in model.RangeAntalKommuner:
        if pyomo.value(model.y[i]) == 1:
            print(model.kommuner[i], 'is open and the following customers are serviced:')
            for j in model.RangeAntalKommuner:
                if pyomo.value(model.x[i, j]) == 1:
                    print(model.kommuner[j], end=',')
            print('\n')


def main(instance_file_name):
    data = readData(instance_file_name)
    model = buildModel(data)
    solveModel(model)
    displaySolution(model)


if __name__ == '__main__':
    instance_file_name = 'Prøve'
    main(instance_file_name)
