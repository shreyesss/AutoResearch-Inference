# Optional VM read replica timer

These are **user service** examples configured for `bitlane-b1`. They use its IAM role; no provider keys or workstation AWS credentials are copied. Adapt the venv/state paths and bucket when installing elsewhere.

```bash
mkdir -p ~/.config/systemd/user
cp infra/research-replica/autoresearch-replica.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now autoresearch-replica.timer
systemctl --user start autoresearch-replica.service
systemctl --user status autoresearch-replica.timer
journalctl --user -u autoresearch-replica.service -n 30
```

The user manager must run outside SSH sessions (`loginctl show-user "$USER" -p Linger`; an administrator can enable lingering). This timer downloads only research snapshots. It does not overwrite writer research or independent experiment records, upload VM state, update serving code, or execute benchmarks. Use `researchctl --replica search ...` for the latest downloaded corpus. A changed HEAD is checksum-verified in a separate versioned directory; unchanged HEAD performs one small remote lookup. Prior replicas remain available; inspect disk usage before pruning older versions. Code updates remain an explicit Git/bundle operation.
