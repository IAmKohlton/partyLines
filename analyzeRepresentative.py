from typing import List
from tabulate import tabulate
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from os.path import join
from pickle import dump, load
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression
from multiprocessing.dummy import Pool as ThreadPool
import statsmodels.api as sm

from Vote import Vote
from Representative import Representative
from readCanada import readCanada
from readUS import readUS
from readSwitzerland import readSwitzerland

def retrieveFromFolder(path: str, country: str) -> List[Representative]:
    """ retreive and process all of the relevant xml files.
        Generate all the relevant Vote, and Representative objects
        Return a dictionary with keys of the representative's name (or unique tag), and values of Representative objects
    """
    if country.lower() == "switzerland" or country.lower() == "swiss":
        return readSwitzerland(path, str)
    elif country.lower() == "usa" or country.lower() == "us":
        return readUS(path, str)
    elif country.lower() == "canada":
        return readCanada(path, str)
    else:
        print("please set the second argument to be one of 'switzerland', 'canada', 'USA'")
        sys.exit(1)
    

# calculate or store allReps in some way. Either:
#   -s reads the xml files and saves a compressed pickle file of the representative dictionary
#      the first argument should be "-s"
#      the second argument should be the path of the folder containing the relevant XML files
#      the third argument should be the name of the country being analyzed
#      the fourth argument should be the name of the pickle file the data is stored in
#   -o open the saved xml files and calculate what's in the bottom part of the sctipt
#      the first argument should be "-o"
#      the second argument should be the file name of the pickle file we want to open and analyze
#      Note: PICKLE IS NOT SECURE. DO NOT USE A PICKLE FILE CREATED BY ANYTHING BUT THIS PROGRAM.

print("Starting load")
if __name__ == "__main__":
    if "-s" == sys.argv[1]:
        allReps = retrieveFromFolder(sys.argv[2], sys.argv[3])
        with open(sys.argv[4], "wb") as f:
            dump(allReps, f)
        sys.exit(0)
    elif "-o" == sys.argv[1]:
        with open(sys.argv[2], "rb") as f:
            allReps = load(f)
    else:
        print("must specify what action should be taken:\n\t" +
                "-s (save raw text to compressed file)\n\t" + 
                "-o (open data from compressed file and compute)")
        sys.exit(1)

print("Starting analysis")

def representativesByNumberOfRebellions(allReps):
    """ Categorize representatives based on the number of times they've voted against party lines
        return a dictionary where the keys are an integer (number of rebellions) and the values are representatives
    """
    repsByNumRebellions = {}
    for rep in allReps:
        totalVotes = allReps[rep].numVotes
        numRebellions = allReps[rep].numRebellions

        if not numRebellions in repsByNumRebellions:
            repsByNumRebellions[numRebellions] = []
        repsByNumRebellions[numRebellions].append(rep)

    return repsByNumRebellions


def repsByNumTimesInGov(allReps):
    """ Categorize representatives based on number of terms they've been in government and take the average rebellion rate of each category
        return a dictionary with keys as number of terms (integer) and values as the average rebellion rate of representatives serving that number of terms
    """
    # categorize representatives by how many terms they've served
    timesInGov = {}
    for rep in allReps:
        numTerms = allReps[rep].numSessionsInGov
        if not numTerms in timesInGov:
            timesInGov[numTerms] = []
        timesInGov[numTerms].append(allReps[rep])

    # take average
    # initialize dict with same keys as timesInGov
    percentRebellions = {}
    for key in sorted(list(timesInGov.keys())):
        totalRebellions = 0
        totalVotes = 0
        for rep in timesInGov[key]:
            totalRebellions += rep.numRebellions
            totalVotes += rep.numRebellions
        average = totalRebellions / totalVotes
        percentRebellions[key] = average
    return percentRebellions

