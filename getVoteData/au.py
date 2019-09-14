import sys
import io
import gzip
import json
try:
    import pycurl
except Exception as e:
    print("pycurl not installed, exiting")
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
        e = True

    buffer.close()

    return (textValue, e)

def allMPIds():
    url = "https://theyvoteforyou.org.au/api/v1/people.json?key=RO%2BCuVM%2BajyxG98UXndt"
    rawJson = connectToSite(url)[0]
    readable = json.loads(rawJson)

    allIds = []
    for politician in readable:
        allIds.append(politician["id"])

    return sorted(allIds)


def getPoliticianStat(id):
    url = "https://theyvoteforyou.org.au/api/v1/people/" + str(id) +".json?key=RO%2BCuVM%2BajyxG98UXndt"
    data = connectToSite(url)[0]
    readable = json.loads(data)
    numRebellions = readable["rebellions"]
    numVotesAttended = readable["votes_attended"]
    party = readable["latest_member"]["party"]
    return {"numRebellions" : numRebellions,
            "numVotesAttended" : numVotesAttended,
            "party" : party}

def getAllPoliticianStats():
    allIds = allMPIds()
    print(allIds)
    allVoteStats = []
    for id in allIds:
        print(id)
        allVoteStats.append(getPoliticianStat(id))
    with open("auVoteData2.json", "w") as f:
        f.write(json.dumps(allVoteStats))

if __name__ == "__main__":
    getAllPoliticianStats()
