import secrets
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import TYPE_CHECKING, Final

import nltk

if TYPE_CHECKING:
    from nltk.corpus.reader.wordnet import Lemma, Synset


class Difficulty(StrEnum):
    """Enum for game difficulties."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


@dataclass
class Word:
    """The dataclass for a Word."""

    word: str
    definition: str
    synonyms: set[str]
    usages: list[str]


class WordGenerator:
    """The class for generating a random word between 5 to 10 chars."""

    CORPORA_WORDNET: Final[str] = "corpora/wordnet"
    WORDNET: Final[str] = "wordnet"

    WORD_LENGTH_MIN: Final[int] = 5
    WORD_LENGTH_MAX: Final[int] = 15

    WORD_AMOUNT_HARD: Final[int] = 1
    WORD_AMOUNT_EASY: Final[int] = 5

    def __init__(self) -> None:
        self.download_corpus()
        self.synsets: list[Synset] = []
        self.mp_len_words: dict[int, dict[Difficulty, list[str]]] = {
            val: {diff: [] for diff in Difficulty}
            for val in range(self.WORD_LENGTH_MIN, self.WORD_LENGTH_MAX + 1)
        }
        self.mp_len_synsets: dict[int, dict[Difficulty, list[Synset]]] = {
            val: {diff: [] for diff in Difficulty}
            for val in range(self.WORD_LENGTH_MIN, self.WORD_LENGTH_MAX + 1)
        }
        self.separate_lengths()

    def separate_lengths(self) -> None:
        """Populate the wordnet data for each length."""
        from nltk.corpus import wordnet

        temp_words: dict[int, dict[str, int]] = {}
        temp_synsets: dict[int, list[Synset]] = {}

        for synset in wordnet.all_synsets():
            word = synset.name().split(".", 1)[0]
            if not self.is_qualified(word):
                continue
            word_length = len(word)

            temp_words.setdefault(word_length, {})
            if not temp_words.get(word_length, {}).get(word):
                self.synsets.append(synset)
                temp_words[word_length][word] = 1
                temp_synsets.setdefault(word_length, [])
                temp_synsets[word_length].append(synset)
            else:
                temp_words[word_length][word] += 1

        for i in range(self.WORD_LENGTH_MIN, self.WORD_LENGTH_MAX + 1):
            for (word, val), synset in zip(
                temp_words[i].items(), temp_synsets[i], strict=False
            ):
                if val == self.WORD_AMOUNT_HARD:
                    self.mp_len_words[i][Difficulty.HARD].append(word)
                    self.mp_len_synsets[i][Difficulty.HARD].append(synset)
                elif self.WORD_AMOUNT_HARD < val < self.WORD_AMOUNT_EASY:
                    self.mp_len_words[i][Difficulty.MEDIUM].append(word)
                    self.mp_len_synsets[i][Difficulty.MEDIUM].append(synset)
                else:
                    self.mp_len_words[i][Difficulty.EASY].append(word)
                    self.mp_len_synsets[i][Difficulty.EASY].append(synset)

    @classmethod
    def boot(cls) -> None:
        """Try accessing wordnet data to trigger data validation."""
        from nltk.corpus import wordnet

        list(wordnet.all_synsets())

    @classmethod
    def download_corpus(cls) -> None:
        """Ensure the wordnet corpus is downloaded."""
        try:
            nltk.data.find(cls.CORPORA_WORDNET)
        except LookupError:
            nltk.download(cls.WORDNET)

    def _random_word_in_synset(self) -> tuple[str, "Synset"]:
        synset: Synset = secrets.choice(self.synsets)
        lemma: Lemma = secrets.choice(synset.lemmas())
        return lemma.name(), synset

    def is_qualified(self, word: str) -> bool:
        """Word qualification for adding into bank."""
        return (
            "-" not in word
            and "_" not in word
            and self.WORD_LENGTH_MIN <= len(word) <= self.WORD_LENGTH_MAX
        )

    def is_valid(self, word: str) -> bool:
        """Check if the word exists in the bank."""
        if len(word) not in self.mp_len_words:
            return False
        return (
            word
            in self.mp_len_words[len(word)][Difficulty.EASY]
            + self.mp_len_words[len(word)][Difficulty.MEDIUM]
            + self.mp_len_words[len(word)][Difficulty.HARD]
        )

    def random(self, length: int, difficulty: Difficulty) -> Word:
        """Randomizes a word from the synset."""
        dataset: list[Synset] = self.mp_len_synsets.get(length, {}).get(
            difficulty, []
        )

        assert len(dataset) > 0, "the word bank is empty"

        synset = secrets.choice(dataset)
        return Word(
            word=synset.name().split(".", 1)[0],
            definition=synset.definition(),
            synonyms={lm.name() for lm in synset.lemmas()},
            usages=synset.examples(),
        )

    def get_word(self, word: str) -> Word:
        """Get Word dataclass with the given word."""
        from nltk.corpus import wordnet

        synset: Synset = wordnet.synsets(word)[0]

        return Word(
            word=synset.name().split(".", 1)[0],
            definition=synset.definition(),
            synonyms={lm.name() for lm in synset.lemmas()},
            usages=synset.examples(),
        )

    def __str__(self) -> str:
        bank_stat = " | ".join(
            [
                f"Len {length}: {len(words[diff])}"
                for diff in Difficulty
                for length, words in sorted(self.mp_len_words.items())
            ]
        )
        return (
            "<WordGenerator"
            f"(Easy to Hard)"
            f" {bank_stat}"
            f" | MinLength = {self.WORD_LENGTH_MIN}"
            f" | MaxLength = {self.WORD_LENGTH_MAX}"
            ">"
        )


@lru_cache
def get_wordgen() -> WordGenerator:
    """Ensure only 1 instance of wordgen is used."""
    return WordGenerator()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    wordgen = WordGenerator()
    logger.info(wordgen)
