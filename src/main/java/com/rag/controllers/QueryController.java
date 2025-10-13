package com.rag.controllers;

import com.rag.dto.QueryRequestDto;
import com.rag.dto.QueryResponseDto;
import com.rag.services.QueryService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class QueryController {

    private final QueryService service;

    public QueryController(QueryService q) {
        this.service = q;
    }

    @PostMapping("/query")
    public ResponseEntity<QueryResponseDto> ask(@Valid @RequestBody QueryRequestDto body) throws Exception {
        return ResponseEntity.ok(service.ask(body.q(), body.k()));
    }
}
