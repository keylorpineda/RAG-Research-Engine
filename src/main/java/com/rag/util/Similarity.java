package com.rag.util;

public class Similarity {
    public static double cosine(double[] a, double[] b) {
        double dot=0, na=0, nb=0;
        int n = Math.min(a.length, b.length);
        for(int i=0;i<n;i++){ dot += a[i]*b[i]; na += a[i]*a[i]; nb += b[i]*b[i]; }
        if (na==0 || nb==0) return 0;
        return dot / (Math.sqrt(na)*Math.sqrt(nb));
    }
}
