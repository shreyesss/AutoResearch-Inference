# Edge-count clarification

The review phrase “two discovered_by edges” refers to two unique paper/query relationships. Exact SQL comparison checked four edge rows: each paper has its original provider-detail row plus an explicit query-receipt/revision binding added by packaging. All four rows are present after fresh restore. This is not four independent discoveries. The package and source hashes are unchanged; there is no effect on the retention approval.
