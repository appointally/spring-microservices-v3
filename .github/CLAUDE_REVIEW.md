# Required Claude review

This public repository uses a local workflow because GitHub does not permit it
to call Appointally's private reusable workflow. The job publishes the same
required `review / review` context as other organization repositories.

A maintainer must configure the `ANTHROPIC_API_KEY` Actions secret for this
repository (or grant it access through an organization secret). The existing
organization key is limited to private repositories. Missing credentials,
partial reviews, findings, unresolved review threads, API failures and stale
heads keep the check blocked. The workflow does not exempt installation PRs.

The review reads the full PR patch and file manifest, requires structured
completion and approval for every changed file, and uses only the workflow's
repository-scoped token with read access to contents and write access to PRs.
Fork and restricted bot PRs without credentials remain blocked; a maintainer
can submit the inspected change through a maintainer-owned replacement PR.
