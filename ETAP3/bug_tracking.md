# Bug Tracking Log - Vehicle Monitoring System

This document serves as the local Issue Tracker/Bug Tracking log for the project, satisfying the requirement to report bugs detected during test cycles.

---

## BUG-01: Missing Threshold Alert Generation Logic

* **ID**: BUG-01
* **Severity**: High
* **Component**: Backend API / Database
* **Requirements Reference**: FR-08
* **Status**: Resolved
* **Description**: The endpoint `POST /sessions/{session_id}/readings/collect` retrieves sensor readings from OBD and external sensor interfaces but does not check them against defined safety thresholds. As a result, no threshold alerts are generated or recorded in the `alerts` database table.
* **Impact**: Critical system functionality of alert notification is broken.
* **Fix Target**: Implement a rule engine/utility to check readings against threshold limits and insert matching `Alert` records when collecting data.
* **Fix details**: Implemented threshold rule checking in `backend/database/alerts.py` and integrated it into `collect_readings` to evaluate sensor data against warning/critical thresholds and generate database alerts in the same transaction.

---

## BUG-02: Event Logging to Database Not Implemented

* **ID**: BUG-02
* **Severity**: Medium
* **Component**: Backend API / Database
* **Requirements Reference**: FR-13
* **Status**: Resolved
* **Description**: The FastAPI router has a GET endpoint `/logs` to query the `event_logs` table, but the backend application never actually inserts any logs into the `event_logs` table. Only standard python console/file logger is used.
* **Impact**: Operative events like starting/stopping sessions or raising alerts are not recorded in the DB for administrator view, violating observability requirements.
* **Fix Target**: Implement a database logging helper function and invoke it when starting/stopping sessions, when an alert is generated, and on critical system events.
* **Fix details**: Implemented database-backed logging in `backend/database/logging_db.py` supporting transaction coordination. Integrated it across all critical endpoints (`create_session`, `stop_session`, `collect_readings`) and within the threshold alert checking logic.

---


## BUG-03: Performance Bottleneck in DB Session Commits (Identified in Profiling)

* **ID**: BUG-03
* **Severity**: Medium (Performance)
* **Component**: Backend Database Connection
* **Requirements Reference**: NFR-01 (Latency < 2s), NFR-02 (20+ parameters)
* **Status**: Resolved
* **Description**: In the collection loop, we perform database commits and object refreshes for each reading individually. With 20+ parameters or high-frequency telemetry, committing one-by-one is highly inefficient and creates database lock contention or slow response times.
* **Impact**: Unnecessary I/O overhead.
* **Fix Target**: Refactor database inserts to use bulk inserts or perform a single commit at the end of the transaction.
* **Fix details**: Optimized session commit flow (single commit per cycle, removed slow row-by-row `db.refresh` calls). Set `expire_on_commit=False` in `SessionLocal` to prevent SQLAlchemy from invalidating instances in memory (preventing lazy SELECTs). Created database indexes (`index=True`) on foreign keys (`session_id`), parameters (`parameter`), levels, and timestamps across `SensorReading`, `Alert`, and `EventLog` tables to guarantee fast queries.

---

## BUG-04: Invalid PyPI package name in requirements.txt

* **ID**: BUG-04
* **Severity**: Medium
* **Component**: Deployment / Setup
* **Requirements Reference**: NFR-10 (Portability / Setup)
* **Status**: Resolved
* **Description**: The `requirements.txt` file specifies `python-obd>=0.7.2`. However, the package name on PyPI is `obd`. This causes the virtual environment installation command (`pip install -r requirements.txt`) to fail with "Could not find a version that satisfies the requirement python-obd".
* **Impact**: Prevents setting up the application environment and running the program.
* **Fix Target**: Update `requirements.txt` to reference `obd>=0.7.2` instead of `python-obd>=0.7.2`.

