"""
Patch for app/worker.py - добавить таймауты в upload_upscale_worker
Заменить код между строками 646-668 на этот:
"""

def upload_upscale_worker_with_timeout():
    vast = get_vast()
    while not stop_event.is_set():
        try:
            task_id = upload_upscale_queue.get(timeout=0.5)
        except Empty:
            _stop_instance_if_fully_idle()
            continue
        with Session(engine) as session:
            ut = session.get(UpscaleTask, task_id)
            if not ut:
                upload_upscale_queue.task_done()
                continue
            try:
                # Ensure instance with timeout
                ut.stage = "ensuring_instance"
                ut.progress = 5
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()

                # Add timeout for instance creation
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError("VAST instance creation timeout")
                
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(300)  # 5 minute timeout
                
                try:
                    inst = vast.ensure_instance_running()
                    ut.vast_instance_id = str(inst.get("id"))
                    session.add(ut)
                    session.commit()
                finally:
                    signal.alarm(0)  # Cancel timeout

                # Sequential upload with timeout
                ut.stage = "uploading"
                ut.progress = 20
                session.add(ut)
                session.commit()
                
                _upload_sem.acquire()
                try:
                    # Add timeout for upload
                    signal.alarm(1800)  # 30 minute timeout for upload
                    try:
                        remote_in, remote_out = vast.upload_and_plan_paths(inst, ut.file_path)
                    finally:
                        signal.alarm(0)
                finally:
                    _upload_sem.release()

                # Store remote paths and enqueue for GPU processing
                with _remote_lock:
                    _remote_paths[task_id] = (remote_in, remote_out)
                ut.stage = "queued_gpu"
                ut.progress = 35
                ut.updated_at = time_utc()
                ut.status = UpscaleStatus.QUEUED
                session.add(ut)
                session.commit()
                process_upscale_queue.put(task_id)
                
            except TimeoutError as e:
                ut.status = UpscaleStatus.ERROR
                ut.stage = "error"
                ut.error = f"Timeout: {str(e)}"
                ut.updated_at = time_utc()
                session.add(ut)
                session.commit()
            except Exception as e:
                # Existing error handling...
                msg = str(e)
                if "still writing" in msg or "appears to be still writing" in msg:
                    try:
                        ut.stage = "queued"
                        ut.status = UpscaleStatus.QUEUED
                        ut.progress = 5
                        ut.error = None
                        ut.updated_at = time_utc()
                        session.add(ut)
                        session.commit()
                    except Exception:
                        pass
                    time.sleep(1.0)
                    upload_upscale_queue.put(task_id)
                else:
                    ut.status = UpscaleStatus.ERROR
                    ut.stage = "error"
                    ut.error = str(e)
                    ut.updated_at = time_utc()
                    session.add(ut)
                    session.commit()
            finally:
                upload_upscale_queue.task_done()