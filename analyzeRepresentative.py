from tabulate import tabulate
from typing import Callable, Iterator, Union, Optional, List
import sys
import io
import gzip
import json
import os
import pickle
from scipy.stats import linregress
from functools import total_ordering
from random import random
try:
    import pycurl
except Exception as e:
    print("pycurl not installed, exiting")
    sys.exit(1)

try:
    import xmltodict
except Exception as e:
    print("xmltodict not installed, exiting")
    sys.exit(1)


@total_ordering
class Vote(object):
    """
    A single vote in parliament.
    Contains self.voteID which is a tuple that identifies parliament number, session number, and vote number.
        This tuple has total ordering meaning that it can be compared and sorted easily.
    Contains self.voteResult which is a dictionary that stores the summary result of the vote.
        This dictionary has keys of the party names, and has values of a two entry list where
        the first entry is how many representatives from that party voted yes,
        and the second entry is how many representatives voted no.
    """
    def __init__(self,voteID, result):
        """
        Specify a voteID, and result for a vote where:
            voteID = (parliament #, session #, vote #)
            voteResult = {party: (num yes, num no), ...}
        """
        self.voteID = voteID
        self.voteResult = result

    def __str__(self):
        """ string representation of the vote. Only represents the vote identifier, not the contents
        """
        return "Parliament: %d, Session: %d, Vote: %d" % self.voteID

    def __lt__(self, other):
        """ takes in another Vote object "other" and says whether this is strictly less than "other". This is based on the vote identifier
        """
        return self.voteID < other.voteID

    def __eq__(self, other):
        """ takes in another Vote object "other" and says whether this is the same as "other". This is based on the vote identifier
        """
        return self.voteID == other.voteID

class Representative(object):
    """
    A single representative in parliament.
    Contains their name (str),
    their riding/constituency (str),
    their province (str),
    the number of parliaments they've been in government (int), and which parliaments those were (list)
    the number of votes they've been in (int), and what votes those were (list of 3-tuples (Vote Object, how they voted 1/0, party they represented))
    the number of votes where they rebelled (int), and what votes those were (same type as above)
    """
    def __init__(self, name, constituency, province, country):
        """
        Specify a representative based on their:
            name: str
            constituency: str
            province: str
        """
        self.name = name
        self.constituency = constituency
        self.country = country

        self.province = province
        self.sessionsInGov = []
        self.numSessionsInGov = 0

        # self.votes is a list of (vote object, rep's vote (1 for yea, 0 for nay), party )
        self.votes = []
        self.numVotes = 0
        self.numRebellions = 0
        self.rebellionVotes = []

    def __str__(self):
        """ String representation of the representative. Represents their basic information, and what votes they rebelled in
        """
        outputString =  "name: %s, consituency: %s, province: %s, number of votes: %d, number of rebellions: %d" % (self.name, self.constituency, self.province, self.numVotes, self.numRebellions) + "\n"
        outputString += "Rebellion Votes:\n"
        for vote in sorted(self.rebellionVotes):
            outputString += "\t" + str(vote) + "\n"
        return outputString


    def voteString(self):
        """ String representation of every vote they've participated in
        """
        outputString = ""
        for v in self.votes:
            outputString += ("vote summary: %s, representative vote: %d\n" % v)
        return outputString

    def __eq__(self, otherRep):
        """ checks whether two representatives names are equal
        """
        return self.name == otherRep.name

    def isRebellion(self, voteTuple):
        """Takes in a vote 3-tuple from self.voteList and checks whether it was a rebellion
        """
        partyVotedYea = 0
        party = voteTuple[2]
        # did the party vote yes
        if voteTuple[0].voteResult[party][0] < voteTuple[0].voteResult[party][1]:
            partyVotedYea = 1
        # check if whether the party voted yea is equal to whether the representative voted yea
        if partyVotedYea == voteTuple[1]:
            return True
        else:
            return False

    def addVote(self, vote, yeaNay, party):
        """ Takes in a Vote object, whether the representative voted yea (1 or 0), and what party the representative was in at the time
            Adds it to the vote list, and if it was a rebellion vote it adds it to the the rebellion list
        """
        voteTuple = (vote, yeaNay, party)
        # append to the big vote list
        self.votes.append(voteTuple)
        self.numVotes += 1
        # if we haven't seen this session they had in government yet then add it
        if (not vote.voteID[0] in self.sessionsInGov):
            self.sessionsInGov.append(vote.voteID[0])
            self.numSessionsInGov += 1

        # if the vote is a rebellion vote
        if self.isRebellion(voteTuple):
            self.numRebellions += 1
            self.rebellionVotes.append(vote)



