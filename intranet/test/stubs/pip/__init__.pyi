# Stubs for pip (Python 3.5)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Optional

cmdoptions = ...  # type: Any
logger = ...  # type: Any

def autocomplete(): ...
def create_main_parser(): ...
def parseopts(args): ...
def check_isolated(args): ...
def main(args: Optional[Any] = ...): ...

class FrozenRequirement:
    name = ...  # type: Any
    req = ...  # type: Any
    editable = ...  # type: Any
    comments = ...  # type: Any
    def __init__(self, name, req, editable, comments: Any = ...) -> None: ...
    @classmethod
    def from_dist(cls, dist, dependency_links): ...
    @staticmethod
    def egg_name(dist): ...
