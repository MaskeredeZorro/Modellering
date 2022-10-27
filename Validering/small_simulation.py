# Silly little simulation of sum of uniformly distributed values with an expected sum-value of 25.
# What is the probability, that the sum exceeds 25?

import numpy as np
import math
from matplotlib import pyplot as plt


def makeHistogram(listOfTotalDemands: list):
    bins = np.linspace(math.ceil(min(listOfTotalDemands)),
                   math.floor(max(listOfTotalDemands)),
                   20)  # fixed number of bins
    plt.xlim([min(listOfTotalDemands) - 5, max(listOfTotalDemands) + 5])

    plt.hist(listOfTotalDemands, bins=bins, alpha=0.5)
    plt.title('Histogram of total demand data (fixed number of bins)')
    plt.xlabel('Total demand (20 evenly spaced bins)')
    plt.ylabel('count')
    plt.show()


def simulation(numOfReplications: int):
    demand1 = np.random.uniform(5, 7, numOfReplications)
    demand2 = np.random.uniform(4, 8, numOfReplications)
    demand3 = np.random.uniform(5, 7, numOfReplications)
    demand4 = np.random.uniform(3, 9, numOfReplications)

    numOfFails = 0
    totalDemandList = []
    for i in range(numOfReplications):
        totalDemand = demand1[i] + demand2[i] + demand3[i] + demand4[i]
        totalDemandList.append(totalDemand)
        if totalDemand > 25:
            numOfFails += 1
    print('Probability of failing : ', (numOfFails / numOfReplications)*100, '%')
    makeHistogram(totalDemandList)


def main():
    replications = 10000000  # 10.000.000
    simulation(replications)


if __name__ == '__main__':
    main()