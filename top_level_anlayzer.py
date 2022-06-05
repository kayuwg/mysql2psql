import pglast
from pglast import parser, parse_sql, Missing
from pglast.visitors import Visitor
from typing import Dict, Set, List
from pglast.enums.primnodes import BoolExprType
from pglast.stream import RawStream

AGGREGATE_NAMES = ["count", "sum", "min", "max", "avg"]

class Column:
    """
    Attributes:
        name: column name
        val: expression for the column
        exact_inner: (table, name) if the column is exactly table.name where table is in a smaller scope; otherwise None
        dependsOn: list of columns this column depends on
        text_form: plain text representation used to check if two columns are obviously equal
    """
    def __repr__(self):
        string = self.name
        if self.exact_inner is not None:
            string += f"({self.exact_inner[0]}.{self.exact_inner[1]})" 
        return string
    
    @classmethod
    def create(cls, table_name: str, column: str):
        """Create a Column from table.column"""
        self = cls()
        self.name = column
        self.val = pglast.ast.ColumnRef(
            [pglast.ast.String(table_name), pglast.ast.String(column)]
        )
        self.exact_inner = (table_name, column)
        self.dependsOn = [self.exact_inner]
        self.text_form = RawStream()(self.val)
        return self
    
    @classmethod
    def from_ast_node(cls, ast_node: pglast.ast.Node, name: str):
        """Takes in a ResTarget"""
        self = cls()
        self.name = name
        self.val = ast_node
        self.exact_inner = None
        if isinstance(ast_node, pglast.ast.ColumnRef):
            self.exact_inner = cls.columnRef_to_exact_inner(ast_node)
        # columns it depends on
        self.dependsOn = find_depending_columns(pglast.node.Node(ast_node))
        self.text_form = RawStream()(self.val)
        return self
    
    @staticmethod
    def name_from_resTarget(target: pglast.node.Node):
        """Find name of column from ResTarget whose val is ColumnRef"""
        if target.name is Missing:
            if target.val.node_tag == "ColumnRef":
                return target.val.fields[-1].val.value
            else:
                raise Exception(f"Please add alias to column {target.val.ast_node}")
        else:
            return target.name.value
        
    @staticmethod
    def name_to_resTarget(table_name: str, column_name: str):
        fields = (pglast.ast.String(value=table_name), pglast.ast.String(value=column_name))
        columnRef = pglast.ast.ColumnRef(fields=fields)
        return pglast.ast.ResTarget(val=columnRef, name=column_name)
         
    
    @staticmethod
    def columnRef_to_exact_inner(columnRef: pglast.ast.ColumnRef):
        """Convert ColumnRef to (table, column)"""
        fields = columnRef.fields
        if len(fields) == 1:
            return fields[0].val
        else:
            return (fields[0].val, fields[1].val)
        
        
    @staticmethod
    def merge(lhs, rhs):
        result = Column()
        result.name = lhs.name
        left_list = lhs.val if isinstance(lhs.val, list) else [lhs.val]
        right_list = rhs.val if isinstance(rhs.val, list) else [rhs.val]
        result.val = left_list + right_list
        result.exact_inner = lhs.exact_inner if lhs.exact_inner == rhs.exact_inner else None
        result.dependsOn = lhs.dependsOn + rhs.dependsOn
        return result
    
