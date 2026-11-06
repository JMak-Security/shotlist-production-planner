# Security

ShotList is a local-only CSV parser and schedule generator. It does not execute input data, access
the network, or connect to a database. Treat user-supplied CSV files as untrusted.

The parser bounds file size, row count, field lengths, and durations; validates the header and every
row; rejects formula-leading text and control characters; and writes to a new output directory
using an atomic staging rename. These controls reduce risk but do not guarantee that every CSV
consumer interprets output identically.

Report security issues privately to the repository maintainer rather than including unpatched
exploit details in a public issue.
