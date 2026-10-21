# Rollback and recovery

Release updates are explicit; there is no push-triggered deployment. Before changing the running release save its Git revision, image/workflow hashes, private environment, matching n8n encryption key, consistent n8n state and PostgreSQL archive. Keep secrets/backups outside Git and encrypt off-host copies.

## Application-only regression

Stop accepting new executions. Reconcile in-flight requests; do not blindly replay. Check out the previously approved release on the independent host, restore its image/tag metadata in the private env deliberately, rebuild/start only the app/processor as appropriate, and run private acceptance. Preserve every named volume. An older application will refuse a newer migration ledger; that is a release blocker, not permission to downgrade/delete tables.

## Workflow regression

Use the saved manifest and exact previous generated workflow JSON. Import/rebind/publish through the protected CLI, preserving stable workflow IDs and the same compatible encrypted credential store. Restart n8n/runner, verify authentication and test with a new controlled request. Importing does not prove the old/new nodes ran; record the actual execution/revision. Never replay unfinished historical executions automatically.

## Database failure or corruption

Do not restore over the live database. Create a separately approved empty destination in the new companion project, restore the last valid custom archive with the exact destination-name confirmation, verify schema/permissions/payload hashes, then obtain an explicit traffic-cutover decision. An older archive may lose later reviews/executions; explain the loss window. There is no destructive downgrade, table reset or production reseed command in these scripts.

## n8n host/volume loss

Stop n8n/runner and restore the complete consistent `.n8n` backup onto a new independent volume/host. Use the **matching** encryption key from private recovery storage. Workflow exports alone are insufficient; a new random key will not decrypt old credentials. Verify permissions/SQLite WAL consistency, start privately, check auth and controlled source processing, then restore approved ingress. Replacement-host restore remains pending; local stop/backup/restart preservation was exercised.

## Ingress or credential incident

Disable only this new host's Funnel (`tailscale funnel reset`, after operator approval) or stop its gateway. Do not change `kailor.co.za` records or other applications. Rotate actually exposed provider/service credentials through the owner console; deliberately rebind n8n. Do not rewrite public Git history without approval or treat an account/inbox identifier as an API key. Keep Gemini disabled while billing status is unknown.

Never run `docker compose down -v`, delete a database/volume, overwrite an env file/key or reset original EventOps infrastructure as an operational shortcut. The free-tier budget remains zero during recovery: if free capacity/quota is unavailable, report downtime rather than creating paid replacements.
