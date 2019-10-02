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
        self.voteTuple = voteID
        self.voteResult = result

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

    def __eq__(self, otherRep):
        return self.name == otherRep.name

    def addVote(self, vote, yeaNay):
        self.votes.append((vote, yeaNay))

allReps = []
repNames = [] # check against rep names to see if they're already in the database

for voteFile in cleanFileNames:
    with open(voteFile) as f:
        resultDict = xmltodict.parse(f.read())
        allVotesList = resultDict["List"]["VoteParticipant"]
        for voterRecord in allVotesList:
            if not voterRecord["Name"] in repNames:
                newRep = Representative(voterRecord["Name"], voterRecord["ConstituencyName"], voterRecord["PartyName"], voterRecord["Province"])
                repNames.append(voterRecord["Name"])



