#!/usr/bin/env python3
"""
Queue Management System for GPU Server Jobs

Manages 3 independent queue types for both Upscale and Cut jobs:
- Download Queue: Downloads files sequentially (1 concurrent)
- Processing Queue: GPU processing with limits (2 concurrent for upscale, 1 for cut)  
- Upload Queue: Uploads results sequentially (1 concurrent)
"""

import threading
import queue
import time
import logging
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class JobType(Enum):
    UPSCALE = "upscale"
    CUT = "cut"

class QueueType(Enum):
    DOWNLOAD = "download"
    PROCESS = "process" 
    UPLOAD = "upload"

@dataclass
class QueuedJob:
    job_id: int
    job_type: JobType
    stage: QueueType
    data: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None

class WorkerQueue:
    """A queue with worker threads that process jobs."""
    
    def __init__(self, name: str, max_workers: int = 1):
        self.name = name
        self.max_workers = max_workers
        self.queue = queue.Queue()
        self.workers = []
        self.running = False
        self.stats = {
            'processed': 0,
            'errors': 0,
            'active_workers': 0
        }
        
    def start(self, worker_func: Callable[[QueuedJob], bool]):
        """Start worker threads."""
        if self.running:
            return
            
        self.running = True
        self.worker_func = worker_func
        
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"{self.name}-worker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            
        logger.info(f"Started {self.max_workers} workers for queue '{self.name}'")
    
    def stop(self):
        """Stop all workers."""
        self.running = False
        
        # Add poison pills to wake up workers
        for _ in range(self.max_workers):
            self.queue.put(None)
            
    def put(self, job: QueuedJob):
        """Add a job to the queue."""
        self.queue.put(job)
        logger.debug(f"Added job {job.job_id} to queue '{self.name}'")
        
    def _worker_loop(self):
        """Main worker loop."""
        while self.running:
            try:
                job = self.queue.get(timeout=1.0)
                if job is None:  # Poison pill
                    break
                    
                self.stats['active_workers'] += 1
                job.started_at = time.time()
                
                try:
                    success = self.worker_func(job)
                    if success:
                        job.completed_at = time.time()
                        self.stats['processed'] += 1
                    else:
                        self.stats['errors'] += 1
                        
                except Exception as e:
                    job.error = str(e)
                    self.stats['errors'] += 1
                    logger.error(f"Worker error processing job {job.job_id}: {e}")
                    
                finally:
                    self.stats['active_workers'] -= 1
                    self.queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker loop error: {e}")

