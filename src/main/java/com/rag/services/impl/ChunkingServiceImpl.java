package com.rag.services.impl;

import com.rag.services.ChunkingService;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class ChunkingServiceImpl implements ChunkingService {

    @Override
    public List<String> chunk(String text, int size, int overlap) {
        List<String> out = new ArrayList<>();
        if (text == null || text.isBlank()) {
            return out;
        }

        String normalized = text.replace("\r", "");
        String[] paragraphs = normalized.split("\n\n+");
        StringBuilder current = new StringBuilder();

        for (String rawParagraph : paragraphs) {
            String paragraph = rawParagraph.trim();
            if (paragraph.isEmpty()) {
                continue;
            }

            for (String segment : splitParagraph(paragraph, size)) {
                if (segment.isEmpty()) {
                    continue;
                }
                current = appendSegment(out, current, segment, size, overlap);
            }
        }

        if (current.length() > 0) {
            out.add(current.toString());
        }

        return out;
    }

    @Override
    public int approxTokens(String text) {
        return Math.max(1, text.length() / 4);
    }

    private List<String> splitParagraph(String paragraph, int size) {
        List<String> segments = new ArrayList<>();
        if (paragraph.length() <= size) {
            segments.add(paragraph);
            return segments;
        }

        String[] words = paragraph.split("\\s+");
        StringBuilder current = new StringBuilder();
        for (String word : words) {
            if (word.isBlank()) {
                continue;
            }

            if (word.length() > size) {
                if (current.length() > 0) {
                    segments.add(current.toString());
                    current.setLength(0);
                }
                int start = 0;
                while (start < word.length()) {
                    int end = Math.min(start + size, word.length());
                    segments.add(word.substring(start, end));
                    start = end;
                }
                continue;
            }

            if (current.length() == 0) {
                current.append(word);
                continue;
            }

            int candidateLength = current.length() + 1 + word.length();
            if (candidateLength <= size) {
                current.append(' ').append(word);
            } else {
                segments.add(current.toString());
                current.setLength(0);
                current.append(word);
            }
        }

        if (current.length() > 0) {
            segments.add(current.toString());
        }

        return segments;
    }

    private StringBuilder appendSegment(List<String> out, StringBuilder current, String segment, int size, int overlap) {
        if (segment.length() > size) {
            int start = 0;
            while (start < segment.length()) {
                int end = Math.min(start + size, segment.length());
                String piece = segment.substring(start, end);
                current = appendSegment(out, current, piece, size, overlap);
                start = end;
            }
            return current;
        }

        if (current.length() == 0) {
            current.append(segment);
            return current;
        }

        int separatorLength = 2; // "\n\n"
        if (current.length() + separatorLength + segment.length() <= size) {
            current.append("\n\n").append(segment);
            return current;
        }

        out.add(current.toString());
        StringBuilder overlapTail = buildOverlapTail(current, overlap);
        overlapTail = ensureTailFits(overlapTail, segment.length(), size, separatorLength);

        if (overlapTail.length() > 0 && overlapTail.length() + separatorLength + segment.length() <= size) {
            overlapTail.append("\n\n").append(segment);
            return overlapTail;
        }

        return new StringBuilder(segment);
    }

    private StringBuilder buildOverlapTail(StringBuilder current, int overlap) {
        if (overlap <= 0 || current.length() == 0) {
            return new StringBuilder();
        }
        int effectiveOverlap = Math.min(overlap, current.length());
        String tail = current.substring(current.length() - effectiveOverlap);
        return new StringBuilder(tail);
    }

    private StringBuilder ensureTailFits(StringBuilder tail, int segmentLength, int size, int separatorLength) {
        if (tail.length() == 0) {
            return tail;
        }

        int maxTailLength = size - segmentLength - separatorLength;
        if (maxTailLength <= 0) {
            return new StringBuilder();
        }

        if (tail.length() > maxTailLength) {
            return new StringBuilder(tail.substring(tail.length() - maxTailLength));
        }

        return tail;
    }
}
