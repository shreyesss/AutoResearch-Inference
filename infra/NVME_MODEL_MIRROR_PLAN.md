# Future Qwen model mirror on local NVMe

## Finding

The active model lives on `/dev/root` (Amazon EBS, 193 GiB total, 33 GiB free).
`/opt/dlami/nvme` is a separate 1.7 TiB Amazon EC2 NVMe Instance Storage volume.
The pinned Qwen revision contains 32 root files, 18 safetensors shards, and
55,586,114,863 bytes. The Hugging Face tree metadata for revision
`1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` supplies LFS SHA-256 for
large files and Git blob IDs for the others. Its SHA-256 is
`5b8b30bdf9a39e0da8a5c9a4adca5385e0e1f4afd73e21a5f39b2dab443285be`.

One cold B0 server boot loaded the 51.75 GiB checkpoint in about 310 seconds;
a later warm boot was about 72 seconds. That spread shows storage/page-cache
state matters. Faster local NVMe is a **hypothesis**, not yet a measured gain.
The mirror will still require the model to be loaded into GPU memory for every
fresh server; compile-cache persistence addresses a different startup phase.

## Prepare after the active pilot ends

```bash
PYTHONPATH=src .venv/bin/python infra/mirror_qwen_to_nvme.py plan
PYTHONPATH=src .venv/bin/python infra/mirror_qwen_to_nvme.py mirror
PYTHONPATH=src .venv/bin/python infra/mirror_qwen_to_nvme.py verify
```

`plan` is read-only. `mirror` refuses active GPU compute and serving containers,
holds the evaluator's GPU lease during the copy, checks the exact NVMe device,
streams each source file into a private staging directory, validates it against
the independent pinned revision hash, rehashes the target, and atomically
promotes the complete mirror. The destination is
`/opt/dlami/nvme/inference-autoresearch/models/Qwen3.8-27B-1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`.
It never modifies `.artifacts/models/Qwen3.8-27B`. `verify` rehashes all
destination files and returns a receipt SHA-256 to pin in a future campaign.

## Future operator-curve runner integration

Create a new campaign ID and model-source field after the mirror is verified.
The trusted controller should require the complete mirror receipt and its hash,
then bind-mount the NVMe path read-only at the same in-container model path
`/models/Qwen3.8-27B`. Keep the vLLM image, model revision, model files and
serving configuration otherwise identical. Never let the proposal agent choose
the model host path. Record the source device, mirror receipt hash, 18 shard
hashes, and `Loading weights took` in every cell. Do not mix EBS and NVMe cells
under one model-source campaign identity.

Compare matched fresh B0 boots from EBS and NVMe, with order alternated, using
server startup logs and the same model/config/GPU. Report cold and warm load
times separately and compare performance metrics after startup. A single faster
boot is insufficient because the EBS warm load already varied substantially.

This is ephemeral instance storage: after host replacement or reboot, verify
that the mount and receipt still exist before using the future campaign. If the
mirror is absent, rebuild it from the pinned EBS source; never silently fall
back to a different source within a campaign.
