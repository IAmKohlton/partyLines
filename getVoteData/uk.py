import sys
import io
import gzip
import json
import re
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

def parseVotePage(url):
    response = connectToSite(url)[0]
    parsed = BeautifulSoup(response, "html.parser")
    try:
        allVoteBox = parsed.find("div", class_="tab-content")
        ayes = allVoteBox.find("div", id="ayesList")
        nays = allVoteBox.find("div", id="noesList")
    except Exception:
        return None

    ayesPartiesSoup = ayes.find_all(id=re.compile("collapse\-ayes\-.*"))
    naysPartiesSoup = nays.find_all(id=re.compile("collapse\-noes\-.*"))

    allParties = []
    votesFor = {}    
    for party in ayesPartiesSoup:
        innerDiv = party.find("div")
        memberList = innerDiv.find_all("div")
        id = party["id"]
        partyTag = id.split("-")[-1]
        votesFor[partyTag] = len(memberList) // 7
        if len(memberList) % 7 != 0:
            print("not 7 div tags per representative")
        if not partyTag in allParties:
            allParties.append(partyTag)

    votesAgainst = {}
    for party in naysPartiesSoup:
        innerDiv = party.find("div")
        memberList = innerDiv.find_all("div")
        id = party["id"]
        partyTag = id.split("-")[-1]
        votesAgainst[partyTag] = len(memberList) // 7 # 7 is the number of div tags per member
        if len(memberList) % 7 != 0:
            print("not 7 div tags per representative")
        if not partyTag in allParties:
            allParties.append(partyTag)

    allVotes = {}
    for party in allParties:
        partyVote = [0,0]
        if party in votesFor:
            partyVote[0] = votesFor[party]
        if party in votesAgainst:
            partyVote[1] = votesAgainst[party]
        
        allVotes[party] = partyVote

    dateBox = parsed.find("div", class_="date")
    date = dateBox.strong.string
    year = int(date.split(" ")[-1])
    allVotes["Parliament"] = year

    return allVotes

    
def allVotes():
    listOfAllVotes = []
    for i in range(12, 711):
        url = "https://commonsvotes.digiminster.com/Divisions/Details/%s?byMember=false" % i
        print(url)
        vote = parseVotePage(url)
        if vote != None:
            listOfAllVotes.append(parseVotePage(url))
    with open("ukVotes.json", "w") as f:
        f.write(json.dumps(listOfAllVotes))

if __name__ == "__main__":
    # print(parseVotePage("https://commonsvotes.digiminster.com/Divisions/Details/658?byMember=false"))
    allVotes()