def analyzeVotes(voteDict):
    """ takes in the processed xml gotten from the vote file
        returns a dictionary with keys of parties, and values of 2-tuple where first value is number of yea votes, and second value is number of nay votes
    """
    allParties = {}
    for participant in voteDict:
        # iterate over every representative in the xml, and if record how they each voted
        party = participant["PartyName"]
        votedYes = participant["Yea"]
        votedNo = participant["Nay"]
        if not party in allParties:
            allParties[party] = [0,0]

        if votedYes == "1":
            yesVotes = allParties[party][0]
            allParties[party][0] = yesVotes + 1
        elif votedNo == "1":
            noVotes = allParties[party][1]
            allParties[party][1] = noVotes + 1
    return allParties


def retrieveFromFolder(path: str, country: str) -> List[Representative]:
    """ retreive all of the relevant xml files.
        Generate all the relevant Vote objects as well as the relevant Representative objects
        Return a dictionary with keys of the representative's name, and values of Representative objects
    """
    # get the full list of file names that contain the relevante xml files
    fileNames = os.listdir(path)
    cleanFileNames = []
    for file in fileNames: 
        fullFileNames = os.path.join(path, file)
        cleanFileNames.append(fullFileNames)

    allReps = {}
    for voteFile in cleanFileNames:
        with open(voteFile) as f:
            # open the file, and parse the xml in it
            print(voteFile)
            resultDict = xmltodict.parse(f.read())
            allVotesList = resultDict["List"]["VoteParticipant"]
            voteMetaData = voteFile.split("/")[-1][:-4].split("_") # gets the meta data of the vote from the file name
            voteMetaData = (int(voteMetaData[0]), int(voteMetaData[1]), int(voteMetaData[2]))
            
            # turn the xml into a summarized dictionary
            voteSummary = analyzeVotes(allVotesList)
            voteOb = Vote(voteMetaData, voteSummary)

            # for every representative in the vote, add the vote object to their list of votes
            for voterRecord in allVotesList:
                currentRepName = voterRecord["Name"]
                if not currentRepName in allReps:
                    # if the representative isn't yet in the all reps dictionary, create it and then add it to the dictionary
                    newRep = Representative(voterRecord["Name"], voterRecord["ConstituencyName"], voterRecord["Province"], country)
                    allReps[currentRepName] = newRep

                rep = allReps[currentRepName]
                rep.addVote(voteOb, int(voterRecord["Yea"]), voterRecord["PartyName"])
    return allReps
    

# calculate allReps in some way. Either:
#   -s reads the xml files and saves a compressed pickle file of the representative dictionary
#   -o open the saved xml files and calculate what's in the bottom part of the sctipt
if __name__ == "__main__":
    if "-s" in sys.argv:
        allReps = retrieveFromFolder(sys.argv[2], sys.argv[3])
        with open(sys.argv[4], "wb") as f:
            pickle.dump(allReps, f)
        sys.exit(0)
    elif "-o" in sys.argv:
        with open(sys.argv[2], "rb") as f:
            allReps = pickle.load(f)
    else:
        print("must specify what action should be taken:\n\t-s (save raw text to compressed file)\n\t-o (open data from compressed file and compute)")
        sys.exit(1)


