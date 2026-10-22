import { AbstainReason, QueryResponse, Reference } from '../../core/api/api.types';

export function ref(n: number, cited = true): Reference {
  return {
    n,
    docId: n,
    filename: `pep-${n}.txt`,
    chunkIndex: n * 2,
    section: n === 1 ? 'Rationale' : null,
    score: 0.03,
    denseScore: 0.7,
    lexicalScore: 0.05,
    rerankScore: null,
    cited,
    text: `Passage ${n} text.`,
  };
}

export function answered(answer = 'Declared with `async def` [1] and awaited [2].'): QueryResponse {
  return {
    answered: true,
    answer,
    reason: null,
    refs: [ref(1), ref(2), ref(3, false)],
    invalidCitations: [],
    evidence: { bestSimilarity: 0.72, minSimilarity: 0.55 },
  };
}

export function abstained(reason: AbstainReason, refs: Reference[] = []): QueryResponse {
  return {
    answered: false,
    answer: null,
    reason,
    refs,
    invalidCitations: [],
    evidence: {
      bestSimilarity: reason === 'no_passages' ? null : 0.31,
      minSimilarity: 0.55,
    },
  };
}
