/** Shapes returned by the FastAPI backend (app/schemas.py). JSON fields are camelCase. */

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed';

export interface DocumentOut {
  id: number;
  filename: string;
  mime: string | null;
  size: number | null;
  status: DocumentStatus;
  uploadTs: string | null;
}

export interface ChunkOut {
  id: number;
  chunkIndex: number;
  tokenCount: number;
  text: string;
}

export interface DocumentDetailOut extends DocumentOut {
  chunks: ChunkOut[];
}

export interface UploadOut {
  ids: number[];
  message: string;
}

export interface MessageOut {
  message: string;
}

export interface HealthOut {
  status: string;
  embeddingModel: string;
  minSimilarity: number;
  jobs: Record<string, number>;
}

export type RetrievalMode = 'dense' | 'lexical' | 'hybrid';

export interface QueryRequest {
  q: string;
  k?: number;
  mode?: RetrievalMode;
  maxTokens?: number;
  minSimilarity?: number | null;
}

export interface Reference {
  n: number;
  docId: number;
  filename: string;
  chunkIndex: number;
  score: number;
  denseScore: number | null;
  lexicalScore: number | null;
  rerankScore: number | null;
  cited: boolean;
  text: string;
}

export type AbstainReason = 'insufficient_evidence' | 'no_passages' | 'model_declined';

export interface QueryResponse {
  answered: boolean;
  answer: string | null;
  reason: AbstainReason | null;
  refs: Reference[];
  invalidCitations: number[];
  evidence: { bestSimilarity: number | null; minSimilarity: number };
}
