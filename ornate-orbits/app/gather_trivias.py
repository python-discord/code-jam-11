# ref: https://github.com/blobfysh/opentdb-api/blob/master/index.js
import asyncio
import logging
import os
from typing import Final, TypedDict

import httpx

from .models.base import Base
from .models.trivia import Trivia, TriviaDifficulty
from .storage.database import trivia_database
from .storage.trivia import trivia_repo

OPENTDB_ENDPOINT: Final[str] = (
    "https://opentdb.com/api.php?amount=50&type=multiple&token={token}"
)
HTTP_200_OK: Final[int] = 200
logger = logging.getLogger("gather_trivia")


class OpentdbResult(TypedDict):
    """Model for result in opentdb."""

    type: str
    difficulty: str
    category: str
    question: str
    correct_answer: str
    incorrect_answers: list[str]


class OpentdbResponse(TypedDict):
    """Model for opentdb response."""

    response_code: int
    results: list[OpentdbResult]


def esc(text: str) -> str:
    """De-escape all escaped strings."""
    return (
        text.replace("&quot;", '"')
        .replace("&#039;", "'")
        .replace("&amp;", "&")
        .replace("&acute;", "`")
        .replace("&eacute;", "é")
        .replace("&oacute;", "ó")
        .replace("&pound;", "£")
        .replace("&aacute;", "á")
        .replace("&Aacute;", "Á")
        .replace("&ntilde;", "ñ")
        .replace("&rdquo;", '"')
        .replace("&ouml;", "ö")
    )


async def main() -> None:
    """The main gather function."""
    token: str = os.environ["TOKEN"]
    response_code: int = 0

    while response_code == 0:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=OPENTDB_ENDPOINT.format(token=token),
                    timeout=None,
                )
                if response.status_code != HTTP_200_OK:
                    logger.warning(
                        "abnormal status_code %d", response.status_code
                    )
                    continue
                response_dict: OpentdbResponse = response.json()
                response_code = response_dict.get("response_code", 0)
                for result in response_dict.get("results", []):
                    logger.info(result)
                    await trivia_repo.create(
                        Trivia(
                            difficulty=TriviaDifficulty(result["difficulty"]),
                            category=esc(result["category"]),
                            question=esc(result["question"]),
                            correct_answer=esc(result["correct_answer"]),
                            incorrect_answer_1=esc(
                                result["incorrect_answers"][0]
                            ),
                            incorrect_answer_2=esc(
                                result["incorrect_answers"][1]
                            ),
                            incorrect_answer_3=esc(
                                result["incorrect_answers"][2]
                            ),
                        )
                    )
        except Exception as exc:
            logger.exception(exc)
            continue
        finally:
            await asyncio.sleep(2)


async def init_db() -> None:
    """Initialize database."""
    async with trivia_database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_random() -> None:
    """Return a random trivia."""
    logger.info((await trivia_repo.get_random()).as_dict())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
    asyncio.run(main())
    asyncio.run(get_random())
