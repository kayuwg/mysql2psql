package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/pingcap/parser"
	"github.com/pingcap/parser/format"
	_ "github.com/pingcap/parser/test_driver"
)

func main() {

	// sql := `with w1 as ( Select *, Dense_Rank() over (partition by DepartmentId order by Salary desc ) as "Rank" from Employee ) Select Department.Name as "Department" , w1.Name as "Employee", w1.Salary as "Salary" from w1 join Department on Department.Id = w1.DepartmentId where w1.Rank = 1 or w1.Rank =2 or w1.Rank = 3 order by Department.Name , w1.Salary desc`
	sql := `SELECT GROUP_CONCAT(a2 SEPARATOR ",") FROM a GROUP BY a1`
	parser := parser.New()
	if len(os.Args) < 2 {
		translated := translate(sql, parser)
		fmt.Println(translated)
		return
	}
	filename := os.Args[1]
	file, err := os.Open(filename)
	if err != nil {
		log.Fatal(err)
		return
	}
	defer file.Close()
	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		log.Fatal(err)
	}
	for i, record := range records {
		// skip title
		if i == 0 {
			continue
		}
		record[1] = translate(record[1], parser)
	}
	writer := csv.NewWriter(os.Stdout)
	for _, record := range records {
		if err := writer.Write(record); err != nil {
			log.Fatalln("error writing record to csv:", err)
		}
	}
	// Write any buffered data to the underlying writer (standard output).
	writer.Flush()
	if err := writer.Error(); err != nil {
		log.Fatal(err)
	}
}

func translate(sql string, parser *parser.Parser) string {
	stmtNodes, _, err := parser.Parse(sql, "", "")
	if err != nil {
		return fmt.Sprintf("ERROR: mysql parse error: %v", err.Error())
	}
	astNode := &stmtNodes[0]
	var stringBuilder strings.Builder
	ctx := format.NewRestoreCtx(
		format.RestoreStringSingleQuotes|
			format.RestoreNameDoubleQuotes|
			format.RestoreKeyWordUppercase|
			format.RestoreStringWithoutCharset|
			format.RestoreStringWithoutDefaultCharset,
		&stringBuilder,
	)
	(*astNode).Restore(ctx)
	return stringBuilder.String()
}
