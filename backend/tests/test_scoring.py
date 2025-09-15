import sys
from unittest.mock import MagicMock

import numpy as np

sys.modules.setdefault("sentence_transformers", MagicMock(SentenceTransformer=MagicMock()))

from backend.search import select_and_ingest as sai


class FakeModel:
    def encode(self, texts):
        vecs = []
        for t in texts:
            v = np.zeros(3)
            if 'cat' in t: v[0] = 1
            if 'mat' in t: v[1] = 1
            if 'economy' in t: v[2] = 1
            if not v.any():
                v[2] = 1
            vecs.append(v)
        return vecs


def test_relevance_thresholds(monkeypatch):
    monkeypatch.setattr(sai, "_get_model", lambda: FakeModel())
    sim = sai.compute_relevance("cat sat on mat", "a cat sits on the mat")
    dis = sai.compute_relevance("cat sat on mat", "economic policies fluctuate")
    assert sim >= 0.7
    assert dis < 0.7
