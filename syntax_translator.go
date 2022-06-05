package main

import (
	"fmt"
	"strings"

	"github.com/pingcap/parser"
	"github.com/pingcap/parser/format"
	_ "github.com/pingcap/parser/test_driver"
)

func main() {
	// sql := `with w1 as ( Select *, Dense_Rank() over (partition by DepartmentId order by Salary desc ) as "Rank" from Employee ) Select Department.Name as "Department" , w1.Name as "Employee", w1.Salary as "Salary" from w1 join Department on Department.Id = w1.DepartmentId where w1.Rank = 1 or w1.Rank =2 or w1.Rank = 3 order by Department.Name , w1.Salary desc`
	sql := `SELECT GROUP_CONCAT(a2 SEPARATOR ",") FROM a GROUP BY a1`
	parser := parser.New()
	translated := translate(sql, parser)
	fmt.Println(translated)
}

func translate(sql string, parser *parser.Parser) string {
	stmtNodes, _, err := parser.Parse(sql, "", "")
	if err != nil {
		fmt.Printf("parse error: %v\n", err.Error())
		return "ERROR"
	}
	astNode := &stmtNodes[0]
	var stringBuilder strings.Builder
	ctx := format.NewRestoreCtx(
		format.RestoreStringSingleQuotes|format.RestoreNameDoubleQuotes|format.RestoreKeyWordUppercase|format.RestoreStringWithoutCharset|format.RestoreStringWithoutDefaultCharset,
		&stringBuilder,
	)
	(*astNode).Restore(ctx)
	return stringBuilder.String()
}
