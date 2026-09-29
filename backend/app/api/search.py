from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import SearchQueryError
from app.schemas import SearchResponse
from app.search.parser import parse_search_query
from app.services.search import execute_search


router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


APPLICATION_TIMEZONE = ZoneInfo("Asia/Kolkata")


@router.get(
    "",
    response_model=SearchResponse,
)
def search_candidates(
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=300,
            description="Natural-language candidate search",
        ),
    ],
    database: Annotated[Session, Depends(get_db)],
) -> SearchResponse:
    now = datetime.now(APPLICATION_TIMEZONE)

    try:
        plan, interpretation = parse_search_query(
            raw_query=q,
            now=now,
        )
    except SearchQueryError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": error.code,
                "message": error.message,
                "fragment": error.fragment,
                "hints": error.hints,
            },
        ) from error

    results = execute_search(
        database=database,
        plan=plan,
        now=now,
    )

    return SearchResponse(
        query=q,
        interpretation=interpretation,
        plan=plan,
        count=len(results),
        results=results,
    )