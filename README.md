## A translator from mysql to psql
Go translator deals with some syntactic differences such as date function names. Run `go run syntax_translator.go syntax.sql` to see what happens.

Python rectifier transforms some queries allowed by MySQL but not PostgreSQL to a form that PostgreSQL accepts. Run `python3 structure_rectifier.py structure.sql` to see what happens.

Specify input and output folder in `translate.sh`.
