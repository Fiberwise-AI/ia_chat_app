"""
API routes for pipeline management.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import json
import logging

from ia_auth_sessions import get_current_active_user
from nexusql import DatabaseManager

from app.core.dependencies import get_db_manager, get_pipeline_cache, get_services
from app.core.container import ServiceContainer
from app.core.pipeline_cache import PipelineCache

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])
logger = logging.getLogger(__name__)


class PipelineCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    pipeline_json: dict


class PipelineUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    pipeline_json: Optional[dict] = None
    is_active: Optional[bool] = None


class PipelineResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    version: str
    is_active: bool
    is_system: bool
    created_at: str
    updated_at: str


@router.get("/", response_model=List[PipelineResponse])
async def list_pipelines(
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
    include_inactive: bool = False
):
    """List all pipelines (from database and filesystem)."""
    logger.info(f"Listing pipelines for user: {current_user['username']}")

    try:
        # Query database pipelines
        if include_inactive:
            query = "SELECT * FROM pipeline_definitions ORDER BY created_at DESC"
            params = {}
        else:
            query = "SELECT * FROM pipeline_definitions WHERE is_active = :is_active ORDER BY created_at DESC"
            params = {"is_active": True}

        pipelines = db_manager.fetch_all(query, params)

        return [
            PipelineResponse(
                id=p["id"],
                name=p["name"],
                display_name=p["display_name"],
                description=p["description"],
                version=p["version"],
                is_active=p["is_active"],
                is_system=p["is_system"],
                created_at=p["created_at"].isoformat(),
                updated_at=p["updated_at"].isoformat()
            )
            for p in pipelines
        ]

    except Exception as e:
        logger.error(f"Error listing pipelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get pipeline details by ID."""
    try:
        pipeline = db_manager.fetch_one(
            "SELECT * FROM pipeline_definitions WHERE id = :id",
            {"id": pipeline_id}
        )

        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        return PipelineResponse(
            id=pipeline["id"],
            name=pipeline["name"],
            display_name=pipeline["display_name"],
            description=pipeline["description"],
            version=pipeline["version"],
            is_active=pipeline["is_active"],
            is_system=pipeline["is_system"],
            created_at=pipeline["created_at"].isoformat(),
            updated_at=pipeline["updated_at"].isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pipeline_id}/json")
