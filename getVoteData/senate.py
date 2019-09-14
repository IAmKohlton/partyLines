import sys
import gzip
import io
import re
import json
try:
    import pycurl
except Exception as e:
    print("pycurl not installed, exiting")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except Exception as e:
    print("Beautiful soup not installed, exiting")
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

def getNumVotesInYear(url):
    response = connectToSite(url)[0]
    soup = BeautifulSoup(response, "html.parser")
    relevantCol = soup.find("div", id="secondary_col2")
    allAs = relevantCol.find_all("a")
    firstVote = allAs[2]
    voteString = firstVote.string
    firstVoteNumber = int(voteString.split()[0])
    return firstVoteNumber

def getNumVotesInAllYears():
    urls = {}
    # do all the first years of the session
    for i in range(101, 117):
        url = "https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_%d_1.htm" % i
        key = "%d_%d" % (i,1)
        urls[key] = url

    for i in range(101, 116):
        url = "https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_%d_2.htm" % i
        key = "%d_%d" % (i,2)
        urls[key] = url
    
    votesInYear = {}
    for tup in urls:
        url = urls[tup]
        numVotes = getNumVotesInYear(url)
        votesInYear[tup] = numVotes

    with open("senateNumVotes.json", "w") as f:
        f.write(json.dumps(votesInYear))


def formatSoupString(string):
    string = string.split("\n")
    formatString = []
    pattern = re.compile("<.*?>")
    beforeBracketPattern = re.compile(".*\(")
    afterBracketPattern = re.compile("\).*")
    for line in string:
        voteResult = {}
        newLine = re.sub(pattern, "", line)
        if newLine != "":
            # get which vote it is
            # this assumes no ones last name contains Yea, or Nay in it
            if "Yea" in newLine:
                voteResult["vote"] = "Yea"
            elif "Nay" in newLine:
                voteResult["vote"] = "Nay"
            else:
                voteResult["vote"] = "Not Voting"
            
            # strip everything out of the line that isn't the vote
            newLine = beforeBracketPattern.sub("", newLine)
            newLine = afterBracketPattern.sub("", newLine)
            party = newLine[0]
            voteResult["party"] = party

            formatString.append(voteResult)
    return formatString

def getVote(url):
    response = connectToSite(url)[0]
    soup = BeautifulSoup(response, "html.parser")
    try:
        byName = soup.find("div", class_ = "newspaperDisplay_3column")
        byName = byName.find("span")
    except Exception as e:
        return None

    formattedVotes = formatSoupString(str(byName))
    parties = {}
    for vote in formattedVotes:
        party = vote["party"]
        if not party in parties:
            parties[party] = [0,0]
        if vote["vote"] == "Yea":
            parties[party][0] += 1
        elif vote["vote"] == "Nay":
            parties[party][1] += 1

    # now get the congress number from the url
    year = url.split("?")[1]
    year = year.split("&")[0]
    year = year.split("=")[1]
    parties["Parliament"] = year
    return parties
    

def getAllVotes():
    with open("senateModifiedVotes.json") as f:
        js = json.loads(f.read())

    for session in js:
        votesForSession = []
        numVotes = js[session]
        congress, sess = session.split("_")
        for i in range(1, numVotes+1):
            url = "https://www.senate.gov/legislative/LIS/roll_call_lists/roll_call_vote_cfm.cfm?congress=%d&session=%d&vote=%05d" %(int(congress), int(sess), i)
            print(url)
            voteResult = getVote(url)
            if voteResult != None:
                votesForSession.append(voteResult)
        with open("senateVotes/%s" % session, "w") as f:
            f.write(json.dumps(votesForSession))
            

if __name__ == "__main__":
    # print(getVote("https://www.senate.gov/legislative/LIS/roll_call_lists/roll_call_vote_cfm.cfm?congress=106&session=2&vote=00297"))
    # getNumVotesInYear("https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_113_1.htm")
    # getNumVotesInAllYears()
    getAllVotes()
