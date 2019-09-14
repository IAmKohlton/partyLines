import sys
import io
import gzip
import json
import os
from multiprocessing.dummy import Pool as ThreadPool

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
        e = True

    buffer.close()

    return (textValue, e)


def getVote(sess):
    parliament = sess[0]
    session = sess[1]
    vote = sess[2]
    url = "https://www.ourcommons.ca/Parliamentarians/en/HouseVotes/ExportDetailsVotes?output=XML&"
    url += "parliament=" + str(parliament) + "&session=" + str(session) + "&vote=" + str(vote)
    print(url)
    rawVoteStats = connectToSite(url)
    if(rawVoteStats[1] == False):
        fileName = "canadaRawXML/%d_%d_%d.xml" % (parliament, session, vote)
        with open(fileName, "wb") as f:
            f.write(rawVoteStats[0])
    else:
        with open("canadaVotesError2.json", "a") as g:
            g.write(url + "\n")

def getAllVotes():
    # first member of each tuple is the parliament number
    # second member is the session number of that parliament
    # third member is the total number of votes that parliament has done
    # sessionStats = [(38,1,3),(39,1,2), (39,2,5)]
    sessionStats = [(38,1,190),(39,1,219), (39,2,161), (40,1,1), (40,2,158), (40,3,204), (41,1,760), (41,2,467), (42,1,1379)]

    for sess in sessionStats:
        parliament = sess[0]
        session = sess[1]
        numVotes = sess[2]
    
        # if sess == (41,2,467):
        #     startValue = 194
        # else:
        #     startValue = 1
        startValue = 1
        allVotes = [(parliament, session, v) for v in range(startValue, numVotes + 1)]

        pool = ThreadPool(8)
        pool.map(getVote, allVotes)
        pool.close()
        pool.join()


if __name__ == "__main__":
    getAllVotes()

