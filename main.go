package main

import (
	"fmt"
	"strings"

	"github.com/pingcap/parser"
	"github.com/pingcap/parser/ast"
	"github.com/pingcap/parser/format"
	_ "github.com/pingcap/parser/test_driver"
)

func main() {
	sql := `with w1 as ( Select *, Dense_Rank() over (partition by DepartmentId order by Salary desc ) as "Rank" from Employee ) Select Department.Name as "Department" , w1.Name as "Employee", w1.Salary as "Salary" from w1 join Department on Department.Id = w1.DepartmentId where w1.Rank = 1 or w1.Rank =2 or w1.Rank = 3 order by Department.Name , w1.Salary desc`
	// sql := "SELECT a.a1 FROM a LIMIT 1, 2"
	translated := translate(sql)
	fmt.Println(translated)
}

func translate(sql string) string {
	astNode, err := parse(sql)
	if err != nil {
		fmt.Printf("parse error: %v\n", err.Error())
		return "ERROR"
	}
	var stringBuilder strings.Builder
	ctx := format.NewRestoreCtx(
		format.RestoreStringSingleQuotes|format.RestoreNameDoubleQuotes|format.RestoreKeyWordUppercase,
		&stringBuilder,
	)
	(*astNode).Restore(ctx)
	return stringBuilder.String()
}

func parse(sql string) (*ast.StmtNode, error) {
	p := parser.New()

	stmtNodes, _, err := p.Parse(sql, "", "")
	if err != nil {
		return nil, err
	}

	return &stmtNodes[0], nil
}
