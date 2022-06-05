id,original query
1,"SELECT a.a1 FROM a WHERE a.a2 < 1 HAVING a.a1 > 1"
2,"SELECT a.a1 c1, COUNT(a.a2) c2 FROM a GROUP BY c1 HAVING c2 > 1"
3,"SELECT ABS(a.a1 + COUNT(a.a2)) c1, a.a1 - a.a3 c2 FROM a GROUP BY a.a1 HAVING c2 > 1"