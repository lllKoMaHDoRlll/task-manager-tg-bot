

class ConfigLoadFailed(Exception):
    """Config loading had failed """


class MakingRequestFailed(Exception):
    """making request had failed"""


class RepeatTimeFormattingFailed(Exception):
    """Error with formatting repeat time"""


class LoadFailed(Exception):
    """Error with loading data"""


class FolderNotFound(Exception):
    """Can't find folder"""
