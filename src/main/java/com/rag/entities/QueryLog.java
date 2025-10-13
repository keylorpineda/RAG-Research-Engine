package com.rag.entities;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;

@Entity
@Table(name = "queries")
public class QueryLog {

  @Id
  @GeneratedValue(strategy = GenerationType.IDENTITY)
  private Integer id;

  @Lob
  @Column(columnDefinition = "TEXT")
  private String queryText;

  private Instant ts = Instant.now();

  @Column(name = "result_refs", columnDefinition = "jsonb")
  @JdbcTypeCode(SqlTypes.JSON)
  private String resultRefs;

  public QueryLog() {
  }

  public Integer getId() {
    return id;
  }

  public void setId(Integer id) {
    this.id = id;
  }

  public String getQueryText() {
    return queryText;
  }

  public void setQueryText(String queryText) {
    this.queryText = queryText;
  }

  public Instant getTs() {
    return ts;
  }

  public void setTs(Instant ts) {
    this.ts = ts;
  }

  public String getResultRefs() {
    return resultRefs;
  }

  public void setResultRefs(String resultRefs) {
    this.resultRefs = resultRefs;
  }
}