class QueueManager:
    """Main queue manager coordinating all job processing."""
    
    def __init__(self):
        # Create queues with different concurrency limits
        self.queues = {
            # Upscale queues
            (JobType.UPSCALE, QueueType.DOWNLOAD): WorkerQueue("upscale-download", 1),
            (JobType.UPSCALE, QueueType.PROCESS): WorkerQueue("upscale-process", 2), 
            (JobType.UPSCALE, QueueType.UPLOAD): WorkerQueue("upscale-upload", 1),
            
            # Cut queues  
            (JobType.CUT, QueueType.DOWNLOAD): WorkerQueue("cut-download", 1),
            (JobType.CUT, QueueType.PROCESS): WorkerQueue("cut-process", 1),
            (JobType.CUT, QueueType.UPLOAD): WorkerQueue("cut-upload", 1),
        }
        
        # Job storage and callbacks
        self.jobs: Dict[int, QueuedJob] = {}
        self.callbacks: Dict[tuple, Callable] = {}
        self.next_stage: Dict[tuple, QueueType] = {
            # Stage progression
            (JobType.UPSCALE, QueueType.DOWNLOAD): QueueType.PROCESS,
            (JobType.UPSCALE, QueueType.PROCESS): QueueType.UPLOAD,
            
            (JobType.CUT, QueueType.DOWNLOAD): QueueType.PROCESS,
            (JobType.CUT, QueueType.PROCESS): QueueType.UPLOAD,
        }
        
    def start(self):
        """Start all queue workers."""
        # Register worker functions
        self.queues[(JobType.UPSCALE, QueueType.DOWNLOAD)].start(self._upscale_download_worker)
        self.queues[(JobType.UPSCALE, QueueType.PROCESS)].start(self._upscale_process_worker)
        self.queues[(JobType.UPSCALE, QueueType.UPLOAD)].start(self._upscale_upload_worker)
        
        self.queues[(JobType.CUT, QueueType.DOWNLOAD)].start(self._cut_download_worker)
        self.queues[(JobType.CUT, QueueType.PROCESS)].start(self._cut_process_worker)
        self.queues[(JobType.CUT, QueueType.UPLOAD)].start(self._cut_upload_worker)
        
        logger.info("Queue manager started")
        
    def stop(self):
        """Stop all queue workers."""
        for q in self.queues.values():
            q.stop()
        logger.info("Queue manager stopped")
        
    def submit_job(self, job_id: int, job_type: JobType, data: Dict[str, Any]) -> QueuedJob:
        """Submit a new job starting with download stage."""
        job = QueuedJob(
            job_id=job_id,
            job_type=job_type, 
            stage=QueueType.DOWNLOAD,
            data=data
        )
        
        self.jobs[job_id] = job
        self.queues[(job_type, QueueType.DOWNLOAD)].put(job)
        
        logger.info(f"Submitted {job_type.value} job {job_id} to download queue")
        return job
        
    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get current status of a job."""
        job = self.jobs.get(job_id)
        if not job:
            return None
            
        status = {
            'job_id': job_id,
            'type': job.job_type.value,
            'stage': job.stage.value,
            'created_at': job.created_at,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
        }
        
        if job.error:
            status['error'] = job.error
            status['status'] = 'failed'
        elif job.completed_at and job.stage == QueueType.UPLOAD:
            status['status'] = 'completed'
        elif job.started_at:
            status['status'] = 'processing'
        else:
            status['status'] = 'queued'
            
        return status
        
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues."""
        stats = {}
        for (job_type, queue_type), q in self.queues.items():
            key = f"{job_type.value}_{queue_type.value}"
            stats[key] = {
                'queue_size': q.queue.qsize(),
                'active_workers': q.stats['active_workers'],
                'max_workers': q.max_workers,
                'processed': q.stats['processed'],
                'errors': q.stats['errors']
            }
        return stats
        
    def _advance_to_next_stage(self, job: QueuedJob) -> bool:
        """Move job to next stage in pipeline."""
        next_stage = self.next_stage.get((job.job_type, job.stage))
        if not next_stage:
            # Job completed all stages
            logger.info(f"Job {job.job_id} completed all stages")
            return True
            
        job.stage = next_stage
        job.started_at = None  # Reset for next stage
        
        self.queues[(job.job_type, next_stage)].put(job)
        logger.debug(f"Advanced job {job.job_id} to {next_stage.value} stage")
        return True
        
    def register_callback(self, job_type: JobType, stage: QueueType, callback: Callable):
        """Register callback function for a specific stage."""
        self.callbacks[(job_type, stage)] = callback
        
    # Worker functions - these call the registered callbacks
    def _upscale_download_worker(self, job: QueuedJob) -> bool:
        callback = self.callbacks.get((JobType.UPSCALE, QueueType.DOWNLOAD))
        if callback:
            success = callback(job)
            if success:
                return self._advance_to_next_stage(job)
            return False
        return False
        
    def _upscale_process_worker(self, job: QueuedJob) -> bool:
        callback = self.callbacks.get((JobType.UPSCALE, QueueType.PROCESS))
        if callback:
            success = callback(job)
            if success:
                return self._advance_to_next_stage(job)
            return False
        return False
        
    def _upscale_upload_worker(self, job: QueuedJob) -> bool:
        callback = self.callbacks.get((JobType.UPSCALE, QueueType.UPLOAD))
        if callback:
            return callback(job)
        return False
        
    def _cut_download_worker(self, job: QueuedJob) -> bool:
        callback = self.callbacks.get((JobType.CUT, QueueType.DOWNLOAD))
        if callback:
            success = callback(job)
            if success:
                return self._advance_to_next_stage(job)
            return False
        return False
        
    def _cut_process_worker(self, job: QueuedJob) -> bool:
        callback = self.callbacks.get((JobType.CUT, QueueType.PROCESS))
        if callback:
            success = callback(job)
            if success:
                return self._advance_to_next_stage(job)
            return False
        return False
        
    def _cut_upload_worker(self, job: QueuedJob) -> bool:
        callback = self.callbacks.get((JobType.CUT, QueueType.UPLOAD))
        if callback:
            return callback(job)
        return False

# Global queue manager instance
queue_manager = QueueManager()