from typing import List
from Representative import Representative
from Vote import Vote
from os.path import join
from os import listdir
from sys import exit
try:
    from xmltodict import parse
except Exception as e:
    print("xmltodict not installed, exiting")
    exit(1)

def readUS(path: str, country: str) -> List[Representative]:
    """ retreive all of the relevant xml files.
        Generate all the relevant Vote objects as well as the relevant Representative objects
        Return a dictionary with keys of the representative's name, and values of Representative objects
    """
    fileNames = listdir(path)
    cleanFileNames = []
    for file in fileNames:
        fullFileNames = join(path, file)
        cleanFileNames.append(fullFileNames)

    allReps = {}
    for voteFile in cleanFileNames:
        with open(voteFile) as f:
            print(voteFile)
            fullXML = parse(f.read())
        metaData = fullXML["rollcall-vote"]["vote-metadata"]
        metaDataTuple = (int(metaData["congress"]), int(metaData["session"][0]), int(metaData["rollcall-num"]))
        try: # for a small amount of votes they don't keep track of totals for this.
             # keeping track of these votes would add uneeded complexity so we instead choose to ignore them
            partyData = metaData["vote-totals"]["totals-by-party"]
        except:
            continue
        voteResult = {}
        for partyResult in partyData:
            voteResult[partyResult["party"]] = (int(partyResult["yea-total"]), int(partyResult["nay-total"]))
        voteOb = Vote(metaDataTuple, voteResult)

        try: # there is a single vote where this line causes a problem
            fullResult = fullXML["rollcall-vote"]["vote-data"]["recorded-vote"]
        except:
            continue
        for representative in fullResult:
            repID = representative["legislator"]
            if representative["vote"] == "Yea" or representative["vote"] == "Aye":
                vote=1
            elif representative["vote"] == "Nay" or representative["vote"] == "No":
                vote=0
            elif representative["vote"] == "Not Voting" or representative["vote"] == "Present":
                continue
            else:
                print(representative["vote"])
            name = repID["#text"] + " " + repID["@state"]
            if not name in allReps:
                newRep = Representative(repID["#text"], repID["@state"], repID["@state"], "USA")
                allReps[name] = newRep

            if repID["@party"] == "R":
                party = "Republican"
            elif repID["@party"] == "D":
                party = "Democratic"
            elif repID["@party"] == "I":
                party = "Independent"

            repOb = allReps[name]
            repOb.addVote(voteOb, vote, party)

    return allReps

