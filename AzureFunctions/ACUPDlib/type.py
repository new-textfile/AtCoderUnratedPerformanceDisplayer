from typing import List, Dict, TypedDict

class ContestInfo(TypedDict):
    date: str
    upper_rating_limit: int
    lower_rating_limit: int

class CalcTempData(TypedDict):
    contest_name : str
    is_ratedcontest: bool
    pred_default_aperf: int
    user_latest_aperf: Dict[str, float]
    aperflist: List[float]
    ratedplace: int
    user_innerperf: Dict[str, float]
    user_perf: Dict[str, float]
    finished: bool
    is_matched: bool

class UserResult(TypedDict):
    IsRated: bool
    Place: int
    OldRating: int
    NewRating: int
    Performance: int
    ContestName: str
    ContestNameEn: str
    ContestScreenName : str
    EndTime: str
    ContestType: int
    UserName: str
    UserScreenName: str
    Country: str
    Affiliation: str
    Rating: int
    Competitions: int
    AtCoderRank: int

class InnerPerfInfo(TypedDict):
    InnerPerf: float
    IsRated: bool

class FetchedContests(TypedDict):
    contests: List[str]