"""Controlled JSON Artifact exchange. Workers receive content, never arbitrary paths."""
import hashlib
import json
import os
import tempfile
from pathlib import Path
from .router import uid, now


class ArtifactStore:
    def __init__(self, root):
        self.root=Path(root).resolve()
        self.root.mkdir(parents=True,exist_ok=True)

    def write_content(self, execution_key, content):
        encoded=json.dumps(content,ensure_ascii=False,sort_keys=True).encode('utf-8')
        digest=hashlib.sha256(encoded).hexdigest()
        name=hashlib.sha256(execution_key.encode()).hexdigest()+'.json'
        destination=self.root/name
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:
                raise ValueError('execution key produced conflicting content')
            return name,digest
        fd,temp=tempfile.mkstemp(prefix='pending-',dir=self.root)
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp,destination)
        finally:
            if os.path.exists(temp): os.unlink(temp)
        return name,digest

    def read(self,con,artifact_id,task_id,project_id,user_id=None):
        row=con.execute('SELECT * FROM artifacts WHERE id=? AND task_id=? AND project_id=?',
                        (artifact_id,task_id,project_id)).fetchone()
        if row is None: raise PermissionError('artifact not in this task/project')
        if user_id and con.execute('SELECT 1 FROM projects WHERE id=? AND owner_user_id=?',(project_id,user_id)).fetchone() is None:
            raise PermissionError('artifact not owned by user')
        path=(self.root/row['storage_uri']).resolve()
        if path.parent!=self.root: raise PermissionError('artifact outside controlled root')
        content=path.read_bytes()
        if hashlib.sha256(content).hexdigest()!=row['sha256']: raise ValueError('artifact hash mismatch')
        return json.loads(content)

    def publish(self,con,run,project_id,content,kind='test_worker_result'):
        name,digest=self.write_content(run['execution_key'],content)
        artifact_id=uid('artifact')
        con.execute('''INSERT INTO artifacts(id,task_id,project_id,kind,storage_uri,sha256,plan_version,
            created_by,validation_status,created_at) VALUES(?,?,?,?,?,?,?,?,'validated',?)''',
            (artifact_id,run['task_id'],project_id,kind,name,digest,run['plan_version'],run['session_id'],now().isoformat()))
        con.execute("INSERT INTO artifact_links VALUES(?,?,'output')",(run['id'],artifact_id))
        return artifact_id
