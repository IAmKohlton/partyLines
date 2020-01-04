import sys
import io
import gzip
import json
import os.path
from os import listdir
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


def getVote(fileName):
    xml = ""
    with open(fileName, "r") as f:
        try:
            xml = xmltodict.parse(f.read())
        except:
            print("%s caused an error" % fileName)
            return None
    
    try:
        year = xml["feed"]["entry"][0]["content"]["m:properties"]["d:VoteEnd"]["#text"]
        year = int(year.split("-")[0])
    except:
        print("%s caused an error" % fileName)
        return None
    decision = {"Parliament" : year}

    for item in xml["feed"]["entry"]:
        prop = item["content"]["m:properties"]
        party = prop["d:ParlGroupName"]
        vote = int(prop["d:Decision"]["#text"])

        if not party in decision:
            decision[party] = [0,0]

        if vote == 1:
            decision[party][0] += 1
        elif vote == 2:
            decision[party][1] += 1

    return decision

def getAllVotes():
    allFiles = listdir("../voteData/swissRawXML")
    allVotes = []
    i = 0
    for file in allFiles:
        voteResult = getVote("../voteData/swissRawXML/%s" % file)
        if voteResult != None:
            allVotes.append(voteResult)
        if i % 500 == 0:
            print(i)
        i += 1

    with open("swissVotes.json", "w") as f:
        f.write(json.dumps(allVotes))

if __name__ == "__main__":
    getAllVotes()
