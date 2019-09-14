import sys
import io
try:
    import pycurl
except Exception as e:
    print("missing pycurl, exiting")
    sys.exit(1)

try:
    import gzip
except Exception as e:
    print("missing gzip, exiting")
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

    return (textValue, e)
# parliamant 50 has 18 sessions
# parliament 49 has 20 sessions
# parliament 48 has 20 sessions

def getAllInfo():
    for i in range(1993,9987):
        print("Connecting to vote number", i)
        url = "https://ws.parlament.ch/odata.svc/Voting?$filter=(Language%20eq%20%27EN%27)%20and%20((Decision%20eq%201)%20or%20(Decision%20eq%202)%20or%20(Decision%20eq%203)%20or%20(Decision%20eq%205)%20or%20(Decision%20eq%206)%20or%20(Decision%20eq%207))%20and%20((IdVote%20eq%20"
        url += str(i)
        url += "))&$orderby=LastName%2CFirstName" 
        rawResponse = connectToSite(url)
        response = rawResponse[0].decode("utf8")
        error = rawResponse[1]
        if error:
            with open("./swissRawXML/errorPages", "a") as f:
                f.write(url)
        else:
            with open("./swissRawXML/vote"+ str(i)+".xml", "w") as f:
                f.write(response) 

if __name__ == "__main__":
    getAllInfo()
