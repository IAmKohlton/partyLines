from functools import total_ordering
@total_ordering
class Vote(object):
    """
    A single vote in parliament.
    Contains self.voteID which is a tuple that identifies parliament number, session number, and vote number.
        This tuple has total ordering meaning that it can be compared and sorted easily.
    Contains self.voteResult which is a dictionary that stores the summary result of the vote.
        This dictionary has keys of the party names, and has values of a two entry list where
        the first entry is how many representatives from that party voted yes,
        and the second entry is how many representatives voted no.
    """
    def __init__(self,voteID, result):
        """
        Specify a voteID, and result for a vote where:
            voteID = (parliament #, session #, vote #)
            voteResult = {party: (num yes, num no), ...}
        """
        self.voteID = voteID
        self.voteResult = result

    def __str__(self):
        """ string representation of the vote. Only represents the vote identifier, not the contents
        """
        return "Parliament: %d, Session: %d, Vote: %d" % self.voteID

    def __lt__(self, other):
        """ takes in another Vote object "other" and says whether this is strictly less than "other". This is based on the vote identifier
        """
        return self.voteID < other.voteID

    def __eq__(self, other):
        """ takes in another Vote object "other" and says whether this is the same as "other". This is based on the vote identifier
        """
        return self.voteID == other.voteID
