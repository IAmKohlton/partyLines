import json
import numpy as np
import pprint
from collections import OrderedDict
import matplotlib.pyplot as plt
import scipy
from scipy.stats import linregress
from scipy.stats import chisquare
from scipy.stats import binom
from scipy.stats import fisher_exact
import math
from tabulate import tabulate

# def auAverageRebellions(voteData):
#     rebels = np.ndarray((len(voteData)))
#     for i, person in enumerate(voteData):
#         rebellions = person["numRebellions"]
#         total = person["numVotesAttended"]
#         if total == 0:
#             rebels[i] = np.nan
#         else:
#             rebels[i] = rebellions/total
#     
#     return {"mean" : np.nanmean(rebels) * 100,
#             "variance" : np.nanvar(rebels) * 100,}
#             # "lower quantile" : np.nanquantile(rebels, 0.25) * 100,
#             # "upper quantile" : np.nanquantile(rebels, 0.75) * 100
# 
# def analyzeAUVotes(url):
#     with open(url) as f:
#         voteData = json.loads(f.read())
#     print(auAverageRebellions(voteData))

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


def regressOnRebPerParliament(voteData):
    perParliament = averageRebellionsPerParliament(voteData)
    parliamentNumbers = []
    means = []
    for key in perParliament:
        parliamentNumbers.append(key)
        means.append(perParliament[key]["mean"])
    minParliament = min(parliamentNumbers)
    parliamentNumbers = [x-minParliament for x in parliamentNumbers]
    regress = linregress(parliamentNumbers, means)
    plt.plot(parliamentNumbers, means, "o")
    plt.plot(parliamentNumbers, regress[1]+regress[0]*np.array(parliamentNumbers), "r")
    plt.show()
    return regress

def rebPerPartyAndParliament(voteData):
    parliaments = {}
    for vote in voteData:
        if not vote["Parliament"] in parliaments:
            parliaments[vote["Parliament"]] = {}
        for party in vote:
            if party == "Parliament":
                continue
            if not party in parliaments[vote["Parliament"]]:
                parliaments[vote["Parliament"]][party] = []

            partyVotes = vote[party][0] + vote[party][1]
            rebellions = min(vote[party][0], vote[party][1])
            parliaments[vote["Parliament"]][party].append((partyVotes, rebellions))
    totals = {}
    for parlNumber in parliaments:
        totals[parlNumber] = {}
        for party in parliaments[parlNumber]:
            totalVotes = 0
            totalRebellions = 0
            for vote in parliaments[parlNumber][party]:
                totalVotes += vote[0]
                totalRebellions += vote[1]
            if totalVotes != 0:
                totals[parlNumber][party] = totalRebellions/totalVotes

    # convert to tabulate-able table
    partySet = []
    parlSet = []
    for parlNumber in totals:
        parlSet.append(parlNumber)
        for party in totals[parlNumber]:
            if not party in partySet:
                partySet.append(party)
    parlSet.sort()
    partySet.sort()
    outputTable = []
    for parl in parlSet:
        row = [parl]
        for party in partySet:
            if party in totals[parl]:
                row.append(totals[parl][party]*100)
            else:
                row.append(-1)
        outputTable.append(row)
    partySet.insert(0,"Time")
    print(tabulate(outputTable, headers=partySet))
    outputTable.insert(0, partySet)
    return outputTable


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


def binomialMSE(prunedData, p, i):
    pmf = binom.pmf(np.arange(0,i+1), i, p) * (np.sum(prunedData))
    totalSquareError = 0
    for actual, simulated in zip(prunedData, pmf):
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
    

    # chi square test will only work when the values are greater than 5 so we'll prune the data set a touch here
    prunedData = []
    greaterThan5 = True
    i = 0
    while greaterThan5:
        theCount = numRebellions.count(i)
        if theCount <= 5:
            greaterThan5 = False
        prunedData.append(theCount)
        i += 1


    n = int(np.mean(numVoters))
    # idea is to check a bunch of different MSE's and pick the best
    allErrors = []
    numTests = 100000
    for p in range(0,numTests+1):
        error = binomialMSE(prunedData, p/(numTests), i)
        allErrors.append((p/(numTests), error))
    
    sortedErrors = sorted(allErrors, key = lambda t: t[1])
    pVals = [x[0] for x in sortedErrors[0:100]]
    minVals = min(pVals)
    maxVals = max(pVals)
    print(minVals, maxVals)

    allErrors = []
    numTests = 100000
    for p in np.arange(minVals,maxVals, (maxVals-minVals) /numTests ):
        error = binomialMSE(prunedData, p, i)
        allErrors.append((p, error))
    
    sortedErrors = sorted(allErrors, key = lambda t: t[1])
    pVals = [x[0] for x in sortedErrors[0:100]]
    print(min(pVals), max(pVals))
    return sortedErrors[0]


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

    numRebellions.sort()
    optimalP = fitBinomial(voteData)[0]

    # prune the data in the same way as fitBinomial does it
    prunedData = []
    greaterThan5 = True
    i = 0
    while greaterThan5:
        theCount = numRebellions.count(i)
        if theCount <= 5:
            greaterThan5 = False
        prunedData.append(theCount)
        i += 1

    pmf = binom.pmf(np.arange(0,i), i, optimalP) * np.sum(prunedData)
    print(pmf)
    print(prunedData)
    result = chisquare(prunedData, f_exp=pmf)
    print(result)


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