def rebellionsPerPartyPerSession(allReps):
    """ Finds how much a particular party votes against party lines in a particular year
        Similar thing done in other file, but it is repeated here for the sake of compatibility
    """
    parties = {} # will hold parties as keys, and a dictionary as a value
                 # the nested dictionary will have keys of years and values of tuples of (# rebellions in year, # votes in year)
    for repName in allReps:
        rep = allReps[repName]
        for vote in rep.votes:
            voteOb, yeaNay, party = vote
            year = voteOb.voteID[0]
            # initialize parties
            if not party in parties:
                parties[party] = {}
            # initialize a given year for a party
            if not year in parties[party]:
                parties[party][year] = [0,0]

            parties[party][year][1] += 1
            if rep.isRebellion(vote):
                parties[party][year][0] += 1
    return parties



def rebellionsByTermNumber(allReps):
    """ Analyze behaviour of nth term representatives.
        looks at how many rebellions/votes a representative had in their first term, second term and so on
        group the behaviour of all representatives in their first term, similarly group the second term etc.
        returns a list saying how often nth term representatives vote against party lines
    """

    # first entry of terms stores behaviour of first term representatives, second entry stores second term behaviour etc
    terms = []
    for rep in allReps:
        rebsInTerm = {} # will be filled with keys of parliament numbers and values of tuples (number of votes in term, number of rebellions in term)
        for vote in allReps[rep].votes:
            parliamentNumber = vote[0].voteID[0]
            if not parliamentNumber in rebsInTerm:
                rebsInTerm[parliamentNumber] = [0,0]
            rebsInTerm[parliamentNumber][0] += 1
            if allReps[rep].isRebellion(vote):
                rebsInTerm[parliamentNumber][1] += 1

        while len(terms) < len(rebsInTerm):             
            terms.append([])
        # add this representatives behaviour in their nth term to the appropriate list in 'terms'
        for par, sessInGov in zip(sorted(rebsInTerm.keys()), range(len(rebsInTerm))):
            terms[sessInGov].append(rebsInTerm[par])

    # now summarize terms in terms of total percentages
    termSummary = []
    for entry in terms:
        totalVotes = 0
        totalRebellions = 0
        for rep in entry:
            totalVotes += rep[0]
            totalRebellions += rep[1]
        termSummary.append((totalVotes, totalRebellions, totalRebellions/totalVotes*100))
    return termSummary

def rebellionsByTermAndParty(allReps):
    """ Same as rebellionsByTermNumber but also breaks it down by party
    """
    partyTerm = {} # dictionary with keys of (term number, party) and values of (total number of votes, total number of rebellions)
    for rep in allReps:
        rebsInTerm = {} # will be filled with keys of (parliament number, party) values of [number of votes in term, number of rebellions in term]
        for vote in allReps[rep].votes:
            parliamentNumber = vote[0].voteID[0]
            party = vote[2]
            if not (parliamentNumber,party) in rebsInTerm:
                rebsInTerm[(parliamentNumber, party)] = [0,0]
            rebsInTerm[(parliamentNumber, party)][0] += 1
            if allReps[rep].isRebellion(vote):
                rebsInTerm[(parliamentNumber, party)][1] += 1

        # get all parliaments this member has participated in
        parliamentToTerm = {}
        termNumber = 0
        for parNum, party in sorted(rebsInTerm.keys()):
            if not parNum in parliamentToTerm:
                parliamentToTerm[parNum] = termNumber
                termNumber += 1

        for parNumber, party in rebsInTerm:
            currentTerm = parliamentToTerm[parNumber]
            if not (currentTerm, party) in partyTerm:
                partyTerm[(currentTerm, party)] = []

            partyTerm[(currentTerm, party)].append(rebsInTerm[(parNumber, party)])

    # now summarize terms
    termSummary = {}
    for entry in partyTerm:
        totalVotes = 0
        totalRebellions = 0
        for rep in partyTerm[entry]:
            totalVotes += rep[0]
            totalRebellions += rep[1]
        termSummary[entry] = (totalVotes, totalRebellions, totalRebellions/totalVotes*100)
    return termSummary 

