from typing import List
from Representative import Representative
from Vote import Vote
from sys import exit
from os.path import join
from os import listdir
try:
    import xmltodict
except Exception as e:
    print("xmltodict not installed, exiting")
    exit(1)

def analyzeVotes(voteXML):
    allParties = {}
    for representativeXML in voteXML:
        rep = representativeXML["content"]["m:properties"]
        party = rep["d:ParlGroupName"]
        if not party in allParties:
            allParties[party] = [0,0]
        vote = int(rep["d:Decision"]["#text"])
        if vote == 1:
            allParties[party][0] += 1
        elif vote == 2:
            allParties[party][1] += 1
    return allParties
        

def readSwitzerland(path: str, country: str) -> List[Representative]:
    fileNames = listdir(path)
    cleanFileNames = []
    for file in fileNames: 
        fullFileNames = join(path, file)
        cleanFileNames.append(fullFileNames)
    
    allReps = {}
    for voteFile in cleanFileNames:
        with open(voteFile) as f:
            print(voteFile)
            try:
                voteXML = xmltodict.parse(f.read())
            except:
                continue

        metaData = voteXML["feed"]["entry"][0]["content"]["m:properties"]
        voteNumber = int(metaData["d:IdVote"]["#text"])
        try:
            voteSession = metaData["d:IdSession"]["#text"]
        except:
            continue
        sessionNumber = int(voteSession[2:4])
        parNumber = int(voteSession[0:2])
        metaDataTuple = (parNumber, sessionNumber, voteNumber)
        voteSummary = analyzeVotes(voteXML["feed"]["entry"])

        voteOb = Vote(metaDataTuple, voteSummary)

        for repXML in voteXML["feed"]["entry"]:
            rep = repXML["content"]["m:properties"]
            name = int(rep["d:PersonNumber"]["#text"])
            party = rep["d:ParlGroupName"]
            voteContent = int(rep["d:Decision"]["#text"])
            if voteContent == 1:
                vote = 1
            elif voteContent == 2:
                vote = 0
            else:
                continue

            if not name in allReps:
                realName = rep["d:FirstName"] + " " + rep["d:LastName"]
                canton = rep["d:CantonName"]
                country = "Switzerland"
                newRep = Representative(realName, canton, canton, country)
                allReps[name] = newRep

            rep = allReps[name]
            rep.addVote(voteOb, vote, party)
    return allReps

