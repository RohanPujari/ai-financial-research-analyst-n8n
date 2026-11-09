# AI Financial Research Analyst — local deployment practice

This repository is a learning project for moving an n8n workflow from a development instance to a separate local practice instance. It is not a customer-facing service. The project is designed to be public; local learning logs and instance-specific exports stay out of the public repository.

## Local environments

- Development n8n: `http://localhost:5678`
- Practice deployment n8n: `http://localhost:5679`
- Both run in Docker Compose with separate persistent volumes.

## Intended release path

```text
Edit workflow in development n8n
  → Export workflow JSON and replace the versioned template
  → Review and commit the change
  → GitHub Actions starts on the Mac self-hosted runner
  → Deployment step reads the practice workflow's current IDs and credential references
  → GitHub Actions updates and publishes the practice workflow
  → Verify workflow and credential connection in the practice instance
```

The deployment workflow runs only for pushes to `main` and manual dispatch. It does not run on public pull requests. The Mac, Docker Desktop, and self-hosted runner must be on; this keeps the exercise free, but it does not host n8n on the public internet.

For the completed deployment exercise, the runner was registered as an ephemeral one-job runner and then removed automatically. Future deployment runs will wait in GitHub until another runner is started. No runner is left active on the Mac, so pushes do not currently deploy by themselves. Do not leave a runner connected unless you intend trusted repository workflows to control local Docker.

Before running the workflow, configure these GitHub repository settings:

- **Variable** `PRACTICE_WORKFLOW_ID`: the workflow ID shown in the practice n8n URL.

The practice n8n instance must already contain the Groq credential. The deployment script fetches the practice workflow export at run time and maps its credential reference and existing SEC User-Agent header onto the development workflow. The SEC contact email stays in the local n8n instance and is neither stored as a GitHub secret nor included in this public repository. Credential secrets are never exported or uploaded.

This repository is public, so keep write access limited to trusted maintainers. GitHub recommends using self-hosted runners with private repositories; this demo avoids `pull_request` triggers, but the Mac runner still has access to Docker and the local practice instance.

## Sensitive data

Do not commit API keys, decrypted credential exports, `.env` files, n8n data volumes, local learning logs, or backup archives. The workflow export contains node configuration and credential references, but not credential secrets.
