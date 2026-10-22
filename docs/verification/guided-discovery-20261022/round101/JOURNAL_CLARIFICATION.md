# Journal argument scope clarification

Both the authoritative database rows and normal history output contain the journal's normalized, allowlisted/redacted argument fields, not complete raw argv. The separate round101 projection preserves the same original stored fields (serialized as JSON), not additional unredacted arguments. The history command parses that stored JSON. Command counts and source immutability are unchanged. Original manifest remains intact.
