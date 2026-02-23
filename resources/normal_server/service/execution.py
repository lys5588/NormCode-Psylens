"""
Run Execution Logic

Handles the execution of NormCode plans with event emission.
"""

import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from .config import get_config
from .state import RunState
from .globals import broadcast_event
from .userbench import get_userbench_manager
from scripts.runner import load_repositories, create_body


# Fields that contain binary data and should not be serialized
BINARY_FIELDS = {'pptx_bytes', 'bytes', 'binary_data', 'raw_bytes', 'file_bytes', 'image_bytes'}


def sanitize_for_serialization(data: Any, max_depth: int = 10) -> Any:
    """
    Recursively sanitize data for JSON serialization by removing binary fields.
    
    Args:
        data: The data to sanitize
        max_depth: Maximum recursion depth to prevent infinite loops
        
    Returns:
        Sanitized data safe for JSON serialization
    """
    if max_depth <= 0:
        return "[max depth reached]"
    
    if data is None:
        return None
    
    if isinstance(data, bytes):
        return f"[binary data: {len(data)} bytes]"
    
    if isinstance(data, (str, int, float, bool)):
        return data
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in BINARY_FIELDS:
                if isinstance(value, bytes):
                    result[key] = f"[binary data: {len(value)} bytes]"
                elif value is not None:
                    result[key] = "[binary data omitted]"
            else:
                result[key] = sanitize_for_serialization(value, max_depth - 1)
        return result
    
    if isinstance(data, (list, tuple)):
        return [sanitize_for_serialization(item, max_depth - 1) for item in data]
    
    # For other types, try to convert to string
    try:
        return str(data)
    except Exception:
        return "[unserializable]"


def save_run_metadata(db_path: Path, run_id: str, metadata: dict):
    """
    Save run metadata to the database for historical run recovery.
    """
    import sqlite3
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        cursor = conn.cursor()
        
        # Ensure table exists (it should from OrchestratorDB, but just in case)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS run_metadata (
                run_id TEXT PRIMARY KEY,
                metadata_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert or replace metadata
        cursor.execute('''
            INSERT OR REPLACE INTO run_metadata (run_id, metadata_json)
            VALUES (?, ?)
        ''', (run_id, json.dumps(metadata)))
        
        conn.commit()
        conn.close()
        logging.debug(f"Saved run metadata for {run_id}: {metadata}")
    except Exception as e:
        logging.warning(f"Failed to save run metadata for {run_id}: {e}")