class TopLevelAnalyzer:
    def __init__(self, node: pglast.node.Node):
        """
        Attributes:
        node (pglast.node.Node): current node
        tables (list[str]): list of top-level table names
        target_columns: dict: column_name -> Column object for those declared in SELECT
        center_exact_inner (list): for each group-by column, if column is t.c for some inner table t, then (t, c);
            else if column is a column in SELECT, then alias name; else None
        """
        self.node: pglast.node.Node = node
        self.tables: list[str] = None
        self.target_columns: Dict[str, Column] = None
        self.group_columns: list[Column] = None
        
    def __call__(self):
        self.find_top_level_tables()
        self.find_target_columns()
        self.find_group_columns()
        
                
    def set_top_level_tables(self, top_level_tables):
        self.tables = top_level_tables
        
    def set_target_columns(self, target_columns):
        self.target_columns = target_columns
    
    def find_top_level_tables(self):
        """fill_in top_level_tables"""
        class TopLevelTableVisitor(Visitor):
            def __init__(self):
                self.top_level_tables = []
            def visit_RangeVar(self, _, node):
                name = node.alias.aliasname if node.alias else node.relname
                self.top_level_tables.append(name)
            def visit_RangeSubselect(self, _, node):
                self.top_level_tables.append(node.alias.aliasname)
                return pglast.visitors.Skip()
            # do not consider SubLink yet
            def visit_SubLink(self):
                return pglast.visitors.Skip()
        visitor = TopLevelTableVisitor()
        visitor(self.node.ast_node)
        self.tables = visitor.top_level_tables
        return self.tables
    
    def find_target_columns(self):
        """fill in target_columns
           assume top_level_tables is filled 
        """
        result = {}
        # Assume after FullAnalyzer, there's no SELECT *
        for target in self.node.targetList:
            column_name = Column.name_from_resTarget(target)
            result[column_name] = Column.from_ast_node(target.val.ast_node, column_name)
        self.target_columns = result
        return self.target_columns
    
    def find_group_columns(self):
        """fill in center_exact_inner, for select statement with group-by clause
           assume target_columns is filled 
        """
        self.group_columns = []
        if self.node.groupClause is Missing:
            return
        group_by_columns = self.node.ast_node.groupClause
        # assume each group by column is either t.c or the name of a column in select clause
        for ast_node in group_by_columns:
            group_column = Column.from_ast_node(ast_node, "")
            # check content to see this group-by column is a select column
            if group_column.exact_inner is None:
                for target_name, target_column in self.target_columns.items():
                    if group_column.text_form == target_column.text_form:
                        group_column.exact_inner = target_name
                        break
            # if this group-by column is a select column, check if the select column has exact_inner
            if isinstance(group_column.exact_inner, str):
                if group_column.exact_inner not in self.target_columns:
                    raise Exception(f"Can't recognize column {group_column.exact_inner}")
                target_exact_inner = self.target_columns[group_column.exact_inner].exact_inner
                if target_exact_inner is not None:
                    group_column.exact_inner = target_exact_inner
            self.group_columns.append(group_column)
        return self.group_columns
    
    def replace_column_alias_usage(self):
        """replace each reference to a column alias (defined in SELECT clause) in an ON/WHERE clause with actual content
           assume target_columns is filled
        """
        class ReplaceVisitor(Visitor):
            def __init__(self, column_name: str, ast_expr: pglast.ast.A_Expr):
                self.column_name = column_name
                self.ast_expr = ast_expr
            def visit_ColumnRef(self, ancestor, node):
                if len(node.fields) == 1 and node.fields[0].val == self.column_name:
                    return self.ast_expr
                return None
            def visit_RangeSubselect(self, _, node):
                return pglast.visitors.Skip()
            # do not consider sublink yet
            def visit_SubLink(self, _, node):
                return pglast.visitors.Skip() 
        for column_name, column_obj in self.target_columns.items():
            replace_visitor = ReplaceVisitor(column_name, column_obj.val)
            replace_visitor(self.node.ast_node)
            
    def add_necessary_group_by_columns(self):
        """if a column appears in SELECT but is not in an aggregate function, then it must also
           be a group-by column
           assume target_columns and group_columns have been calculated
        """
        class AllColumnsValidVisitor(Visitor):
            def __init__(self, group_columns):
                self.group_columns = group_columns
                self.invalid_columns = []
            def visit_ColumnRef(self, ancestors, node):
                # if any ancestor is aggregate function, we are safe
                num_ancestors = len(list(ancestors))
                for i in range(1, num_ancestors - 1):
                    ancestor = ancestors[i]
                    if isinstance(ancestor, pglast.ast.FuncCall) and ancestor.funcname[0].val in AGGREGATE_NAMES:
                        return None
                # if this column is a group-by column, we are safe
                column = Column.from_ast_node(node, "")
                if any(column.text_form == group_column.text_form for group_column in self.group_columns):
                    return None
                self.invalid_columns.append(column)
            # do not go into sublink
            def visit_SubLink(self, _, node):
                return pglast.visitors.Skip()
            
        if self.node.groupClause is Missing:
            return 
        new_group_columns = [*self.group_columns]
        for target_column in self.target_columns.values():
            all_columns_valid_visitor = AllColumnsValidVisitor(self.group_columns)
            all_columns_valid_visitor(target_column.val)
            new_group_columns.extend(all_columns_valid_visitor.invalid_columns)
        seen = set()
        new_group_column_nodes = []
        for column in new_group_columns:
            if column.text_form not in seen:
                seen.add(column.text_form)
                new_group_column_nodes.append(column.val)
        self.node.ast_node.groupClause = new_group_column_nodes
        
    
def ast_BoolExpr(boolop: BoolExprType, predicates: List):
    if len(predicates) == 0:
        return None
    elif len(predicates) == 1 and boolop is not BoolExprType.NOT_EXPR:
        return predicates[0]
    else:
        return pglast.ast.BoolExpr(boolop, predicates)    

def add_predicates_to_where(root: pglast.ast.SelectStmt, predicates: List[pglast.ast.Node]):
    predicates_node = ast_BoolExpr(BoolExprType.AND_EXPR, predicates)
    if predicates_node is None:
        return
    if root.whereClause is None:
        root.whereClause = predicates_node
    else:
        conjunction = pglast.ast.BoolExpr(BoolExprType.AND_EXPR, [root.whereClause, predicates_node])
        root.whereClause = conjunction
    
def find_depending_columns(node: pglast.node.Node):
    """Find all (table, column) in a node, not considering sublink"""
    class FindColumnVisitor(Visitor):
        def __init__(self):
            self.dependsOn = []
        def visit_ColumnRef(self, _, node):
            self.dependsOn.append(Column.columnRef_to_exact_inner(node))
        def visit_SubLink(self, _, node):
            return pglast.visitors.Skip()
    find_column_visitor = FindColumnVisitor()
    find_column_visitor(node.ast_node)
    return find_column_visitor.dependsOn
    
if __name__ == "__main__":           
    schema_file = "phase1schema.json"
    # sql = """SELECT a.a1 a1, a.a1 + b.b1 AS sum FROM (a cross join b) left join (SELECT c.c1 FROM c WHERE c.c1 = sum) c0 on abs(sum + c0.c1) where sum < 10 AND (sum < 9 OR sum < 8) AND sum + c0.c1 = 1"""
    sql = """SELECT
        COUNT(DISTINCT A.id, B.id) ab
    FROM I
        LEFT JOIN A
        ON I.x1 < A.a1
        INNER JOIN (
        B
        LEFT JOIN C
        ON B.x2 < C.c1
        CROSS JOIN E)
        ON B.b1 > A.a2
        LEFT JOIN D
        ON D.d1 = C.c2

    GROUP BY I.x"""
    #         WHERE B.b1 >= A.a2 AND (A.a1 < A.a1 OR I.x2 < C.c1) OR NOT(D.d1 = C.c2 AND 1 AND B.id < 1 AND E.id = D.id)
    root = pglast.node.Node(parse_sql(sql))
    node = root[0].stmt
    analyzer = TopLevelAnalyzer(node)
    analyzer()
    analyzer.replace_column_alias_usage()

        