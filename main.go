package main

import (
	"fmt"
	"strings"

	"github.com/pingcap/parser"
	"github.com/pingcap/parser/ast"
	"github.com/pingcap/parser/format"
	_ "github.com/pingcap/parser/test_driver"
)

func parse(sql string) (*ast.StmtNode, error) {
	p := parser.New()

	stmtNodes, _, err := p.Parse(sql, "", "")
	if err != nil {
		return nil, err
	}

	return &stmtNodes[0], nil
}

func main() {
	astNode, err := parse("SELECT t.c1 as 'tc1', b as `bb` FROM s s0 INNER JOIN t ON s0.id = \"yes\" GROUP BY bb")
	if err != nil {
		fmt.Printf("parse error: %v\n", err.Error())
		return
	}
	var stringBuilder strings.Builder
	ctx := format.NewRestoreCtx(
		format.RestoreStringSingleQuotes|format.RestoreNameDoubleQuotes|format.RestoreKeyWordUppercase,
		&stringBuilder,
	)
	(*astNode).Restore(ctx)
	fmt.Println(stringBuilder.String())

}
