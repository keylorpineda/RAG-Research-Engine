import os

# Tests run with the local embedding model settings (384 dims) unless told otherwise. This must
# happen before `app` is imported: the vector column size is read from the settings.
os.environ.setdefault("EMBEDDING_PROVIDER", "local")
