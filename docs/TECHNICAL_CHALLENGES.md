# Technical Challenges Faced

## Multi-Worker Memory Split (SSE Event Void)

**The Symptom:** 
When viewing the Dashboard, the Server-Sent Events (SSE) notification stream for newly sent emails would randomly drop 75% of incoming events. 

**The Architecture:** 
The FastAPI backend runs behind Gunicorn/Uvicorn with `--workers 4` to handle concurrent connections and DAG processing. I initially stored SSE subscriber queues in an in-memory Python list.

**The Root Cause:** 
The 4 worker processes operate in completely isolated memory spaces. When a user opens the UI, their browser's SSE connection binds to exactly one of the four workers. However, when a DAG spawns 10 parallel jobs, the PostgreSQL database distributes those jobs across all 4 workers. If Worker #2 processes the email job, it broadcasts the notification to its *own* local memory list. If the user's browser is connected to Worker #1, the event fires into the void.

**The Solution:** 
I replaced the in-memory Python list with a **PostgreSQL `LISTEN/NOTIFY` Pub/Sub architecture**. I tied a `pg_notify` trigger directly to the database transaction that persists the email. Now, all 4 workers run a background `asyncpg` listener loop. When any worker processes an email, the database blasts the event to all 4 workers simultaneously across the IPC barrier, guaranteeing 100% notification delivery regardless of which worker the browser is connected to.

I deliberately chose PostgreSQL over Redis for this pub/sub mechanism for two crucial architectural reasons:
1. **Transactional Integrity**: `pg_notify` respects transaction boundaries. The notification is only broadcast if the transaction that saves the email successfully commits. With Redis, I would have risked a "dual-write" race condition where an event fires, but the database transaction rolls back, sending false notifications to the UI.
2. **Infrastructure Complexity**: I was already running a highly optimized PostgreSQL instance. Introducing Redis would mean provisioning, monitoring, and securing an entirely new infrastructural component just for low-volume administrative UI alerts. Keeping the stack lean significantly reduced the operational burden.

---

## 1-Second UI Freeze (Nginx Keep-Alive Teardown)

**The Symptom:** 
After deploying the DAG upgrade, clicking between UI components (Dashboard, Jobs, DLQ) caused the browser to "hang" for a full second before the data loaded, making the application feel extremely sluggish.

**The Root Cause:** 
While attempting to optimize Nginx to support long-lived SSE streams, I globally disabled chunked transfer encoding (`chunked_transfer_encoding off;`) for the `/api` route. 
Simultaneously, Nginx was configured to use `gzip` compression. When Nginx compresses a JSON payload, the original `Content-Length` header is invalidated and stripped. Normally, Nginx replaces it with `Transfer-Encoding: chunked` so the browser knows how to parse the dynamic stream. 
Because I strictly forbade chunking, the browser received an HTTP/1.1 response with **no length indicator**. The HTTP specification dictates that under these conditions, the browser must wait until the server physically closes the TCP connection to know the file is complete. This caused a heavy 1-second delay as the browser waited for connection teardown timeouts.

**The Solution:** 
I wrote a sed-scrubbing script into my GitHub Actions CI/CD pipeline to surgically remove the `chunked_transfer_encoding off;` directive from the production Nginx config, immediately restoring sub-millisecond API responses while preserving SSE integrity.

---

## Silent Retries (Shadowed Variables & Transaction Boundaries)

**The Symptom:** 
The UI was successfully receiving notifications, but it was receiving exactly 3 identical notifications for every 1 email sent.

**The Root Cause:** 
During the implementation of the Postgres `pg_notify` fix, I accidentally shadowed a function parameter (`payload`) with a local JSON string variable containing the notification payload.
1. The system executed the `pg_notify` database command flawlessly.
2. On the very next line, the system attempted to log the recipient using `payload["to"]`.
3. Because `payload` was now a string instead of a dictionary, Python threw a `TypeError: string indices must be integers`.
4. The background worker gracefully caught the exception, marked the job as `FAILED`, incremented the retry counter, and **committed the database transaction**.
5. Because the transaction committed, Postgres successfully broadcasted the `pg_notify` event to the UI.
6. The worker then immediately picked the job back up for a retry, failed again on the exact same log line, and broadcasted a second notification.
7. Because the system is configured with `max_retries = 3`, it performed this loop exactly 3 times before finally moving the job to the Dead Letter Queue.

**The Solution:** 
I renamed the shadowed variable to `notify_payload` to preserve the original dictionary structure, preventing the `TypeError` and breaking the silent retry loop.
