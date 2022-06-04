module m2p

require (
	github.com/pingcap/parser v0.0.0-20200623164729-3a18f1e5dceb
)

replace github.com/pingcap/parser v0.0.0-20200623164729-3a18f1e5dceb => ./parser

go 1.16
