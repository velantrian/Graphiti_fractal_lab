// Minimal Experience schema (Neo4j 5)

// Uniqueness constraints
CREATE CONSTRAINT taskrun_uuid_unique IF NOT EXISTS
FOR (n:TaskRun)
REQUIRE n.uuid IS UNIQUE;

CREATE CONSTRAINT toolcall_uuid_unique IF NOT EXISTS
FOR (n:ToolCall)
REQUIRE n.uuid IS UNIQUE;

CREATE CONSTRAINT testrun_uuid_unique IF NOT EXISTS
FOR (n:TestRun)
REQUIRE n.uuid IS UNIQUE;

CREATE CONSTRAINT errorevent_uuid_unique IF NOT EXISTS
FOR (n:ErrorEvent)
REQUIRE n.uuid IS UNIQUE;

// Range indexes (filtering)
CREATE INDEX taskrun_status IF NOT EXISTS
FOR (n:TaskRun)
ON (n.status);

CREATE INDEX taskrun_task_type IF NOT EXISTS
FOR (n:TaskRun)
ON (n.task_type);

CREATE INDEX taskrun_context_hash IF NOT EXISTS
FOR (n:TaskRun)
ON (n.context_hash);

CREATE INDEX taskrun_started_at IF NOT EXISTS
FOR (n:TaskRun)
ON (n.started_at);

// Common labels used for linking (optional)
CREATE INDEX file_path IF NOT EXISTS
FOR (n:File)
ON (n.path);

CREATE INDEX project_name IF NOT EXISTS
FOR (n:Project)
ON (n.name);


