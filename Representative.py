class Representative(object):
    """
    A single representative in parliament.
    Contains their name (str),
    their riding/constituency (str),
    their province (str),
    the number of parliaments they've been in government (int), and which parliaments those were (list)
    the number of votes they've been in (int), and what votes those were (list of 3-tuples (Vote Object, how they voted 1/0, party they represented))
    the number of votes where they rebelled (int), and what votes those were (same type as above)
    """
    def __init__(self, name, constituency, province, country):
        """
        Specify a representative based on their:
            name: str
            constituency: str
            province: str
        """
        self.name = name
        self.constituency = constituency
        self.country = country

        self.province = province
        self.sessionsInGov = []
        self.numSessionsInGov = 0

        # self.votes is a list of (vote object, rep's vote (1 for yea, 0 for nay), party )
        self.votes = []
        self.numVotes = 0
        self.numRebellions = 0
        self.rebellionVotes = []

    def __str__(self):
        """ String representation of the representative. Represents their basic information, and what votes they rebelled in
        """
        outputString =  "name: %s, consituency: %s, province: %s, number of votes: %d, number of rebellions: %d" % (self.name, self.constituency, self.province, self.numVotes, self.numRebellions) + "\n"
        outputString += "Rebellion Votes:\n"
        for vote in sorted(self.rebellionVotes):
            outputString += "\t" + str(vote) + "\n"
        return outputString


    def voteString(self):
        """ String representation of every vote they've participated in
        """
        outputString = ""
        for v in self.votes:
            outputString += ("vote summary: %s, representative vote: %d\n" % v)
        return outputString

    def __eq__(self, otherRep):
        """ checks whether two representatives names are equal
        """
        return self.name == otherRep.name

    def isRebellion(self, voteTuple):
        """Takes in a vote 3-tuple from self.voteList and checks whether it was a rebellion
        """
        partyVotedYea = 0
        party = voteTuple[2]
        # did the party vote yes
        if voteTuple[0].voteResult[party][0] < voteTuple[0].voteResult[party][1]:
            partyVotedYea = 1
        # check if whether the party voted yea is equal to whether the representative voted yea
        if partyVotedYea == voteTuple[1]:
            return True
        else:
            return False

    def addVote(self, vote, yeaNay, party):
        """ Takes in a Vote object, whether the representative voted yea (1 or 0), and what party the representative was in at the time
            Adds it to the vote list, and if it was a rebellion vote it adds it to the the rebellion list
        """
        voteTuple = (vote, yeaNay, party)
        # append to the big vote list
        self.votes.append(voteTuple)
        self.numVotes += 1
        # if we haven't seen this session they had in government yet then add it
        if (not vote.voteID[0] in self.sessionsInGov):
            self.sessionsInGov.append(vote.voteID[0])
            self.numSessionsInGov += 1

        # if the vote is a rebellion vote
        if self.isRebellion(voteTuple):
            self.numRebellions += 1
            self.rebellionVotes.append(vote)