async def get_pipeline_json(
    pipeline_id: str,
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get pipeline JSON definition."""
    try:
        pipeline = db_manager.fetch_one(
            "SELECT pipeline_json FROM pipeline_definitions WHERE id = :id",
            {"id": pipeline_id}
        )

        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        return {"pipeline_json": json.loads(pipeline["pipeline_json"])}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pipeline JSON: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PipelineResponse)
async def create_pipeline(
    pipeline: PipelineCreate,
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
    pipeline_cache: PipelineCache = Depends(get_pipeline_cache)
):
    """Create a new pipeline."""
    logger.info(f"Creating pipeline: {pipeline.name}")

    try:
        # Validate pipeline JSON has required fields
        if "name" not in pipeline.pipeline_json:
            raise HTTPException(status_code=400, detail="Pipeline JSON must have 'name' field")

        if "steps" not in pipeline.pipeline_json:
            raise HTTPException(status_code=400, detail="Pipeline JSON must have 'steps' field")

        # Check if pipeline with same name exists
        existing = db_manager.fetch_one(
            "SELECT id FROM pipeline_definitions WHERE name = :name",
            {"name": pipeline.name}
        )

        if existing:
            raise HTTPException(status_code=400, detail=f"Pipeline '{pipeline.name}' already exists")

        # Create pipeline
        pipeline_id = str(uuid4())
        now = datetime.now()

        db_manager.execute(
            """
            INSERT INTO pipeline_definitions
            (id, name, display_name, description, version, pipeline_json, is_active, is_system, created_by, created_at, updated_at)
            VALUES (:id, :name, :display_name, :description, :version, :pipeline_json, :is_active, :is_system, :created_by, :created_at, :updated_at)
            """,
            {
                "id": pipeline_id,
                "name": pipeline.name,
                "display_name": pipeline.display_name,
                "description": pipeline.description,
                "version": pipeline.pipeline_json.get("version", "1.0.0"),
                "pipeline_json": json.dumps(pipeline.pipeline_json),
                "is_active": True,
                "is_system": False,
                "created_by": current_user["id"],
                "created_at": now,
                "updated_at": now
            }
        )

        # Load into cache
        pipeline_cache.add(pipeline.name, pipeline.pipeline_json)

        logger.info(f"Pipeline '{pipeline.name}' created successfully")

        return PipelineResponse(
            id=pipeline_id,
            name=pipeline.name,
            display_name=pipeline.display_name,
            description=pipeline.description,
            version=pipeline.pipeline_json.get("version", "1.0.0"),
            is_active=True,
            is_system=False,
            created_at=now.isoformat(),
            updated_at=now.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: str,
    updates: PipelineUpdate,
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
    pipeline_cache: PipelineCache = Depends(get_pipeline_cache)
):
    """Update pipeline."""
    try:
        # Get existing pipeline
        pipeline = db_manager.fetch_one(
            "SELECT * FROM pipeline_definitions WHERE id = :id",
            {"id": pipeline_id}
        )

        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        # Don't allow updating system pipelines
        if pipeline["is_system"]:
            raise HTTPException(status_code=403, detail="Cannot update system pipelines")

        # Build update query
        update_fields = []
        params = {"id": pipeline_id, "updated_at": datetime.now()}

        if updates.display_name is not None:
            update_fields.append("display_name = :display_name")
            params["display_name"] = updates.display_name

        if updates.description is not None:
            update_fields.append("description = :description")
            params["description"] = updates.description

        if updates.is_active is not None:
            update_fields.append("is_active = :is_active")
            params["is_active"] = updates.is_active

        if updates.pipeline_json is not None:
            # Validate JSON
            if "name" not in updates.pipeline_json or "steps" not in updates.pipeline_json:
                raise HTTPException(status_code=400, detail="Invalid pipeline JSON structure")

            update_fields.append("pipeline_json = :pipeline_json")
            update_fields.append("version = :version")
            params["pipeline_json"] = json.dumps(updates.pipeline_json)
            params["version"] = updates.pipeline_json.get("version", "1.0.0")

            # Update cache
            pipeline_cache.add(pipeline["name"], updates.pipeline_json)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        update_fields.append("updated_at = :updated_at")

        query = f"UPDATE pipeline_definitions SET {', '.join(update_fields)} WHERE id = :id"
        db_manager.execute(query, params)

        # Get updated pipeline
        updated = db_manager.fetch_one(
            "SELECT * FROM pipeline_definitions WHERE id = :id",
            {"id": pipeline_id}
        )

        return PipelineResponse(
            id=updated["id"],
            name=updated["name"],
            display_name=updated["display_name"],
            description=updated["description"],
            version=updated["version"],
            is_active=updated["is_active"],
            is_system=updated["is_system"],
            created_at=updated["created_at"].isoformat(),
            updated_at=updated["updated_at"].isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: str,
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
    pipeline_cache: PipelineCache = Depends(get_pipeline_cache)
):
    """Delete pipeline."""
    try:
        # Get pipeline
        pipeline = db_manager.fetch_one(
            "SELECT * FROM pipeline_definitions WHERE id = :id",
            {"id": pipeline_id}
        )

        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        # Log warning if deleting system pipeline
        if pipeline["is_system"]:
            logger.warning(f"Deleting system pipeline: {pipeline['name']} (requested by user: {current_user['username']})")

        # Delete from database
        db_manager.execute(
            "DELETE FROM pipeline_definitions WHERE id = :id",
            {"id": pipeline_id}
        )

        # Remove from cache
        pipeline_cache.remove(pipeline["name"])

        logger.info(f"Pipeline '{pipeline['name']}' deleted successfully")

        return {"message": f"Pipeline '{pipeline['name']}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-from-filesystem")
async def import_from_filesystem(
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
    pipeline_cache: PipelineCache = Depends(get_pipeline_cache),
    request: Request = None,
    services_container: ServiceContainer = Depends(get_services),
    force: bool = False,
    dry_run: bool = False,
    validate_only: bool = False,
    allow_hitl_override: bool = False
):
    """Import pipelines from filesystem into database."""
    logger.info(f"Importing pipelines from filesystem by user: {current_user['username']}")

    try:
        from pathlib import Path

        pipelines_dir = Path(__file__).parent.parent / "pipelines"
        imported = []
        skipped = []

        for json_file in pipelines_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    pipeline_json = json.load(f)

                pipeline_name = json_file.stem  # Filename without extension

                # Check if already exists
                existing = db_manager.fetch_one(
                    "SELECT * FROM pipeline_definitions WHERE name = :name",
                    {"name": pipeline_name}
                )

                # Validate pipeline JSON before writing
                # Use ia_modules validator - validate pipeline structure and step imports
                try:
                    from ia_modules.cli.validate import validate_pipeline
                    validation_result = validate_pipeline(pipeline_json, strict=False)
                except Exception as e:
                    logger.warning(f"Validation routine failed for {pipeline_name}: {e}")
                    validation_result = None

                if validation_result is not None:
                    if not validation_result.is_valid:
                        # If the request only asked to validate, return errors
                        if dry_run or validate_only:
                            skipped.append(f"{pipeline_name} (validation failed)")
                            continue
                        else:
                            # Abort the whole operation and return errors for non-dry-run
                            raise HTTPException(status_code=400, detail={"pipeline": pipeline_name, "errors": validation_result.errors, "warnings": validation_result.warnings})

                if existing:
                    # existing pipeline - decide behavior based on 'force'
                    if not force:
                        skipped.append(f"{pipeline_name} (already exists)")
                        continue

                    # Force operation allowed only for admins
                    if not current_user.get('is_admin'):
                        raise HTTPException(status_code=403, detail="Force import is restricted to administrators")

                    # Prevent force if there are pending HITL interactions (protect live workflows)
                    if not allow_hitl_override:
                        try:
                            pending = db_manager.fetch_one(
                                "SELECT COUNT(*) as cnt FROM hitl_interactions WHERE pipeline_id = :pipeline_id AND status = 'pending'",
                                {"pipeline_id": existing['id']}
                            )
                            if pending and pending.get('cnt', 0) > 0:
                                raise HTTPException(status_code=409, detail=f"Pipeline {pipeline_name} has pending human interactions - cannot force import")
                        except Exception:
                            # If hitl table doesn't exist or query fails, continue silently (no HITL on system)
                            pass

                    # If only asked to validate, do not write
                    if validate_only or dry_run:
                        imported.append(pipeline_name)
                        continue

                    # Replace existing pipeline JSON
                    pipeline_id = existing['id']
                    now = datetime.now()

                    # Write previous version to versions table for rollback/audit
                    try:
                        db_manager.execute(
                            """
                            INSERT INTO pipeline_versions (id, pipeline_id, pipeline_name, pipeline_json, git_commit_sha, imported_by)
                            VALUES (:id, :pipeline_id, :pipeline_name, :pipeline_json, :git_commit_sha, :imported_by)
                            """,
                            {
                                'id': str(uuid4()),
                                'pipeline_id': pipeline_id,
                                'pipeline_name': pipeline_name,
                                'pipeline_json': existing.get('pipeline_json'),
                                'git_commit_sha': request.headers.get('X-GIT-COMMIT') if request else None,
                                'imported_by': current_user.get('id')
                            }
                        )
                    except Exception:
                        # Ignore if table not present or insert fails
                        pass

                    db_manager.execute(
                        """
                        UPDATE pipeline_definitions
                        SET pipeline_json = :pipeline_json,
                            version = :version,
                            updated_at = :updated_at
                        WHERE id = :id
                        """,
                        {
                            "id": pipeline_id,
                            "pipeline_json": json.dumps(pipeline_json),
                            "version": pipeline_json.get("version", existing.get('version', '1.0.0')),
                            "updated_at": now
                        }
                    )

                    # Refresh cache (update in-memory registry)
                    pipeline_cache.add(pipeline_name, pipeline_json)

                    imported.append(pipeline_name)
                    logger.info(f"Replaced pipeline: {pipeline_name}")
                    try:
                        redis_client = getattr(services_container, 'redis_client', None)
                        if redis_client:
                            commit_sha = None
                            if request:
                                commit_sha = request.headers.get('X-GIT-COMMIT') or request.headers.get('x-git-commit')
                            await redis_client.publish('pipeline_update', json.dumps({
                                'pipeline': pipeline_name,
                                'git_commit': commit_sha
                            }))
                    except Exception as e:
                        logger.debug(f"Failed to publish pipeline_update: {e}")
                    continue

                # Import (new pipeline)
                pipeline_id = str(uuid4())
                now = datetime.now()

                db_manager.execute(
                    """
                    INSERT INTO pipeline_definitions
                    (id, name, display_name, description, version, pipeline_json, is_active, is_system, created_by, created_at, updated_at)
                    VALUES (:id, :name, :display_name, :description, :version, :pipeline_json, :is_active, :is_system, :created_by, :created_at, :updated_at)
                    """,
                    {
                        "id": pipeline_id,
                        "name": pipeline_name,
                        "display_name": pipeline_json.get("name", pipeline_name),
                        "description": pipeline_json.get("description", ""),
                        "version": pipeline_json.get("version", "1.0.0"),
                        "pipeline_json": json.dumps(pipeline_json),
                        "is_active": True,
                        "is_system": True,  # Imported from filesystem = system pipeline
                        "created_by": current_user["id"],
                        "created_at": now,
                        "updated_at": now
                    }
                )

                imported.append(pipeline_name)
                logger.info(f"Imported pipeline: {pipeline_name}")

                # Create initial version entry
                try:
                    db_manager.execute(
                        """
                        INSERT INTO pipeline_versions (id, pipeline_id, pipeline_name, pipeline_json, git_commit_sha, imported_by)
                        VALUES (:id, :pipeline_id, :pipeline_name, :pipeline_json, :git_commit_sha, :imported_by)
                        """,
                        {
                            'id': str(uuid4()),
                            'pipeline_id': pipeline_id,
                            'pipeline_name': pipeline_name,
                            'pipeline_json': json.dumps(pipeline_json),
                            'git_commit_sha': request.headers.get('X-GIT-COMMIT') if request else None,
                            'imported_by': current_user.get('id')
                        }
                    )
                except Exception:
                    pass

                # Publish a pipeline update event for cache invalidation if Redis client is available
                try:
                    redis_client = getattr(services_container, 'redis_client', None)
                    if redis_client:
                        commit_sha = None
                        if request:
                            commit_sha = request.headers.get('X-GIT-COMMIT') or request.headers.get('x-git-commit')
                        await redis_client.publish('pipeline_update', json.dumps({
                            'pipeline': pipeline_name,
                            'git_commit': commit_sha
                        }))
                except Exception as e:
                    logger.debug(f"Failed to publish pipeline_update: {e}")

            except Exception as e:
                logger.error(f"Error importing {json_file.name}: {e}")
                skipped.append(f"{json_file.name} (error: {str(e)})")

        return {
            "imported": imported,
            "skipped": skipped,
            "total_imported": len(imported),
            "total_skipped": len(skipped)
        }

@router.post("/{pipeline_name}/revert")
async def revert_pipeline(
    pipeline_name: str,
    version_id: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db_manager: DatabaseManager = Depends(get_db_manager),
    pipeline_cache: PipelineCache = Depends(get_pipeline_cache),
    request: Request = None,
    services_container: ServiceContainer = Depends(get_services)
):
    """Revert pipeline to a previous version from pipeline_versions table."""
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Only admins may revert pipelines")

    try:
        if version_id:
            version = db_manager.fetch_one(
                "SELECT * FROM pipeline_versions WHERE id = :id",
                {"id": version_id}
            )
        else:
            # Get latest version for pipeline
            version = db_manager.fetch_one(
                "SELECT * FROM pipeline_versions WHERE pipeline_name = :pipeline_name ORDER BY imported_at DESC LIMIT 1",
                {"pipeline_name": pipeline_name}
            )

        if not version:
            raise HTTPException(status_code=404, detail="Pipeline version not found")

        # Check for pending HITL interactions
        pending = None
        try:
            pending = db_manager.fetch_one(
                "SELECT COUNT(*) AS cnt FROM hitl_interactions WHERE pipeline_id = :pipeline_id AND status = 'pending'",
                {"pipeline_id": version['pipeline_id']}
            )
            if pending and pending.get('cnt', 0) > 0:
                raise HTTPException(status_code=409, detail="Cannot revert while pipeline has pending human interactions")
        except Exception:
            pass

        # Write back to pipeline_definitions
        db_manager.execute(
            "UPDATE pipeline_definitions SET pipeline_json = :pipeline_json, updated_at = :updated_at WHERE name = :name",
            {
                'pipeline_json': version['pipeline_json'],
                'updated_at': datetime.now(),
                'name': pipeline_name
            }
        )

        pipeline_cache.add(pipeline_name, json.loads(version['pipeline_json']))

        # Publish cache invalidation
        try:
            redis_client = getattr(services_container, 'redis_client', None)
            if redis_client:
                await redis_client.publish('pipeline_update', json.dumps({'pipeline': pipeline_name, 'reverted_to': version['id']}))
        except Exception:
            pass

        return {"message": f"Pipeline '{pipeline_name}' reverted to version {version['id']}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverting pipeline {pipeline_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Error importing pipelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
