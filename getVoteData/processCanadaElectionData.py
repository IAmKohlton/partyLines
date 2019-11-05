from os import listdir
from os.path import join
from sys import exit
from json import dumps

for i in range(38,43):
    dirPath = join("../voteData/canadaElections/", str(i))
    winners = {}
    for fileName in listdir(dirPath):
        filePath = join(dirPath, fileName)
        with open(filePath, "r", encoding="iso-8859-15") as f:
            candidateNames = f.readline().strip().split(",")[4:-3]
            candidateTotals = [0 for j in range(len(candidateNames))]
            for line in f:
                splitLine = line.strip().split(",")[4:-3]
                for voteCount, j in zip(splitLine, range(len(splitLine))):
                    try:
                        candidateTotals[j] += int(voteCount)
                    except:
                        continue # this line has some other non-vote number text on it

            winningCandidate = ""
            mostVotes = 0
            for candidate, voteNum in zip(candidateNames, candidateTotals):
                # will break when there's ties
                if mostVotes < voteNum:
                    winningCandidate = candidate
                    mostVotes = voteNum
            
            winners[winningCandidate] = sorted(candidateTotals)

    writeName = join("../voteData/electionResults/", str(i))
    with open(writeName, "w") as f:
        f.write(dumps(winners))
