try:
    import xmltodict
except Exception as e:
    print("xmltodict not installed, exiting")
    sys.exit(1)

from typing import List
from os import listdir
from os.path import join
from Representative import Representative
from Vote import Vote
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

def readCanada(path: str, country: str) -> List[Representative]:
    """ retreive all of the relevant xml files.
        Generate all the relevant Vote objects as well as the relevant Representative objects
        Return a dictionary with keys of the representative's name, and values of Representative objects
    """
    # get the full list of file names that contain the relevante xml files
    fileNames = listdir(path)
    cleanFileNames = []
    for file in fileNames: 
        fullFileNames = join(path, file)
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
