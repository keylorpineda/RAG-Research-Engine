package com.rag.entities;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "embeddings")
public class Embedding {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Integer id;

  @Column(name = "chunk_id")
  private Integer chunkId;

  @Column(columnDefinition = "jsonb")
  @JdbcTypeCode(SqlTypes.JSON)
  private double[] vector;

  public Embedding() {
  }

  public Integer getId() {
    return id;
  }

  public void setId(Integer id) {
    this.id = id;
  }

  public Integer getChunkId() {
    return chunkId;
  }

  public void setChunkId(Integer chunkId) {
    this.chunkId = chunkId;
  }

  public double[] getVector() {
    return vector;
  }

  public void setVector(double[] vector) {
    this.vector = vector;
  }
}