def termPartyAccountForYear(allReps):
    """ Does same thing as rebellionsByTermAndParty() but accounts for the parties voting behaviour at the time
    """

    # Dict[party, Dict[session, Dict[term number, (num rebellions, num votes)]]]
    partyData = {}
    for repName in allReps:
        rep = allReps[repName]
        rep.sessionsInGov.sort()
        for vote in rep.votes:
            party = vote[2]
            if not party in partyData:
                partyData[party] = {}
            currentParty = partyData[party]
            session = vote[0].voteID[0]
            termNum = rep.sessionsInGov.index(session)
            if not session in currentParty:
                currentParty[session] = {}
            if not termNum in currentParty[session]:
                currentParty[session][termNum] = [0,0]
            currentParty[session][termNum][1] += 1
            if rep.isRebellion(vote):
                currentParty[session][termNum][0] += 1

  
    # for every party create a data array and a result vector
    # where data array is a 2d array where every row is a list of [year, term]
    # and the corresponding value in result vector is num rebellions / num votes
    for party in partyData:
        dataArray = []
        resultVector = []
        data = partyData[party]
        for session in data:
            for termNum in data[session]:
                rebelData = data[session][termNum]
                rebelRate = rebelData[0] / rebelData[1]
                dataArray.append([session, termNum])
                resultVector.append(rebelRate)
        # prediction = LinearRegression().fit(dataArray, resultVector)
        # print(party, prediction.coef_)
        X2 = sm.add_constant(dataArray)
        est = sm.OLS(resultVector, X2)
        est2 = est.fit()
        print(est2.summary())

def regressWithinParty(termSummary):
    """ Take in termSummary from above method.
        Check if the number of terms a representative is in parliament for affects the amount they rebel
    """
    # sort by party. every key in partyList will be a party 
    # and the values will be how representatives in the party behaved in their first term, second term etc
    partyList = {}
    for term, party in termSummary:
        if not party in partyList:
            partyList[party] = []
        partyList[party].append((term, termSummary[(term,party)][2]))

    for party in partyList:
        termNum = []
        rebellionPercent = []
        for vote in partyList[party]:
            termNum.append(vote[0])
            rebellionPercent.append(vote[1])
        
        # see if representative behaviour over time is linear
        if(len(partyList[party]) > 2):
            print(party)
            regress = linregress(termNum, rebellionPercent)
            print(regress)
            plt.plot(termNum, rebellionPercent, "o")
            plt.plot(termNum, regress[1] + regress[0] * np.array(termNum), "r")
            plt.show()

            print()


# result = rebellionsByTermAndParty(allReps)
# regressWithinParty(result)
# tableVersion = []
# for entry in sorted(result.keys()):
#     data = result[entry]
#     tableVersion.append([entry[0], entry[1], data[0], data[1], data[2]])


def rebellionsByElectionResult(allReps):
    """ Only use for Canada
        See if election result coorelates with individual representative behaviour
    """

    allElectionResults = {}
    for i in range(38,43):
        fileName = join("./voteData/electionResults/", str(i)+".json")
        # this file contains a dictionary for a particular election
        # the keys of the dict are names of the winners, and values are the number of votes each person got in decreasing order
        # only contains name of elected representative
        with open(fileName) as f:
            allElectionResults[i] = (json.loads(f.read()))

    # will contain keys of (representative name, parliament number)
    # and values of (total votes in riding, and vote percent of this representative)
    electionReps = {}
    for parNum in allElectionResults:
        elec = allElectionResults[parNum]
        for rep in elec:
            voteTotal = 0
            for voteForCandidate in elec[rep]:
                voteTotal += voteForCandidate
            electionReps[(rep,parNum)] = voteTotal, elec[rep][0]/voteTotal

    # this just takes the "Mr." and "Mrs." out of names
    modifiedAllReps = {}
    for rep in allReps:
        newKey = " ".join(rep.split()[1:])         
        modifiedAllReps[newKey] = allReps[rep]

    # so there is a reasonable sized problem here
    # I'm getting names from two different locations and kinda hoping that they're the same
    # The problem with this is that in many cases people write their names differntly e.g. Alex vs Alexander
    # This problem is hightened by the fact that one system deals with accents well while the other one doesn't
    # The solution for the time being is to ignore any representative whose name appears in one list but not the other
    # This work around ignores about 10% of the data
    # A very big TODO is to fix this, but that's a task for another day
    rebellionInTerm = {}
    for rep,parNum in electionReps:
        try:
            repRecord = modifiedAllReps[rep] # i have a feeling that something is going to break here
        except:
            continue
        numVotes = 0
        numRebellions = 0
        for vote in repRecord.votes:
            if vote[0].voteID[0] == parNum:
                if repRecord.isRebellion(vote):
                    numRebellions += 1
                numVotes += 1
        if numVotes != 0: # speakers of the house don't vote
            rebellionInTerm[(rep,parNum)] = numRebellions/numVotes*100

    # now we want to try correlate the value in electionReps with the values in rebellionInTerm
    electionRepsList = []
    rebellionInTermList = []
    for name, parNum in rebellionInTerm:
        electionRepsList.append(electionReps[(name,parNum)][1])
        rebellionInTermList.append(rebellionInTerm[(name,parNum)])

    regress = linregress(electionRepsList, rebellionInTermList)
    print(regress)
    plt.plot(electionRepsList, rebellionInTermList, "o")
    plt.plot(electionRepsList, regress[1] + regress[0] * np.array(electionRepsList), "r")
    plt.show()
            
