// Create vector index for semantic deduplication
CREATE VECTOR INDEX fractal_episodic_vector IF NOT EXISTS
FOR (n:Episodic)
ON (n.embedding)
OPTIONS {indexConfig: {
 `vector.dimensions`: 1536,
 `vector.similarity_function`: 'cosine'
}};
