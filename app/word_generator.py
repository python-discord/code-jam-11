import secrets
from dataclasses import dataclass
from typing import Final

import nltk
from nltk.corpus import wordnet
from nltk.corpus.reader.wordnet import Lemma, Synset


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
    WORD_LENGTH_MAX: Final[int] = 10

    def __init__(self) -> None:
        self.synsets: list[Synset] = list(wordnet.all_synsets())

    @classmethod
    def download_corpus(cls) -> None:
        """Ensure the wordnet corpus is downloaded."""
        try:
            nltk.data.find(cls.CORPORA_WORDNET)
        except LookupError:
            nltk.download(cls.WORDNET)

    def _random_word_in_synset(self) -> tuple[str, Synset]:
        synset: Synset = secrets.choice(self.synsets)
        lemma: Lemma = secrets.choice(synset.lemmas())
        return lemma.name(), synset

    def is_valid(self, word: str) -> bool:
        """Validate the word."""
        return (
            "-" not in word
            and "_" not in word
            and self.WORD_LENGTH_MIN <= len(word) <= self.WORD_LENGTH_MAX
        )

    def random(self) -> Word:
        """Randomizes a word from the synset."""
        word, synset = self._random_word_in_synset()
        while not self.is_valid(word):
            word, synset = self._random_word_in_synset()
        return Word(
            word=word,
            definition=synset.definition(),
            synonyms={lm.name() for lm in synset.lemmas()},
            usages=synset.examples(),
        )