# rebellionsByElectionResult(allReps)

def binarySimilarity(allReps, repName1, repName2):
    """ takes two representatives names and compares how often they vote similarly
        Return a tuple with (repName1, repName2, number of votes they voted the same, number of votes they voted differently)
    """ 
    # create dictionary of representative votes so we can have constant time access
    rep1Votes = {}
    for vote in allReps[repName1].votes:
        id = vote[0].voteID
        rep1Votes[id] = vote

    rep2Votes = {}
    for vote in allReps[repName2].votes:
        id = vote[0].voteID
        rep2Votes[id] = vote

    similarVotes = 0
    dissimilarVotes = 0
    rep1PermanentParty = ""
    rep2PermanentParty = ""
    numSameParty = 0
    for vote1 in rep1Votes:
        if vote1 in rep2Votes:
            rep1Result = rep1Votes[vote1][1]
            rep2Result = rep2Votes[vote1][1]
            
            rep1Party = rep1Votes[vote1][2]
            rep2Party = rep2Votes[vote1][2]

            if rep1PermanentParty == "":
                rep1PermanentParty = rep1Party
            elif rep1PermanentParty != rep1Party:
                rep1PermanentParty = "Changed"

            if rep2PermanentParty == "":
                rep2PermanentParty = rep2Party
            elif rep2PermanentParty != rep2Party:
                rep2PermanentParty = "Changed"

            
            if rep1Party == rep2Party:
                numSameParty += 1

            if rep1Result == rep2Result:
                similarVotes += 1
            else:
                dissimilarVotes += 1
    return (repName1, repName2, similarVotes, dissimilarVotes, numSameParty, rep1PermanentParty, rep2PermanentParty)

def repSimilarity(allReps):
    keySet = list(allReps.keys())
    usedKeys = keySet[:50]
    repsToAnalyze = []
    for repName1 in usedKeys:
        for repName2 in usedKeys:
            if repName1 == repName2:
                continue
            repsToAnalyze.append([allReps, repName1, repName2])
    
    pool = ThreadPool(16)
    result = pool.starmap(binarySimilarity, repsToAnalyze)

    diffPartyResults = []
    for res in result:
        rep1Name, rep2Name, similarVotes, dissimilarVotes, numSameParty, rep1Party, rep2Party = res
        if numSameParty != 0:
            continue
        if similarVotes + dissimilarVotes == 0:
            continue
        ratioSame = similarVotes / (similarVotes + dissimilarVotes)
        diffPartyResults.append((ratioSame, similarVotes + dissimilarVotes, rep1Name,rep1Party, rep2Name, rep2Party))
    sortedDiffParty = sorted(diffPartyResults)
    for line in sortedDiffParty:
        print(line)

# repSimilarity(allReps)

