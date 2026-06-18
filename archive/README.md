# Archived Code

This folder contains code that is **not part of the active Cathode project** but is kept for historical reference.

## `cloud_deployment/`

Abandoned mid-migration GCP deployment (GCS + BigQuery + Vertex AI). The local backend in `backend/` is the supported path.

- Contains hardcoded GCP project IDs, bucket names, and Vertex endpoints from a personal account — **do not deploy as-is**
- `cathode_api/` duplicates the local FastAPI stack with an incomplete cloud `data_manager`
- README references a `docker-compose.yml` that was never committed
- Kept to document that cloud architecture was explored and deferred due to cost

## `playlistAgent.py`

Legacy prototype that fetched lyrics live from the Genius API instead of using the local lyrics dataset. Superseded by `backend/hybrid_agent.py`.
