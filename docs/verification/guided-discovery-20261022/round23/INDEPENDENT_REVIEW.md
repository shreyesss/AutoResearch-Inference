# Independent round23 loader review

The narrow closure is supported: the exact two-file checkpoint loaded by Transformers 5.16.1/tokenizers 0.23.2 in the isolated default configuration has the same complete 1,283-entry added-token table as raw input. This resolves the specific sidecar named-token flag concern for that combination, not native compatibility or deployment admission.

I independently checked all29 frozen file hashes, all six retained installed-source hashes, the four installed/remote source pairs, complete added-token data, and model serialization after the stated merge-pair/default normalization. I read the actual base loader map override at1903–1925 and the pinned vLLM from_pretrained wrapper. The report's apparent BOS/EOS discrepancy is correctly classified as an input discrepancy resolved by actual loader precedence. Equivalent serialized data after normalization is not a cross-version algorithm theorem.

Seven saved comparisons are raw0.23.2 versus materialized0.23.2, not the old0.22.2 donor engine. Required source dependency versions really differ from earlier native experiments. The split_special_tokens negative control establishes why checkpoint SHA alone is insufficient. Runtime added vocabulary and tokenizer options can invalidate an otherwise matching artifact; default raw-table equality must not justify a registry bypass.

The probe uses actual tokenizer-only materialization with import guards and offline local files; it does not execute the vLLM wrapper/cache adapter, a model, native TokTier, or a production environment. Recorded import/network absence applies during this probe, not package/source retrieval. I did not rerun tokenizer execution or package installation.

Keep S01 accepted for bounded CPU investigation and implementation/service unqualified. Next useful gate is a chosen-runtime effective-loader/native compatibility bridge and actual adapter option guards, not more raw-SHA-only tests. No performance claim or broader deployment closure follows.
