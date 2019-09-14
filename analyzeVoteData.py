import json
import numpy as np
import pprint
from collections import OrderedDict
import matplotlib.pyplot as plt
import scipy
import scipy.stats
from scipy.stats import binom
import math

def auAverageRebellions(voteData):
    rebels = np.ndarray((len(voteData)))
    for i, person in enumerate(voteData):
        rebellions = person["numRebellions"]
        total = person["numVotesAttended"]
        if total == 0:
            rebels[i] = np.nan
        else:
            rebels[i] = rebellions/total
    
    return {"mean" : np.nanmean(rebels) * 100,
            "variance" : np.nanvar(rebels) * 100,}
            # "lower quantile" : np.nanquantile(rebels, 0.25) * 100,
            # "upper quantile" : np.nanquantile(rebels, 0.75) * 100

def analyzeAUVotes(url):
    with open(url) as f:
        voteData = json.loads(f.read())
    print(auAverageRebellions(voteData))

def averageRebellions(voteData):
    rebels = np.ndarray((len(voteData)))
    for i, vote in enumerate(voteData):
        rebellions = 0
        total = 0
        for party in vote:
            if party == "Parliament":
                continue
            total += vote[party][0] + vote[party][1]
            rebellions += min(vote[party][0], vote[party][1])

        if total == 0:
            rebels[i] = np.nan
        else:
            rebels[i] = rebellions/total

    return {"mean" : np.nanmean(rebels) * 100,
            "variance" : np.nanvar(rebels) * 100}


def averageRebellionsPerParty(voteData):
    parties = {}
    for vote in voteData:
        for party in vote:
            if party == "Parliament":
                continue
            if not party in parties:
                parties[party] = []
            total = vote[party][0] + vote[party][1]
            rebellions = min(vote[party][0], vote[party][1])
            if total == 0:
                parties[party].append(np.nan)
            else:
                parties[party].append(rebellions/total)

    results = {}
    for party in parties:
        results[party] = {"mean" : np.nanmean(parties[party]) * 100,
                          "variance" : np.nanvar(parties[party]) * 100}
    return results

def averageRebellionsPerParliament(voteData):
    parliaments = {}
    for vote in voteData:
        total = 0
        rebellions = 0
        parl = ""
        for party in vote:
            if party == "Parliament":
                parl = vote[party]
                if not parl in parliaments:
                    parliaments[parl] = []
            else:
                total += vote[party][0] + vote[party][1]
                rebellions += min(vote[party][0], vote[party][1])
        if total == 0:
            parliaments[parl].append(np.nan)
        else:
            parliaments[parl].append(rebellions / total)

    result = {}
    for parl in parliaments:
        result[parl] = {"mean" : np.nanmean(parliaments[parl]) * 100,
                        "variance" : np.nanvar(parliaments[parl]) * 100}

    return OrderedDict(sorted(result.items(), key=lambda t: t[0]))

def distributionOfRebellions(voteData):
    numRebellions = {}
    for vote in voteData:
        rebels = 0
        for party in vote:
            if party == "Parliament":
                continue
            rebels += min(vote[party][0], vote[party][1])

        if not rebels in numRebellions:
            numRebellions[rebels] = 0
        numRebellions[rebels] += 1

    totalVotes = len(voteData)
    for rebelNumber in numRebellions:
        numRebellions[rebelNumber] /= totalVotes

    return OrderedDict(sorted(numRebellions.items(), key=lambda t: t[0]))


# p is a parameter for the geometric distribution and expected is a list of expected values
def geoMeanSquareError(p, size, actual):
    n = len(actual)
    totalSquareError = 0
    for i in range(n):
        actualValue = actual[i]
        expectedValue = (1-p)**i * p * size # geometric distribution pdf times the size to get the expected number of that outcome in the samply
        totalSquareError += (expectedValue - actualValue) ** 2
    return totalSquareError / n


def binomialMSE(rebelArray, n, p):
    # chi square test will only work when the values are greater than 5 so we'll prune the data set a touch here
    prunedData = []
    greaterThan5 = True
    i = 0
    while greaterThan5:
        theCount = rebelArray.count(i)
        if theCount <= 5:
            greaterThan5 = False
        prunedData.append(theCount)
        i += 1

    pmf = binom.pmf(np.arange(0,i), n, p) * n

    totalSquareError = 0
    for actual, simulated in zip(prunedData, rebelArray):
        totalSquareError += (actual - simulated) ** 2

    return totalSquareError

    

