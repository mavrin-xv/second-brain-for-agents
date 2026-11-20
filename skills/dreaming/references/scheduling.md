# Scheduling the nightly run

The night job is plain scripts, so any scheduler works. It must not need a model to succeed; the judgement step (SKILL.md step 2) is an optional extra if your harness can run an agent on a schedule.

## The job

`templates/nightly.sh` in this repo runs, in order: qmd re-index (if installed), graph with footers, health report, ingest queue, dreaming scan. It writes the health report to `proposals/health-YYYY-MM-DD.txt` and exits non-zero if any step failed.

```bash
cp templates/nightly.sh ~/notes/nightly.sh
VAULT_DIR=~/notes/vault ~/notes/nightly.sh
```

Failures should be loud: if a step errors, the morning review should say so instead of showing an empty proposal file. Check the exit code of the script, or send the health file to wherever you read things in the morning.

## cron (Linux, macOS)

```cron
30 3 * * * /home/you/notes/nightly.sh >> /home/you/notes/nightly.log 2>&1
```

## launchd (macOS)

Create `~/Library/LaunchAgents/local.vault.nightly.plist` with `ProgramArguments` pointing at `nightly.sh` and `StartCalendarInterval` Hour 3, Minute 30. Load it with `launchctl load ~/Library/LaunchAgents/local.vault.nightly.plist`.

## Windows Task Scheduler

```powershell
$a = New-ScheduledTaskAction -Execute "bash.exe" -Argument "-lc ~/notes/nightly.sh"
$t = New-ScheduledTaskTrigger -Daily -At 3:30am
Register-ScheduledTask -TaskName "vault-nightly" -Action $a -Trigger $t
```

Or call `python3` on each script from a `.cmd` file if you do not use bash.

## Agent harness schedulers

If your agent tool can run a prompt on a schedule, use a prompt like:

```
Run the dreaming skill, step 1 and step 2, on the vault at ~/notes/vault.
Write only the proposal file. Do not edit any note. End with the candidate count.
```

Keep the "write only the proposal file" sentence. It is the line that keeps an unattended agent from editing your notes.

## Morning

Make the review a habit with one fixed entry point: the first message of the day to your agent, or a shell alias:

```bash
alias dream='python3 ~/.claude/skills/dreaming/scripts/dream_digest.py status --pending'
```
