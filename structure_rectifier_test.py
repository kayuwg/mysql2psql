from structure_rectifier import rectify

def test_bad_having():
    sql = "SELECT a.a1 FROM a WHERE a.a2 < 1 HAVING a.a1 > 1"
    exptected = "SELECT a.a1 FROM a WHERE (a.a2 < 1) AND (a.a1 > 1)"
    assert rectify(sql) == exptected
    
def test_same_level_alias():
    sql = "SELECT a.a1 c1, COUNT(a.a2) c2 FROM a GROUP BY c1 HAVING c2 > 1"
    exptected = "SELECT a.a1 AS c1, count(a.a2) AS c2 FROM a GROUP BY a.a1 HAVING count(a.a2) > 1"
    assert rectify(sql) == exptected
    
def test_necessary_group_by():
    sql = "SELECT ABS(a.a1 + COUNT(a.a2)) c1, a.a1 - a.a3 c2 FROM a GROUP BY a.a1 HAVING c2 > 1"
    exptected = "SELECT abs(a.a1 + count(a.a2)) AS c1, a.a1 - a.a3 AS c2 FROM a GROUP BY a.a1, a.a3 HAVING ((a.a1 - a.a3)) > 1"
    assert rectify(sql) == exptected