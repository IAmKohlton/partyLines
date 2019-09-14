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

def connectToSite(url):
    curl = pycurl.Curl()
    curl.setopt(pycurl.URL, url)
    curl.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0")

    connectionHeader = ["Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding: gzip, deflate",
            "Accept-Language: en-US,en;q=0.5",
            "Connection: keep-alive",
            "Dnt: 1",
            "Upgrade-Insecure-Requests: 1",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0"]

    curl.setopt(pycurl.HTTPHEADER, connectionHeader)
    buffer = io.BytesIO()
    curl.setopt(pycurl.WRITEFUNCTION, buffer.write)

    e = False
    try:
        curl.perform()
    except Exception as error:
        print(error)
        e = True

    byteValue = buffer.getvalue()
    textValue = byteValue
    try:
        textValue = gzip.decompress(byteValue)
    except Exception as error:
        pass

    buffer.close()
    textValue = textValue.decode("utf8")

    return (textValue, e)

######################
# These functions are to download all the pages with votes in them

# takes in url of format: http://clerk.house.gov/evs/1990/index.asp
def getNumVotesInYear(url):
    page = connectToSite(url)[0]
    soup = BeautifulSoup(page, "html.parser")
    allTableRows = soup.find_all("tr")
    maxDataRow = allTableRows[1]
    firstCol = maxDataRow.find_all("td")[0]
    maxVote = firstCol.string
    return int(maxVote)

def allNumVotes():
    maxVoteInYear = {}
    for i in range(1990,2019):
        url = "http://clerk.house.gov/evs/%d/index.asp" % i
        print(url)
        maxVoteInYear[i] = getNumVotesInYear(url)

    with open("./usHouseRawHTML/numVotes.json", "w") as f:
        f.write(json.dumps(maxVoteInYear))

# I didn't finish so I just wrote it to a json to read here
def getVotesForYear(year, numVotes):
    for vote in range(1,numVotes+1):
        url = "http://clerk.house.gov/evs/%03d/roll%d.xml" % (int(year), int(vote))
        print(url)
        pathToVote = "./usHouseRawHTML/year%d_vote%d" % (int(year), int(vote))

        # if the file hasn't been created yet then create it
        if not os.path.isfile(pathToVote):
            response = connectToSite(url)[0]
            with open(pathToVote, "w") as f:
                f.write(response)

def getVotesForAllYears():
    votesPerYear = {}
    with open("./usHouseRawHTML/numVotes.json", "r") as f:
        votesPerYear = json.loads(f.read())
    for year in votesPerYear:
        getVotesForYear(year, votesPerYear[year])



def getCertainVotesInYear(year):
    for vote in range(1,100):
        url = "http://clerk.house.gov/evs/%d/roll%03d.xml" % (int(year), int(vote))
        print(url)
        pathToVote = "./usHouseRawHTML/year%d_vote%03d" % (int(year), int(vote))

        # if the file hasn't been created yet then create it
        if not os.path.isfile(pathToVote):
            response = connectToSite(url)[0]
            with open(pathToVote, "w") as f:
                f.write(response)

def getCertainVotes():
    for year in range(1990, 2019):
        getCertainVotesInYear(year)
#############################
# these parts are to analyze the downloaded files

def voteToInt(data):
    try:
        value = int(data.string)
    except Exception as e:
        value = 0
    return value

def getVoteNumbers(fileName):
    xml = ""
    with open(fileName) as f:
        try:
            xml = xmltodict.parse(f.read())
        except:
            print("%s caused an error" % fileName)
            return None
    
    # initialize with the congress number. called parlement
    vote = {"Parliament" : int(xml["rollcall-vote"]["vote-metadata"]["congress"])}

    
    try:
        listOfPartyResults = xml["rollcall-vote"]["vote-metadata"]["vote-totals"]["totals-by-party"]
    except:
        print("%s caused an error" % fileName)
        return None
    for party in listOfPartyResults:
        partyName = party["party"]
        numYes = int(party["yea-total"])
        numNo = int(party["nay-total"])
        vote[partyName] = [numYes, numNo]
        
    return vote

def getAllVotes():
    allFiles = listdir("./usHouseRawHTML")
    allVotes = []
    i = 0
    for file in allFiles:
        voteResult = getVoteNumbers("./usHouseRawHTML/%s" % file)
        if voteResult != None:
            allVotes.append(voteResult)
        if i %1000 == 0:
            print("done %d" % i)
        i += 1

    with open("usHouse.json", "w") as f:
        f.write(json.dumps(allVotes))

if __name__ == "__main__":
    getAllVotes()
    # getCertainVotes()
    # print(getVoteNumbers("./usHouseRawHTML/year2008_vote397"))
