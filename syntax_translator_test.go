package main

import (
	"testing"

	"github.com/pingcap/parser"
)

var p *parser.Parser

func init() {
	p = parser.New()
}

func TestIf(t *testing.T) {
	sql := "SELECT IF(a.a1 > 1, 1, 2) FROM a"
	expected := `SELECT CASE WHEN "a"."a1">1 THEN 1 ELSE 2 END FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}
func TestIfNull(t *testing.T) {
	sql := "SELECT IFNULL(a.a1, 1, 2) FROM a"
	expected := `SELECT COALESCE("a"."a1", 1, 2) FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestIsNull(t *testing.T) {
	sql := "SELECT 1 FROM a WHERE ISNULL(a.a2)"
	expected := `SELECT 1 FROM "a" WHERE "a"."a2" IS NULL`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestLimit(t *testing.T) {
	sql := "SELECT 1 FROM a LIMIT 1, 2"
	expected := `SELECT 1 FROM "a" LIMIT 2 OFFSET 1`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestCast(t *testing.T) {
	sql := "SELECT CAST(a.a1 AS SIGNED), CAST(a.a1 AS UNSIGNED) FROM a"
	expected := `SELECT CAST("a"."a1" AS INTEGER),CAST("a"."a1" AS INTEGER) FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestDateAdd(t *testing.T) {
	sql := `SELECT DATE_ADD(a1, INTERVAL 1 DAY), ADDDATE("2022-06-03", 2) FROM a`
	expected := `SELECT "a1" + INTERVAL '1 DAY',CAST('2022-06-03' AS DATE) + INTERVAL '2 DAY' FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestDateDiff(t *testing.T) {
	sql := `SELECT DATEDIFF(a1, '2019-01-31') FROM a`
	expected := `SELECT "a1" - CAST('2019-01-31' AS DATE) FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestDateFormat(t *testing.T) {
	sql := `SELECT DATE_FORMAT(a1, '%b %e, %Y, %T') FROM a`
	expected := `SELECT TO_CHAR("a1", 'Mon dd, YYYY, HH24:MM:SS') FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestGroupConcat(t *testing.T) {
	sql := `SELECT GROUP_CONCAT(a2 SEPARATOR ",") FROM a GROUP BY a1`
	expected := `SELECT STRING_AGG("a2", ',') FROM "a" GROUP BY "a1"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestMonthQuarterYear(t *testing.T) {
	sql := `SELECT MONTH(a1), QUARTER(a1), YEAR(a1) FROM a`
	expected := `SELECT EXTRACT(MONTH FROM "a1"),EXTRACT(QUARTER FROM "a1"),EXTRACT(YEAR FROM "a1") FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestToDays(t *testing.T) {
	sql := `SELECT TO_DAYS(a1) FROM a`
	expected := `SELECT EXTRACT(EPOCH FROM "a1") FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}

func TestDiv(t *testing.T) {
	sql := `SELECT 5 DIV 2 FROM a`
	expected := `SELECT DIV(5, 2) FROM "a"`
	translated := translate(sql, p)
	if translated != expected {
		t.Fatalf(translated + " ==mismatch== " + expected)
	}
}
