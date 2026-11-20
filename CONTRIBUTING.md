# Contributing

Useful contributions, roughly in order:

1. **A vault that breaks a script.** The smallest set of files that reproduces it, the command, and the output. Strip anything personal first.
2. **Rules from real use.** Something the agent filed in the wrong place, a merge it should not have proposed, a check that cries wolf. Include the before and after.
3. **New health checks or dreaming candidates** that a script can find without a model. Add a planted case to `examples/sample-vault/` so the check has something to find.
4. **Platform reports.** macOS and Linux runs of the checks in [AGENTS.md](AGENTS.md); so far only Windows with Git Bash has been tested.
5. **Non-English vaults.** The plural fold and stop words are English. A per-language list in `SCHEMA.md` would be welcome.

Before a pull request, run the checks in [AGENTS.md](AGENTS.md). Keep examples on the invented ceramics studio, Acme or Northwind.

Scripts stay on the Python standard library. If something needs a dependency (like defuddle or qmd), make it optional and detect it at run time.
