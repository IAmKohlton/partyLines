import os
import json

def main():
    currDir = os.getcwd()
    voteDirectory = currDir + "/senateVotes"
    files = os.listdir(voteDirectory)

    allVotes = []
    for file in files:
        with open("%s/%s" % (voteDirectory, file)) as f:
            content = json.loads(f.read())
            allVotes.extend(content)

    with open("senateVotes.json", "w") as f:
        f.write(json.dumps(allVotes))

if __name__ == "__main__":
    main()
