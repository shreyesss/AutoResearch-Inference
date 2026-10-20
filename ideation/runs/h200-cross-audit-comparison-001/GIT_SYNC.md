# Git synchronization and preservation

## Repository and source commits

Both VMs use `git@github.com:shreyesss/AutoResearch-Inference.git`, branch `main`.
The local Mac workspace is not itself a Git repository; publishing used an isolated
worktree on `.223`, followed by normal pushes and fast-forward pulls on both VMs.

| Artifact | Commit containing the preserved input | Git tree |
|---|---|---|
| B200 audit, `pr-evaluation-audit-001` | `6b77211f1ba0b87ee2f7e243426ced71dfdf1c23` | `85683bc8c190bd30ecc0d6c38d77413436e0b2be` |
| Sofia H200 audit, `h200-pr-evaluation-audit-001` | `5121f8ab9df7e6b73065bab0c7fe5061a3b5013d` | `bad58e03b457ebc6e60ff45871316bf370e3fdc7` |
| Independent H200 research, `h200-fresh-research-001` | `2227aa48274947a834b58d0db93d99b264f7f068` | `0ed71251824f0fbf991fd2e152bda6d83d25de82` |

The comparison is a separate fourth directory, `h200-cross-audit-comparison-001`.
No source run was renamed, combined with another run, or edited to agree with this
comparison. The comparison's own final commit is reported in the delivery receipt
outside this directory, avoiding a self-referential commit identifier.

## Locations on both VMs

Each of the four directories above is available below:

- `sofia-gpu-mumbai:/home/ubuntu/shreyas/skunk-work/ideation/runs/`
- `ubuntu@217.18.55.223:/home/ubuntu/AutoResearch-Inference/ideation/runs/`

For example, the comparison lives at
`/home/ubuntu/shreyas/skunk-work/ideation/runs/h200-cross-audit-comparison-001`
on Sofia and
`/home/ubuntu/AutoResearch-Inference/ideation/runs/h200-cross-audit-comparison-001`
on `.223`.

## Preservation checks

During the first synchronization, both original checkouts fast-forwarded to
`2227aa48274947a834b58d0db93d99b264f7f068`. All three source tree hashes matched
between VMs, and neither H200 run had a tracked working-tree diff.

Before and after pulling, SHA-256 content checks verified all 18 unrelated dirty
tracked files on Sofia and all 7 on `.223`. All 806 original files in the fresh
H200 directory were also verified byte-for-byte after its move into Git tracking.
The final comparison synchronization repeats the dirty-file and source-tree
checks; its result is recorded in the separate delivery receipt.

The `.223` checkout retains a local modification to
`ideation/runs/pr-evaluation-audit-001/README.md` and an untracked
`ideation/runs/pr-evaluation-audit-001/h200/` evaluator directory. These are
independent work, were not committed or overwritten, and are not included in the
B200 tree hash above. Thus the **tracked B200 audit is identical** on the two VMs;
the entire B200 working directory is intentionally not claimed identical.
Other unrelated code, configuration, infrastructure and research edits remain in
their original working checkouts.

## Included evidence and exclusions

The fresh run contributes 804 tracked files. Source snapshots, patches, generated
research, prompts, evidence logs and test logs are retained, including files
needed to resolve report citations. The SQLite backup and Python bytecode cache
are excluded from Git but preserved on `.223`; no `.env` or SSH key was added.
A credential-pattern scan of all newly published fresh-run content found no
matches. This is a bounded pattern check, not a claim of exhaustive secret
detection.

A complete pre-publication copy is preserved at:

`ubuntu@217.18.55.223:/home/ubuntu/h200-fresh-research-001-preserved-before-git-20261020`

The isolated publishing worktree is:

`ubuntu@217.18.55.223:/home/ubuntu/h200-research-sync-20261020`

No force push, hard reset, deployment change, or GPU experiment was performed by
this synchronization task.