def fitBinomial(voteData):
    numRebellions = []
    numVoters = []
    for vote in voteData:
        rebels = 0
        num = 0
        for party in vote:
            if party == "Parliament":
                continue
            num += vote[party][0] + vote[party][1]
            rebels += min(vote[party][0], vote[party][1])
        numVoters.append(num)
        numRebellions.append(rebels)

    numRebellions.sort()
    
    n = int(np.mean(numVoters))
    # idea is to check a bunch of different MSE's and pick the best
    allErrors = []
    numTests = 10
    for p in range(0,numTests):
        error = binomialMSE(numRebellions, n, p/numTests)
        allErrors.append((p, error))
    print(allErrors)


# check if distribution of rebellions follows a geometric (exponential) distributionn
def checkIfBinomial(voteData):
    numRebellions = []
    for vote in voteData:
        rebels = 0
        for party in vote:
            if party == "Parliament":
                continue
            rebels += min(vote[party][0], vote[party][1])
        numRebellions.append(rebels)

    # numRebellions = (np.random.geometric(p=0.1, size=len(numRebellions)) - 1).tolist()
    size = len(numRebellions)
    x = scipy.arange(size)
    y = numRebellions
    h = plt.hist(y, bins=range(math.floor(max(numRebellions))))

    # plot a best fit exponential distribution vs the real data
#     dist_name = "beta"
#     dist = getattr(scipy.stats, dist_name)
#     param = dist.fit(y)
#     pdf_fitted = dist.pdf(x, *param[:-2], loc=param[-2], scale=param[-1]) * size
#     plt.plot(pdf_fitted, label=dist_name)
#     plt.xlim(math.floor(min(numRebellions)), math.floor(max(numRebellions)))
#     plt.legend(loc='upper right')
#     plt.show()

    # chi square tests only work if the expected values are above 5
    # we either combine categories together, or we disregard numbers below 5.
    # for simplicity we'll do the latter


    # now we have a best fit exponential distribution
    # now we want to do a chi squared test to see whether it is that distribution
    actual = np.array([  numRebellions.count(x) for x in range(np.shape(expected)[0])  ])
    print(actual)
    print(expected)
    # we compare this to pdf_fitted
    

    # will need to do some data analysis so all expected values are above 5
    testResult = scipy.stats.chisquare(actual, f_exp=expected)
    print(testResult)
    return testResult


# checks how often the actual result of the vote is different from when the party would vote as a whole
def rebellionsChangeResult(voteData):
    numVotes = len(voteData)
    numChanges = 0
    for vote in voteData:
        unityVotesFor = 0
        unityVotesAgainst = 0
        actualVotesFor = 0
        actualVotesAgainst = 0
        for party in vote:
            if party == "Parliament":
                continue
            partyVotes = vote[party]
            actualVotesFor += partyVotes[0]
            actualVotesAgainst += partyVotes[1]
            if partyVotes[0] < partyVotes[1]: # if the party voted against the bill
                unityVotesAgainst += (partyVotes[0] + partyVotes[1])
            elif partyVotes[0] > partyVotes[1]:
                unityVotesFor += (partyVotes[0] + partyVotes[1])
        unityResult = unityVotesFor > unityVotesAgainst
        actualResult = actualVotesFor > actualVotesAgainst
        if unityResult != actualResult:
            numChanges += 1

    return (numChanges, numVotes, numChanges/numVotes) 

def analyzeVote(voteData):
    fitBinomial(voteData)

def analyzeVotes(paths):
    data = {}
    for country in paths:
        with open(paths[country]) as f:
            data[country] = analyzeVote(json.loads(f.read()))
        pp = pprint.PrettyPrinter(indent=4)
        print(country)
        pp.pprint(data[country])
        print()

    return data


if __name__ == "__main__":
    # analyzeAUVotes("auVotes.json")
    analysis = analyzeVotes({"canada" : "./voteData/canadaVotes.json", "house" : "./voteData/houseVotes.json", "senate": "./voteData/senateVotes.json", "switzerland" : "./voteData/swissVotes.json", "uk" : "./voteData/ukVotes.json"})
#     for country in analysis:
#         xList = []
#         yList = []
#         for numRebels in analysis[country]:
#             xList.append(numRebels)
#             yList.append(analysis[country][numRebels])
#         plt.plot(xList, yList, 'ro')
#         plt.title(country)
#         plt.show()
# 