def setup_run_logging(run_dir: Path, run_id: str) -> logging.FileHandler:
    """
    Set up file logging for a specific run.
    Returns the file handler so it can be removed after the run.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = run_dir / f"run_{run_id[:8]}_{timestamp}.log"
    
    # Create file handler with DEBUG level to capture all details
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    ))
    
    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    logging.info(f"Run logging initialized: {log_file}")
    return file_handler


async def execute_run_with_events(run_state: RunState, orchestrator, total_inferences: int):
    """
    Execute orchestrator cycles with granular event emission.
    This wraps the orchestrator's async execution to emit events for each inference.
    """
    completed_count = 0
    cycle_count = 0
    
    # Loop tracking for better progress reporting
    loop_state = {
        'active_loops': {},  # flow_index -> {'iteration': n, 'started_at': time, 'children_completed': 0}
        'total_loop_iterations': 0,  # Total iterations across all loops
        'unique_completed': set(),  # Track unique flow_indexes completed (not counting loop re-executions)
    }
    
    # Get the blackboard to monitor status changes
    bb = orchestrator.blackboard
    tracker = orchestrator.tracker
    
    # Track previous statuses to detect changes
    prev_statuses = dict(run_state._node_statuses)
    
    async def emit_status_changes():
        """Emit events for status changes since last check."""
        nonlocal prev_statuses
        changes = {}
        
        for item in orchestrator.waitlist.items:
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            if flow_index:
                current_status = bb.get_item_status(flow_index)
                if prev_statuses.get(flow_index) != current_status:
                    changes[flow_index] = current_status
                    run_state.set_node_status(flow_index, current_status)
        
        if changes:
            await run_state.emit_event("node:statuses", {"statuses": changes})
            prev_statuses = dict(run_state._node_statuses)
        
        return changes
    
    async def run_cycle_async():
        """Run one cycle with event emission.
        
        IMPORTANT: We must check readiness INSIDE the execution loop, not before.
        This is because loop/quantifying sequences may set context variables that
        make other items ready during the same cycle. Collecting ready items at
        the start would miss these newly-ready items.
        """
        nonlocal completed_count, cycle_count
        
        cycle_count = tracker.cycle_count + 1
        retries = []
        cycle_executions = 0
        
        # Process ALL items, checking readiness for each one INSIDE the loop
        # This matches the orchestrator's native _run_cycle_async behavior
        items_to_process = list(orchestrator.waitlist.items)
        
        for item in items_to_process:
            # Check for pause/stop before each inference
            if run_state._stop_requested:
                break
            
            # Wait if paused
            if not run_state._pause_event.is_set():
                await run_state.emit_event("execution:paused", {
                    "completed_count": completed_count,
                    "total_count": total_inferences,
                    "cycle_count": cycle_count,
                })
            
            should_continue = await run_state.wait_if_paused()
            if not should_continue:
                break
            
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            
            # Check readiness INSIDE the loop (critical for loops/quantifying sequences)
            # This allows items that become ready after loop iterations to be executed
            item_status = bb.get_item_status(flow_index)
            if item_status != 'pending':
                continue
            
            if not orchestrator._is_ready(item):
                continue
            
            cycle_executions += 1
            concept_name = item.inference_entry.concept_to_infer.concept_name
            
            # Update current inference tracking
            run_state.current_inference = flow_index
            
            # Check for breakpoint BEFORE execution
            if run_state.check_breakpoint(flow_index):
                run_state.status = "paused"
                run_state._pause_event.clear()
                await run_state.emit_event("breakpoint:hit", {
                    "flow_index": flow_index,
                    "concept_name": concept_name,
                    "completed_count": completed_count,
                    "total_count": total_inferences,
                })
                run_state.add_log("info", flow_index, f"Breakpoint hit - paused before execution")
                
                # Wait for resume
                should_continue = await run_state.wait_if_paused()
                if not should_continue:
                    return False, retries
            
            # Emit inference started
            await run_state.emit_event("inference:started", {
                "flow_index": flow_index,
                "concept_name": concept_name,
            })
            run_state.add_log("info", flow_index, f"Starting: {concept_name}")
            
            # Execute the item
            start_time = time.time()
            try:
                new_status = await orchestrator._execute_item_async(item)
                duration = time.time() - start_time
                
                if new_status == 'completed':
                    # Track unique completions (not counting loop re-executions)
                    is_first_completion = flow_index not in loop_state['unique_completed']
                    if is_first_completion:
                        loop_state['unique_completed'].add(flow_index)
                    
                    completed_count += 1
                    
                    # Check if this is a loop completing
                    if flow_index in loop_state['active_loops']:
                        loop_info = loop_state['active_loops'].pop(flow_index)
                        await run_state.emit_event("inference:completed", {
                            "flow_index": flow_index,
                            "duration": duration,
                            "is_loop": True,
                            "total_iterations": loop_info['iteration'],
                        })
                        run_state.add_log("info", flow_index, f"Loop completed after {loop_info['iteration']} iterations in {duration:.2f}s")
                    else:
                        await run_state.emit_event("inference:completed", {
                            "flow_index": flow_index,
                            "duration": duration,
                        })
                        run_state.add_log("info", flow_index, f"Completed in {duration:.2f}s")
                    
                    # Emit progress based on unique completions
                    unique_completed = len(loop_state['unique_completed'])
                    await run_state.emit_event("execution:progress", {
                        "completed_count": unique_completed,
                        "total_count": total_inferences,
                        "cycle_count": cycle_count,
                        "loop_iterations": loop_state['total_loop_iterations'],
                    })
                    run_state.update_progress(completed=unique_completed, total=total_inferences, cycle=cycle_count)
                    
                elif new_status == 'retry':
                    retries.append(item)
                    await run_state.emit_event("inference:retry", {
                        "flow_index": flow_index,
                    })
                    run_state.add_log("warning", flow_index, f"Needs retry")
                elif new_status == 'pending':
                    # Looping sequences return 'pending' when iteration is ongoing
                    # Track loop state
                    if flow_index not in loop_state['active_loops']:
                        loop_state['active_loops'][flow_index] = {
                            'iteration': 1,
                            'started_at': time.time(),
                            'children_completed': 0,
                        }
                    
                    iteration = loop_state['active_loops'][flow_index]['iteration']
                    loop_state['total_loop_iterations'] += 1
                    
                    await run_state.emit_event("inference:pending", {
                        "flow_index": flow_index,
                        "duration": duration,
                        "reason": "loop_iteration",
                        "iteration": iteration,
                    })
                    # Emit loop-specific progress
                    await run_state.emit_event("loop:progress", {
                        "flow_index": flow_index,
                        "iteration": iteration,
                        "duration": duration,
                    })
                    run_state.add_log("debug", flow_index, f"Loop iteration {iteration} ongoing")
                elif new_status == 'restart':
                    # Looping sequences return 'restart' when moving to next iteration
                    if flow_index in loop_state['active_loops']:
                        loop_state['active_loops'][flow_index]['iteration'] += 1
                        iteration = loop_state['active_loops'][flow_index]['iteration']
                    else:
                        loop_state['active_loops'][flow_index] = {
                            'iteration': 2,
                            'started_at': time.time(),
                            'children_completed': 0,
                        }
                        iteration = 2
                    
                    loop_state['total_loop_iterations'] += 1
                    
                    await run_state.emit_event("inference:restarted", {
                        "flow_index": flow_index,
                        "duration": duration,
                        "iteration": iteration,
                    })
                    # Emit loop-specific progress
                    await run_state.emit_event("loop:progress", {
                        "flow_index": flow_index,
                        "iteration": iteration,
                        "duration": duration,
                    })
                    run_state.add_log("debug", flow_index, f"Starting loop iteration {iteration}")
                elif new_status == 'skipped':
                    # Timing/conditional sequences can skip execution
                    await run_state.emit_event("inference:skipped", {
                        "flow_index": flow_index,
                        "duration": duration,
                    })
                    run_state.add_log("info", flow_index, f"Skipped (condition not met)")
                elif new_status == 'in_progress':
                    # Item is still being processed (e.g., waiting for user input)
                    await run_state.emit_event("inference:in_progress", {
                        "flow_index": flow_index,
                        "duration": duration,
                    })
                    run_state.add_log("debug", flow_index, f"In progress")
                else:
                    # Only truly unexpected statuses are failures
                    await run_state.emit_event("inference:failed", {
                        "flow_index": flow_index,
                        "status": new_status,
                    })
                    run_state.add_log("error", flow_index, f"Failed with status: {new_status}")
                
            except Exception as e:
                duration = time.time() - start_time
                await run_state.emit_event("inference:error", {
                    "flow_index": flow_index,
                    "error": str(e),
                    "duration": duration,
                })
                raise
            
            # Emit status changes after each inference
            await emit_status_changes()
            
            # Update and emit progress (use unique_completed to avoid
            # inflating the count with loop re-executions)
            unique_completed = len(loop_state['unique_completed'])
            run_state.update_progress(
                completed=unique_completed,
                total=total_inferences,
                cycle=cycle_count
            )
            await run_state.emit_event("execution:progress", {
                "completed_count": unique_completed,
                "total_count": total_inferences,
                "cycle_count": cycle_count,
                "current_inference": flow_index,
            })
            
            # Handle step mode - pause after completing one inference
            run_state.complete_step()
            
            # SLOW run mode: execute one inference per cycle, then break
            # This allows better UI tracking at the cost of slightly slower overall execution
            if run_state.run_mode == "slow":
                break
        
        # Progress was made if we executed any items
        progress_made = cycle_executions > 0
        return progress_made, retries
    
    # Main execution loop
    retries = []
    while bb.get_all_pending_or_in_progress_items():
        tracker.cycle_count += 1
        
        await run_state.emit_event("cycle:started", {
            "cycle": tracker.cycle_count,
        })
        
        progress_made, retries = await run_cycle_async()
        
        # Save checkpoint at the end of each cycle (same as Orchestrator.run())
        if orchestrator.checkpoint_manager:
            try:
                orchestrator.checkpoint_manager.save_state(
                    tracker.cycle_count, 
                    orchestrator, 
                    inference_count=0  # 0 marks "end of cycle" checkpoint
                )
                logging.debug(f"Checkpoint saved for cycle {tracker.cycle_count}")
            except Exception as e:
                logging.warning(f"Failed to save checkpoint for cycle {tracker.cycle_count}: {e}")
        
        await run_state.emit_event("cycle:completed", {
            "cycle": tracker.cycle_count,
            "progress_made": progress_made,
        })
        
        if not progress_made and not retries:
            logging.warning("No progress made and no retries - possible deadlock")
            break
        
        # Check max cycles
        if tracker.cycle_count >= orchestrator.max_cycles:
            logging.warning(f"Max cycles ({orchestrator.max_cycles}) reached")
            break
        
        # Small yield to allow other async operations
        await asyncio.sleep(0)
    
    # Save final checkpoint to capture completed state
    if orchestrator.checkpoint_manager:
        try:
            orchestrator.checkpoint_manager.save_state(
                tracker.cycle_count, 
                orchestrator, 
                inference_count=completed_count  # Use actual inference count
            )
            logging.info(f"Final checkpoint saved: cycle={tracker.cycle_count}, inferences={completed_count}")
        except Exception as e:
            logging.warning(f"Failed to save final checkpoint: {e}")
    
    # Get final concepts (same pattern as Orchestrator.run())
    final_concepts = [c for c in orchestrator.concept_repo.get_all_concepts() if c.is_final_concept]
    return final_concepts


async def execute_run(run_state: RunState, llm_override: Optional[str], max_cycles_override: Optional[int]):
    """Execute a run in the background with granular event emission."""
    from infra._orchest._orchestrator import Orchestrator
    
    run_state.status = "running"
    run_state.started_at = datetime.now()
    
    # Emit run started event
    await run_state.emit_event("run:started", {
        "plan_id": run_state.plan_id,
        "started_at": run_state.started_at.isoformat(),
    })
    
    # Setup run-specific logging
    cfg = get_config()
    run_dir = cfg.runs_dir / run_state.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_log_handler = setup_run_logging(run_dir, run_state.run_id)
    
    try:
        logging.info(f"=" * 60)
        logging.info(f"Starting Run: {run_state.run_id}")
        logging.info(f"Plan: {run_state.plan_id}")
        logging.info(f"Config path: {run_state.config.config_path}")
        logging.info(f"Run mode: {run_state.run_mode} ({'one inference per cycle' if run_state.run_mode == 'slow' else 'all ready per cycle'})")
        logging.info(f"=" * 60)
        
        # Load repositories (this also loads inputs.json if present)
        concept_repo, inference_repo = load_repositories(run_state.config)
        
        # Apply runtime ground_inputs if provided (overrides inputs.json values)
        if run_state.ground_inputs:
            logging.info(f"Applying {len(run_state.ground_inputs)} runtime ground_inputs")
            for name, value in run_state.ground_inputs.items():
                # Skip metadata keys
                if name.startswith('_'):
                    continue
                try:
                    if isinstance(value, dict) and 'data' in value:
                        concept_repo.add_reference(
                            name,
                            value['data'],
                            axis_names=value.get('axes')
                        )
                    else:
                        concept_repo.add_reference(name, value)
                    logging.debug(f"  Applied ground_input: {name}")
                except Exception as e:
                    logging.warning(f"  Failed to apply ground_input '{name}': {e}")
        
        # Create body with deployment tools for actual LLM runs
        body = create_body(run_state.config, llm_override, use_deployment_tools=True)
        
        logging.info(f"Run {run_state.run_id}: Using LLM '{llm_override or run_state.config.llm_model}'")
        
        # Get or create user's bench for isolated outputs
        # UserBench is keyed by user_id, not run_id
        userbench_manager = get_userbench_manager()
        userbench = userbench_manager.start_run_in_bench(
            user_id=run_state.user_id,
            run_id=run_state.run_id,
            plan_id=run_state.plan_id,
            plan_dir=run_state.config.project_dir,
        )
        
        # Write ground_inputs as inputs.json to the userbench so it reflects
        # the actual values used for this run (not the plan defaults)
        if run_state.ground_inputs:
            inputs_path = userbench.root / "inputs.json"
            try:
                with open(inputs_path, "w", encoding="utf-8") as f:
                    json.dump(run_state.ground_inputs, f, indent=2, ensure_ascii=False)
                logging.info(f"Run {run_state.run_id}: Written ground_inputs to userbench inputs.json")
            except Exception as e:
                logging.warning(f"Run {run_state.run_id}: Failed to write inputs.json to bench: {e}")
        
        # Repoint file system to userbench — the bench already contains
        # plan provisions (copied with skip_existing) plus user-uploaded files,
        # so all path resolution should happen against it, not the plan dir.
        if hasattr(body, 'file_system') and body.file_system:
            body.file_system.base_dir = str(userbench.root)
            body.file_system.set_workspace(userbench)
            
            # Subscribe to file events and broadcast them
            async def on_file_event(event):
                await run_state.emit_event("file:changed", event.to_dict())
            
            def sync_file_handler(event):
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(on_file_event(event))
                    else:
                        loop.run_until_complete(on_file_event(event))
                except Exception as e:
                    logging.debug(f"File event broadcast error: {e}")
            
            userbench_manager.subscribe_to_events(run_state.run_id, sync_file_handler)
            logging.info(f"Run {run_state.run_id}: UserBench created at {userbench.outputs_dir}")
        
        # Set run context on user input tool for client connectivity
        if hasattr(body, 'user_input') and body.user_input:
            if hasattr(body.user_input, 'set_run_context'):
                body.user_input.set_run_context(run_state.run_id, userbench)
                logging.info(f"Run {run_state.run_id}: User input tool connected")
        
        # Create orchestrator
        # Priority: request override > plan config > server default
        cfg = get_config()
        max_cycles = max_cycles_override or run_state.config.max_cycles or cfg.default_max_cycles
        
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=max_cycles,
            db_path=str(run_dir / "run.db"),
            run_id=run_state.run_id
        )
        
        run_state.orchestrator = orchestrator
        
        # Save initial run metadata for historical recovery
        save_run_metadata(run_dir / "run.db", run_state.run_id, {
            "plan_id": run_state.plan_id,
            "user_id": run_state.user_id,
            "userbench_id": run_state.userbench_id,
            "status": "running",
            "started_at": run_state.started_at.isoformat(),
            "llm_model": llm_override or run_state.config.llm_model,
            "max_cycles": max_cycles,
            "outputs_url": f"/api/userbenches/{run_state.user_id}/files/productions",
        })
        
        # Emit userbench info
        await run_state.emit_event("userbench:created", {
            "user_id": run_state.user_id,
            "userbench_id": run_state.userbench_id,
            "workspace_id": run_state.user_id,  # Compatibility
            "outputs_url": f"/api/userbenches/{run_state.user_id}/files/productions",
            "events_url": f"/api/userbenches/{run_state.user_id}/events/stream",
        })
        
        # Get total inference count for progress tracking
        total_inferences = len(list(orchestrator.waitlist.items))
        
        # Initialize progress on run_state
        run_state.update_progress(completed=0, total=total_inferences, cycle=0)
        
        # Emit initial node statuses (all pending)
        initial_statuses = {}
        for item in orchestrator.waitlist.items:
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            if flow_index:
                initial_statuses[flow_index] = 'pending'
                run_state.set_node_status(flow_index, 'pending')
        
        await run_state.emit_event("node:statuses", {
            "statuses": initial_statuses,
            "total_count": total_inferences,
        })
        
        # Run with event emission using cycle-based approach
        final_concepts = await execute_run_with_events(run_state, orchestrator, total_inferences)
        
        # Collect results
        run_state.result = {
            "run_id": run_state.run_id,
            "plan_id": run_state.plan_id,
            "status": "completed",
            "final_concepts": []
        }
        
        for fc in final_concepts:
            concept_result = {
                "name": fc.concept_name,
                "has_value": False
            }
            
            # Try to get reference data from multiple sources
            ref_data = None
            ref_shape = None
            ref_axes = None
            
            # Source 1: concept.reference (if hydrated)
            if fc.concept and fc.concept.reference:
                ref_data = fc.concept.reference.tensor  # .tensor returns .data
                ref_shape = list(fc.concept.reference.shape)
                ref_axes = list(fc.concept.reference.axes) if fc.concept.reference.axes else None
            
            # Source 2: reference_data on the entry (from checkpoint restoration)
            if ref_data is None and fc.reference_data is not None:
                ref_data = fc.reference_data
                ref_axes = fc.reference_axis_names
                # Calculate shape from data
                if isinstance(ref_data, list):
                    shape = []
                    current = ref_data
                    while isinstance(current, list):
                        shape.append(len(current))
                        if current:
                            current = current[0]
                        else:
                            break
                    ref_shape = shape
            
            if ref_data is not None:
                concept_result["has_value"] = True
                if ref_shape:
                    concept_result["shape"] = ref_shape
                if ref_axes:
                    concept_result["axes"] = ref_axes
                
                # Sanitize data to remove binary fields before serialization
                sanitized_data = sanitize_for_serialization(ref_data)
                
                # Use JSON serialization for proper frontend parsing
                try:
                    data_str = json.dumps(sanitized_data, ensure_ascii=False)
                except (TypeError, ValueError):
                    # Fallback to string representation for non-JSON-serializable data
                    data_str = str(sanitized_data)
                
                if len(data_str) > 10000:  # Increased limit for full data visibility
                    data_str = data_str[:9997] + "..."
                concept_result["value"] = data_str
            
            run_state.result["final_concepts"].append(concept_result)
        
        run_state.status = "completed"
        run_state.completed_at = datetime.now()
        
        # Update metadata to completed
        save_run_metadata(run_dir / "run.db", run_state.run_id, {
            "plan_id": run_state.plan_id,
            "status": "completed",
            "started_at": run_state.started_at.isoformat(),
            "completed_at": run_state.completed_at.isoformat(),
            "llm_model": llm_override or run_state.config.llm_model,
        })
        
        # Notify websocket subscribers
        await broadcast_event(run_state.run_id, {
            "event": "run:completed",
            "run_id": run_state.run_id,
            "result": run_state.result
        })
        
    except Exception as e:
        logging.exception(f"Run {run_state.run_id} failed: {e}")
        run_state.status = "failed"
        run_state.error = str(e)
        run_state.completed_at = datetime.now()
        
        # Update metadata to failed
        save_run_metadata(run_dir / "run.db", run_state.run_id, {
            "plan_id": run_state.plan_id,
            "status": "failed",
            "started_at": run_state.started_at.isoformat() if run_state.started_at else None,
            "completed_at": run_state.completed_at.isoformat(),
            "error": str(e),
        })
        
        await broadcast_event(run_state.run_id, {
            "event": "run:failed",
            "run_id": run_state.run_id,
            "error": str(e)
        })
    finally:
        # Clean up run-specific logging handler
        if run_log_handler:
            logging.info(f"Run {run_state.run_id} log file saved to: {run_dir}")
            run_log_handler.close()
            logging.getLogger().removeHandler(run_log_handler)


async def execute_run_with_resume(run_state: RunState, llm_override: Optional[str], max_cycles_override: Optional[int]):
    """Execute a run resumed from a checkpoint."""
    from infra._orchest._orchestrator import Orchestrator
    
    run_state.status = "running"
    run_state.started_at = datetime.now()
    
    resume_info = getattr(run_state, '_resume_from', None)
    if not resume_info:
        run_state.status = "failed"
        run_state.error = "No resume info available"
        return
    
    cfg = get_config()
    run_dir = cfg.runs_dir / run_state.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_log_handler = setup_run_logging(run_dir, run_state.run_id)
    
    try:
        logging.info(f"=" * 60)
        logging.info(f"Resuming Run: {run_state.run_id}")
        logging.info(f"From: {resume_info['original_run_id']} cycle={resume_info['cycle']}")
        logging.info(f"Plan: {run_state.plan_id}")
        logging.info(f"=" * 60)
        
        # Load repositories (this also loads inputs.json if present)
        concept_repo, inference_repo = load_repositories(run_state.config)
        
        # Apply runtime ground_inputs if provided (overrides inputs.json values)
        if run_state.ground_inputs:
            logging.info(f"Applying {len(run_state.ground_inputs)} runtime ground_inputs for resumed run")
            for name, value in run_state.ground_inputs.items():
                if name.startswith('_'):
                    continue
                try:
                    if isinstance(value, dict) and 'data' in value:
                        concept_repo.add_reference(
                            name,
                            value['data'],
                            axis_names=value.get('axes')
                        )
                    else:
                        concept_repo.add_reference(name, value)
                except Exception as e:
                    logging.warning(f"  Failed to apply ground_input '{name}': {e}")
        
        # Create body
        body = create_body(run_state.config, llm_override, use_deployment_tools=True)
        
        # Priority: request override > plan config > server default
        cfg = get_config()
        max_cycles = max_cycles_override or run_state.config.max_cycles or cfg.default_max_cycles
        
        # Create orchestrator with resume
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=max_cycles,
            db_path=str(run_dir / "run.db"),
            run_id=run_state.run_id,
        )
        
        run_state.orchestrator = orchestrator
        
        # Save initial run metadata for historical recovery
        save_run_metadata(run_dir / "run.db", run_state.run_id, {
            "plan_id": run_state.plan_id,
            "status": "running",
            "started_at": run_state.started_at.isoformat(),
            "llm_model": llm_override or run_state.config.llm_model,
            "max_cycles": max_cycles,
            "resumed_from": resume_info['original_run_id'],
            "resumed_cycle": resume_info['cycle'],
        })
        
        # Resume from checkpoint
        orchestrator.resume_from_checkpoint(
            db_path=resume_info['db_path'],
            run_id=resume_info['original_run_id'],
            cycle=resume_info['cycle'],
            inference_count=resume_info['inference_count'],
        )
        
        # Run
        final_concepts = await orchestrator.run_async()
        
        # Collect results (same as execute_run)
        run_state.result = {
            "run_id": run_state.run_id,
            "plan_id": run_state.plan_id,
            "status": "completed",
            "resumed_from": resume_info,
            "final_concepts": []
        }
        
        for fc in final_concepts:
            concept_result = {"name": fc.concept_name, "has_value": False}
            
            # Try to get reference data from multiple sources
            ref_data = None
            ref_shape = None
            ref_axes = None
            
            if fc.concept and fc.concept.reference:
                ref_data = fc.concept.reference.tensor
                ref_shape = list(fc.concept.reference.shape)
                ref_axes = list(fc.concept.reference.axes) if fc.concept.reference.axes else None
            
            if ref_data is None and fc.reference_data is not None:
                ref_data = fc.reference_data
                ref_axes = fc.reference_axis_names
                if isinstance(ref_data, list):
                    shape = []
                    current = ref_data
                    while isinstance(current, list):
                        shape.append(len(current))
                        if current:
                            current = current[0]
                        else:
                            break
                    ref_shape = shape
            
            if ref_data is not None:
                concept_result["has_value"] = True
                if ref_shape:
                    concept_result["shape"] = ref_shape
                if ref_axes:
                    concept_result["axes"] = ref_axes
                try:
                    data_str = json.dumps(ref_data)
                except (TypeError, ValueError):
                    data_str = str(ref_data)
                if len(data_str) > 10000:
                    data_str = data_str[:9997] + "..."
                concept_result["value"] = data_str
            
            run_state.result["final_concepts"].append(concept_result)
        
        run_state.status = "completed"
        run_state.completed_at = datetime.now()
        
        # Update metadata to completed
        save_run_metadata(run_dir / "run.db", run_state.run_id, {
            "plan_id": run_state.plan_id,
            "status": "completed",
            "started_at": run_state.started_at.isoformat(),
            "completed_at": run_state.completed_at.isoformat(),
            "llm_model": llm_override or run_state.config.llm_model,
            "resumed_from": resume_info['original_run_id'],
        })
        
        await broadcast_event(run_state.run_id, {
            "event": "run:completed",
            "run_id": run_state.run_id,
            "result": run_state.result
        })
        
    except Exception as e:
        logging.exception(f"Resumed run {run_state.run_id} failed: {e}")
        run_state.status = "failed"
        run_state.error = str(e)
        run_state.completed_at = datetime.now()
        
        # Update metadata to failed
        save_run_metadata(run_dir / "run.db", run_state.run_id, {
            "plan_id": run_state.plan_id,
            "status": "failed",
            "started_at": run_state.started_at.isoformat() if run_state.started_at else None,
            "completed_at": run_state.completed_at.isoformat(),
            "error": str(e),
            "resumed_from": resume_info.get('original_run_id') if resume_info else None,
        })
        
        await broadcast_event(run_state.run_id, {
            "event": "run:failed",
            "run_id": run_state.run_id,
            "error": str(e)
        })
    finally:
        if run_log_handler:
            logging.info(f"Run {run_state.run_id} log file saved to: {run_dir}")
            run_log_handler.close()
            logging.getLogger().removeHandler(run_log_handler)