def rebellionCorrelation(voteData):
    parls = {}
    # first we sort the votes by parliament
    for vote in voteData:
        if not vote["Parliament"] in parls:
            parls[vote["Parliament"]] = []
        parls[vote["Parliament"]].append(vote)

    for parliament in parls:
        rebsPerParty = {}
        for party in parls[parliament][0]:
            if party == "Parliament":
                continue
            if parls[parliament][0][party][0] + parls[parliament][0][party][1] > 5: # if the party has more than 5 reps then count them
                rebsPerParty[party] = []

        for vote in parls[parliament]:
            for party in rebsPerParty:
                try:
                    rebels = min(vote[party][0], vote[party][1])
                    total = vote[party][0] + vote[party][1]
                except:
                    rebels = 0
                try:
                    rebsPerParty[party].append(rebels/total)
                except:
                    rebsPerParty[party].append(0)

        for partyA in rebsPerParty:
            for partyB in rebsPerParty:
                if partyA == partyB:
                    continue
                print(partyA, partyB)
                print(linregress(rebsPerParty[partyA], rebsPerParty[partyB]))


def binaryRebellionCorrelation(voteData):
    parls = {}
    # first we sort the votes by parliament
    for vote in voteData:
        if not vote["Parliament"] in parls:
            parls[vote["Parliament"]] = []
        parls[vote["Parliament"]].append(vote)

    for parliament in parls:
        rebsPerParty = {}
        for party in parls[parliament][0]:
            if party == "Parliament":
                continue
            if parls[parliament][0][party][0] + parls[parliament][0][party][1] > 5: # if the party has more than 5 reps then count them
                rebsPerParty[party] = []

        for vote in parls[parliament]:
            for party in rebsPerParty:
                try:
                    rebels = min(vote[party][0], vote[party][1])
                    rebels = 1 if rebels != 0 else 0
                except:
                    rebels = 0
                try:
                    rebsPerParty[party].append(rebels)
                except:
                    rebsPerParty[party].append(0)

        for partyA in rebsPerParty:
            for partyB in rebsPerParty:
                if partyA == partyB:
                    continue
                print(partyA, partyB)
                # print(rebsPerParty[partyA], rebsPerParty[partyB])
                aRebels = rebsPerParty[partyA].count(0)
                bRebels = rebsPerParty[partyB].count(0)

                aNonRebels = rebsPerParty[partyA].count(1)
                bNonRebels = rebsPerParty[partyB].count(1)

                fisherMatrix = np.array([[aNonRebels,bNonRebels], [aRebels, bRebels]])
                print(fisher_exact(fisherMatrix))

                # do a linear regression and a fisher exact test at the same time
                print(linregress(rebsPerParty[partyA], rebsPerParty[partyB]))
                print()

def collectPartyNames(voteData):
    partyNames = []
    for vote in voteData:
        for party in vote:
            if not party in partyNames:
                partyNames.append(party)


def partyCorrelation(voteData):
    partyList = collectPartyNames(voteData)
    voteTogetherMatrix = np.zeros((len(partyList), len(partyNames)))


def savePartyParliamentToFile(path, saveFile):
    with open(path, "r") as f:
        outputTable = rebPerPartyAndParliament(json.loads(f.read()))
    with open(saveFile, "w") as f:
        for line in outputTable:
            line = ["\""+str(x)+"\"" for x in line]
            f.write(",".join(line)+"\n")


def partySize(voteData):
    # organize votes by parliament number
    parliamentPartyRebellion = {} # Dict[parl#: Dict[party: (votes, rebellions, # of votes)]]
    for vote in voteData:
        parl = vote["Parliament"]
        if not parl in parliamentPartyRebellion:
            parliamentPartyRebellion[parl] = {}
        for party in vote:
            if party == "Parliament":
                continue
            if not party in parliamentPartyRebellion[parl]:
                parliamentPartyRebellion[parl][party] = [0,0,0]
            numReps = vote[party][0] + vote[party][1]
            numRebellions = min(vote[party][0], vote[party][1])
            parliamentPartyRebellion[parl][party][0] += numReps
            parliamentPartyRebellion[parl][party][1] += numRebellions
            parliamentPartyRebellion[parl][party][2] += 1

    sizeToRebRatio = []
    for parl in parliamentPartyRebellion:
        for party in parliamentPartyRebellion[parl]:
            totalRepVotes, rebellions, numVotes = parliamentPartyRebellion[parl][party]
            if totalRepVotes == 0 or numVotes == 0:
                print(parl, party)
                continue

            numberOfReps = totalRepVotes / numVotes
            rebellionPercentage = rebellions / totalRepVotes
            sizeToRebRatio.append((numberOfReps, rebellionPercentage))

    return linregress(sizeToRebRatio)
    

def analyzeVote(voteData):
    return partySize(voteData)

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
    # savePartyParliamentToFile("./voteData/canadaVotes.json", "./canadaOverTime.csv")
    # savePartyParliamentToFile("./voteData/houseVotes.json", "./usOverTime.csv")
    # savePartyParliamentToFile("./voteData/swissVotes.json", "./swissOverTime.csv")

    # analysis = analyzeVotes({"canada" : "./voteData/canadaVotes.json"})
    analysis = analyzeVotes({"canada" : "./voteData/canadaVotes.json", "US" : "./voteData/houseVotes.json", "switzerland" : "./voteData/swissVotes.json"})
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