# TODO: this function but make it robust enough to deal with people who switch parties
def similarityToParty(allReps):
    """ Compares how similarly representatives vote compared to the party at large.
        Notes when the most similar party to a representative is not their own party
    """
    returnDict = {}
    for repName in allReps:
        rep = allReps[repName]

        repParty = ""

        parties = {} # contain key of party name, and 2-list of [# similar votes, # different votes]
        for voteObject in rep.votes:
            vote = voteObject[0]
            repVote = voteObject[1]
            partyForThisVote = voteObject[2]

            if repParty == "":
                repParty = partyForThisVote
            elif repParty != partyForThisVote:
                repParty = "Changed"

            for party in vote.voteResult:
                if not party in parties:
                    parties[party] = [0,0]
                partyVotedYes = 1 if vote.voteResult[party][0] > vote.voteResult[party][1] else 0
                if repVote == partyVotedYes:
                    parties[party][0] += 1
                else:
                    parties[party][1] += 1

        similarityScore = {}
        for party in parties:
            totalVotes = parties[party][0] + parties[party][1]
            similarityScore[party] = parties[party][0] / totalVotes
        
        closestParty = ""
        closestPartyScore = 0
        for party in similarityScore:
            if similarityScore[party] > closestPartyScore:
                closestParty = party
                closestPartyScore = similarityScore[party]

        if repParty != "Changed":
            if closestParty != repParty:
                returnDict[repName] = [rep.name, repParty, similarityScore[repParty], closestParty, similarityScore[closestParty]]

    return returnDict

# similarity = similarityToParty(allReps)
# simList = [similarity[key] for key in similarity]
# simList = sorted(simList, key=lambda list: abs(list[2]-list[4]), reverse=True)
# print(tabulate(simList))

def getVoteList(allReps):
    allVotes = {}
    for repName in allReps:
        for vote in allReps[repName].votes:
            voteID = vote[0].voteID
            voteOb = vote[0]
            if not voteID in allVotes:
                allVotes[voteID] = voteOb
    return allVotes

def provinceDefect(allReps):
    allVotes = getVoteList(allReps)

    # classify representatives by province
    provinces = {} # Dict[prov, Dict[repName, repObject]]
    for repName in allReps:
        rep = allReps[repName]
        if not rep.province in provinces:
            provinces[rep.province] = {}
        provinces[rep.province][repName] = rep

    # from here we compare exptected province cohesion against actual province cohesion
    # for every vote we calculate what the majority of the party voted for to get an expected result for the provincial representatives. 
    # from this we calculate expected provincial cohesion
    # we then calculate actual provincial cohesion and see if it's higher

    # start with calculating vote cohesion
    cohesion = {} # Dict[voteId, Dict[party, cohesion]]
    for vote in allVotes:
        cohesion[vote.voteID] = {}
        result = vote.voteResult
        for party in result:
            votedYea = result[party][0] > result[party][1]
            cohesion[vote.voteID][party] = votedYea

    # now we get every representative that participated in a vote from a particular province
    allData = {} # Dict[province, List[(expected cohesion, actual cohesion)]]
    for voteID in allVotes:
        vote = allVotes[voteID]
        for prov in provinces:
            if not prov in allData:
                allData[prov] = []

            repsInProvince = {} # Dict[repName, vote (the kind stored in rep.votes)]
            for repName in provinces[prov]:
                rep = provinces[prov][repName]

                # check if the represntative voted in this vote
                repVote = None
                for vote in rep.votes:
                    currentVoteID = vote[0].voteID
                    if currentVoteID == voteID:
                        repVote = vote
                        break
                if repVote != None:
                    repsInProvince[repName, vote]

            # calculate the expected cohesion
            expectedYea = 0
            expectedNay = 0
            for repName in provinces[prov]:
                currentParty = repsInProvince[repName][2]
                partyVotedYea = cohesion[voteID][currentParty]
                if partyVotedYea:
                    expectedYea += 1
                else:
                    expectedNay += 1
            expectedProvinceCohesion = max(expectedYea, expectedNay) / (expectedYea + expectedNay)
            
            # now calculate actual cohesion
            actualYea = 0
            actualNay = 0
            for repName in provinces[prov]:
                repVote = repsInProvince[repName]
                if repVote[1] == 1:
                    actualYea += 1
                else:
                    actualNay += 1

            actualProvinceCohesion = max(actualYea, actualNay) / (actualYea + actualNay)

            allData[prov].append((expectedProvinceCohesion, actualProvinceCohesion))
    return allData

