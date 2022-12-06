#Print sum:
A=[16,22,21,23,25,24,11,25,22,19]
print(sum(A))


#Print sum vha. liste
A=[16,22,21,23,25,24,11,25,22,19]
theSum=0
for num in A:
    theSum=theSum+num
print(theSum)

#Print summen af tallene i listen for de tal som er mindre end eller lig med 11:
#Print sum vha. sum funktionen:
A=[11,5,18,5,9,12,11,12,16,9]
sumSum=sum(A[i] for i in range(len(A)) if A[i] <=11)
print(sumSum)

#Print summen af tallene i listen for de tal som er mindre end eller lig med 11:
#Print sum vha. et forloop
A=[11,5,18,5,9,12,11,12,16,9]
sumListe=0
for a in A:
    if a<=11:
        sumListe=sumListe+a
print(sumListe)


#Knapsack problem hvor vi summerer profitten og omkostninger hvis den aktiveres, vha. en sum funktion:
Profit=[70,55,65,100,65,95,90,75,50,100]
Omkostning=[35,30,45,50,50,40,60,60,30,80]
Budget=360
x=[1,1,0,1,1,1,1,1,1,0]

sumProfit=sum(Profit[i] for i in range(len(Profit)) if x[i]==1)
sumOmk=sum(Omkostning[i] for i in range(len(Profit)) if x[i]==1)
print(sumProfit)
print(sumOmk)

#Knapsack problem hvor vi summerer profitten og omkostninger hvis den aktiveres, vha. et forloop:
#Vi har her 2 lister i spil
Profit=[70,55,65,100,65,95,90,75,50,100]
Omkostning=[35,30,45,50,50,40,60,60,30,80]
Budget=360
x=[1,1,0,1,1,1,1,1,1,0]

sumProf=0
sumOmko=0

#Profit sum
for i in range(len(Profit)):
    if x[i] ==1:
        sumProf = sumProf + Profit[i]
print(sumProf)

#Omk sum
for i in range(len(Omkostning)):
    if x[i] ==1:
        sumOmko = sumOmko + Omkostning[i]
print(sumOmko)


#Finde den største værdi i en liste ved et forloop (kan også bare bruge max(A):
A = [62, 71, 38, 37, 34, 21, 19, 92, 35, 71, 99, 48, 18, 8, 63]

Maks=0
for n in A:
    if n>Maks:
        Maks=n
print(Maks)


#Funktion som tjekker om løsningen til et Knapsack problem er feasible:
def kpChecker(solution:list,costs:list,budget:int)->bool:
    totalCosts=sum(costs[i] for i in range(len(costs)) if 1 == solution[i])
    if totalCosts<=budget:
      return True
    else:
      return False

#Tjekke løsning:

costs=[35,30,45,50,50,40,60,60,30,80]
budget=360
solution=[[1,1,1,1,0,0,1,1,1,1,1],
[2,1,1,1,1,1,1,1,1,1,0],
[3,1,1,1,1,0,1,1,0,0,1],
[4,1,1,1,0,1,1,1,1,1,1],
[5,1,0,1,0,1,1,0,1,1,1],
[6,1,1,1,1,1,0,0,1,0,1],
[7,1,1,1,1,1,0,1,1,0,1],
[8,0,1,1,1,1,1,1,1,0,1]]

for sol in solution:
    print(kpChecker(sol,costs,budget))
