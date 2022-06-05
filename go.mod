module m2p

require (
	github.com/go-sql-driver/mysql v1.5.0 // indirect
	github.com/pingcap/parser v0.0.0-20210602030610-10b704ade769
)

replace github.com/pingcap/parser v0.0.0-20210602030610-10b704ade769 => ./parser

go 1.16
