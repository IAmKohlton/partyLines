import sys
import io
import gzip
import json
import os
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


# model as list of representatives where each representative has a pointer to a vote they participated in

fileNames = os.listdir("../voteData/canadaRawXML")

cleanFileNames = []
for file in fileNames: 
    fullFileNames = os.path.join("../voteData/canadaRawXML", file)
    cleanFileNames.append(fullFileNames)

class Vote(object):
    def __init__(self,voteID, result):
        """
        Specify a voteID, and result for a vote where:
            voteID = (parliament #, session #, vote #)
            voteResult = {party: (num yes, num no)}
        """
        self.voteID = voteID
        self.voteResult = result

    def __str__(self):
        tempList = [str(x) for x in self.voteTuple]
        return "_".join(tempList) + " " + str(self.voteResult)

class Representative(object):
    def __init__(self, name, constituency, party, province):
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
        self.party = party
        self.province = province

        # self.votes is a list of (vote object, rep's vote (1 or 0) )
        self.votes = []

    def __str__(self):
        return "name: %s, consituency: %s, party: %s, province: %s" % (self.name, self.constituency, self.party, self.province)

    def voteString(self):
        outputString = ""
        for v in self.votes:
            outputString += ("vote summary: %s, representative vote: %d\n" % v)
        return outputString

    def __eq__(self, otherRep):
        return self.name == otherRep.name

    def addVote(self, vote, yeaNay):
        self.votes.append((vote, yeaNay))


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

allReps = {}
floorCrossers = [] # if they ever cross the floor don't analyze them

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
            if currentRepName in floorCrossers:
                continue
            if not currentRepName in allReps:
                newRep = Representative(voterRecord["Name"], voterRecord["ConstituencyName"],
                                        voterRecord["PartyName"], voterRecord["Province"])
                allReps[currentRepName] = newRep
            rep = allReps[currentRepName]

            # if they ever switch parties delete them from the database
            if rep.party != voterRecord["PartyName"]:
                del allReps[currentRepName]
                floorCrossers.append(currentRepName)
            
            rep.addVote(voteOb, int(voterRecord["Yea"]))


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
        




