import csv
import sys
import pglast
from pglast.visitors import Visitor
from top_level_anlayzer import TopLevelAnalyzer, add_predicates_to_where
from pglast.stream import RawStream
    
def fix_having_without_groupby(ast_node: pglast.ast.Node):
    """fix having without group by"""
    class BadHavingVisitor(Visitor):
        def visit_SelectStmt(self, _, node):
            if node.havingClause is not None and node.groupClause is None:
                add_predicates_to_where(node, [node.havingClause])
                node.havingClause = None
    bad_having_visitor = BadHavingVisitor()
    bad_having_visitor(ast_node)
    
def fix_same_level_alias_usage(ast_node: pglast.ast.Node):
    """replace each usage of select column alias at the same level to the actual content"""
    class SameLevelAliasFixer(Visitor):
        def visit_SelectStmt(self, _, node):
            top_level = TopLevelAnalyzer(pglast.node.Node(node))
            top_level()
            top_level.replace_column_alias_usage()
    same_level_alias_fixer = SameLevelAliasFixer()
    same_level_alias_fixer(ast_node)
    
def add_necessary_group_by_columns(ast_node: pglast.ast.Node):
    """if a column appears in SELECT but is not in an aggregate function, then it must also
        be a group-by column
        assume target_columns and group_columns have been calculated
    """
    class AddGroupByColumnsVisitor(Visitor):
        def visit_SelectStmt(self, _, node):
            top_level = TopLevelAnalyzer(pglast.node.Node(node))
            top_level()
            top_level.add_necessary_group_by_columns()
    visitor = AddGroupByColumnsVisitor()
    visitor(ast_node)
    
def rectify(sql: str) -> str :
    ast_node = pglast.parse_sql(sql)
    fix_having_without_groupby(ast_node)
    fix_same_level_alias_usage(ast_node)
    add_necessary_group_by_columns(ast_node)
    return RawStream()(ast_node)
    

def test_custom():
    sql = "SELECT ABS(a.a1 + COUNT(a.a2)) c1, a.a1 - a.a3 c2 FROM a GROUP BY c1 HAVING c2 > 1"
    print(rectify(sql))
          
def rectify_file(filename):
    with open(filename) as file:
        reader = csv.reader(file, delimiter=",", quotechar='"')
        records = [row for row in reader]
    for i, record in enumerate(records):
        print(i, record)
        if i == 0:
            continue 
        if record[1][0:5] == "ERROR":
            continue
        try:
            record[1] = rectify(record[1])
        except Exception as error:
            return f"ERROR: {error}"
            
        
    writer = csv.writer(sys.stdout)
    writer.writerows(records)

    
if __name__ == "__main__": 
    if len(sys.argv) > 1:
        rectify_file(sys.argv[0])