def representativesByNumberOfRebellions(allReps):
    repsByNumRebellions = {}
    for rep in allReps:
        party = allReps[rep].party
        totalVotes = len(allReps[rep].votes)
        numRebellions = 0
        for vote in allReps[rep].votes:
            partyVotedYea = 0
            if vote[0].voteResult[party][0] < vote[0].voteResult[party][1]:
                partyVotedYea = 1
            if partyVotedYea == vote[1]:
                numRebellions += 1

        if not numRebellions in repsByNumRebellions:
            repsByNumRebellions[numRebellions] = []
        
        repsByNumRebellions[numRebellions].append(rep)

    return repsByNumRebellions

def repsByNumTimesInGov(allReps):
    timesInGov = {}
    for rep in allReps:
        if not allReps[rep].numSessionsInGov in timesInGov:
            timesInGov[allReps[rep].numSessionsInGov] = []
        timesInGov[allReps[rep].numSessionsInGov].append(allReps[rep])

    # this works okay but I want to change it to keep track of whether a representative votes more or less as their seat gets safer

    # initialize dict with same keys as timesInGov
    percentRebellions = {}
    for key in sorted(list(timesInGov.keys())):
        runningTotal = 0
        for rep in timesInGov[key]:
            runningTotal += rep.numRebellions / rep.numVotes
        average = runningTotal / len(timesInGov[key])
        print(key, average)

def rebellionsByTermNumber(allReps):
    terms = [] # list of lists of (total number of votes, total number of rebellions)
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
        for par, sessInGov in zip(sorted(rebsInTerm.keys()), range(len(rebsInTerm))):
            terms[sessInGov].append(rebsInTerm[par])

    # now summarize terms
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

def regressWithinParty(termSummary):
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

        if(len(partyList[party]) > 2):
            print(party)
            print(linregress(termNum, rebellionPercent))
            print()


result = rebellionsByTermAndParty(allReps)
regressWithinParty(result)
tableVersion = []
for entry in sorted(result.keys()):
    data = result[entry]
    tableVersion.append([entry[0], entry[1], data[0], data[1], data[2]])
tableVersion = sorted(tableVersion, key=lambda x:x[4])
print(tabulate(tableVersion))


def rebellionsByElectionResult(allReps):
    allElectionResults = {}
    for i in range(38,43):
        fileName = os.path.join("../voteData/electionResults/", str(i)+".json")
        with open(fileName) as f:
            allElectionResults[i] = (json.loads(f.read()))

    electionReps = {}
    for parNum in allElectionResults:
        elec = allElectionResults[parNum]
        for rep in elec:
            voteTotal = 0
            for voteForCandidate in elec[rep]:
                voteTotal += voteForCandidate
            electionReps[(rep,parNum)] = voteTotal, elec[rep][0]/voteTotal

    modifiedAllReps = {}
    for rep in allReps:
        newKey = " ".join(rep.split()[1:])
        modifiedAllReps[newKey] = allReps[rep]


    print(sorted(modifiedAllReps.keys()))

    rebellionInTerm = {}
    for rep,parNum in electionReps:
        repRecord = modifiedAllReps[rep] # i have a feeling that something is going to break here
        numVotes = 0
        numRebellions = 0
        for vote in repRecord.votes:
            if vote[0].voteID[0] == parNum:
                if repRecord.isRebellion(vote):
                    numRebellions += 1
                numVotes += 1

        rebellionInTerm[(rep,parNum)] = numRebellions/numVotes*100

    # now we want to try correlate the value in electionReps with the values in rebellionInTerm
    electionRepsList = []
    rebellionInTermList = []
    for key in electionReps:
        electionRepsList.append(electionReps[key])
        rebellionInTermList.append(rebellionInTerm[key])

    print(linregress(electionRepsList, rebellionInTermList))
            
# rebellionsByElectionResult(allReps)
