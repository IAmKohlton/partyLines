import sys
import io
import gzip
import json
import os
import pickle
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


class Vote(object):
    def __init__(self,voteID, result):
        """
        Specify a voteID, and result for a vote where:
            voteID = (parliament #, session #, vote #)
            voteResult = {party: (num yes, num no), ...}
        """
        self.voteID = voteID
        self.voteResult = result

    def __str__(self):
        return "Parliament: %d, Session: %d, Vote: %d" % self.voteID

    def __lt__(self, other):
        return self.voteID < other.voteID

    def __eq__(self, other):
        return self.voteID == other.voteID

class Representative(object):
    def __init__(self, name, constituency, province):
        """
        Specify a representative based on their:
            name: str
            constituency: str
            party: str
            province: str
            votes: list of tuples (not specified by user at initialization)
        """
        self.name = name
        self.constituency = constituency

        self.province = province
        self.sessionsInGov = []
        self.numSessionsInGov = 0

        # self.votes is a list of (vote object, rep's vote (1 or 0), party )
        self.votes = []
        self.numVotes = 0
        self.numRebellions = 0
        self.rebellionVotes = []

    def __str__(self):
        outputString =  "name: %s, consituency: %s, province: %s, number of votes: %d, number of rebellions: %d" % (self.name, self.constituency, self.province, self.numVotes, self.numRebellions) + "\n"
        outputString += "Rebellion Votes:\n"
        for vote in sorted(self.rebellionVotes):
            outputString += "\t" + str(vote) + "\n"
        return outputString


    def voteString(self):
        outputString = ""
        for v in self.votes:
            outputString += ("vote summary: %s, representative vote: %d\n" % v)
        return outputString

    def __eq__(self, otherRep):
        return self.name == otherRep.name

    def isRebellion(self, voteTuple):
        """Takes in a vote from own voteList
        """
        partyVotedYea = 0
        party = voteTuple[2]
        if voteTuple[0].voteResult[party][0] < voteTuple[0].voteResult[party][1]:
            partyVotedYea = 1
        if partyVotedYea == voteTuple[1]:
            return True
        else:
            return False

    def addVote(self, vote, yeaNay, party):
        self.votes.append((vote, yeaNay, party))
        self.numVotes += 1
        if (not vote.voteID[0] in self.sessionsInGov):
            self.sessionsInGov.append(vote.voteID[0])
            self.numSessionsInGov += 1

        partyVotedYea = 0
        if (vote.voteResult[party][0] < vote.voteResult[party][1]):
            partyVotedYea = 1
        if partyVotedYea == yeaNay:
            self.numRebellions += 1
            self.rebellionVotes.append(vote)



def analyzeVotes(voteDict):
    allParties = {}
    for participant in voteDict:
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


def retrieveFromFolder():
    fileNames = os.listdir("../voteData/canadaRawXML")
    cleanFileNames = []
    for file in fileNames: 
        fullFileNames = os.path.join("../voteData/canadaRawXML", file)
        cleanFileNames.append(fullFileNames)

    allReps = {}
    for voteFile in cleanFileNames:
        with open(voteFile) as f:
            print(voteFile)
            resultDict = xmltodict.parse(f.read())
            allVotesList = resultDict["List"]["VoteParticipant"]
            voteMetaData = voteFile.split("/")[-1][:-4].split("_")
            voteMetaData = (int(voteMetaData[0]), int(voteMetaData[1]), int(voteMetaData[2]))
            
            voteSummary = analyzeVotes(allVotesList)
            voteOb = Vote(voteMetaData, voteSummary)

            for voterRecord in allVotesList:
                currentRepName = voterRecord["Name"]
                if not currentRepName in allReps:
                    newRep = Representative(voterRecord["Name"], voterRecord["ConstituencyName"], voterRecord["Province"])
                    allReps[currentRepName] = newRep
                rep = allReps[currentRepName]
                
                rep.addVote(voteOb, int(voterRecord["Yea"]), voterRecord["PartyName"])
    return allReps
    

# calculate allReps from either pickle file, from xml, or from xml and save as pickle
if "-sc" in sys.argv or "-cs" in sys.argv:
    allReps = retrieveFromFolder()
    with open("data.pickle", "wb") as f:
        pickle.dump(allReps, f)
elif "-s" in sys.argv:
    allReps = retrieveFromFolder()
    with open("data.pickle", "wb") as f:
        pickle.dump(allReps, f)
    sys.exit(0)
elif "-c" in sys.argv:
    allReps = retrieveFromFolder()
elif "-o" in sys.argv:
    with open("data.pickle", "rb") as f:
        allReps = pickle.load(f)
else:
    print("must specify what action should be taken:\n\t-s (save raw text to compressed file)\n\t-c (open raw text and compute)\n\t-o (open data from compressed file and compute),\n\t-sc (both save to compressed file and compute)")
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

    for repList in sorted(list(repsByNumRebellions.keys())):
        print(repList)
        print("\t" + str(repsByNumRebellions[repList]))
        print()

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

rebellionsByTermNumber(allReps)



