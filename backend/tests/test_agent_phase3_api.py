import asyncio
import httpx
import unittest
import test_agent_phase2_api as fixture
from backend.app import main
from backend.app.agent.migration_v4 import migrate_runtime_schema
from backend.app.scientific import research_store as store


class RuntimeApiTests(unittest.TestCase):
    tearDown=fixture.AgentApiTests.tearDown
    def setUp(self):
        fixture.AgentApiTests.setUp(self)
        with store.connect() as con: migrate_runtime_schema(con)

    def test_plan_approval_and_cancellation_are_scoped(self):
        if hasattr(asyncio,'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        async def scenario():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),base_url='http://test') as client:
                client.cookies.set('soilmate_session','session-one-token-123456789012345')
                headers={'X-CSRF-Token':'csrf-1'}
                created=await client.post('/api/agent/messages',json={'text':'帮我分析这份数据','project_id':'p1'},headers=headers)
                task=created.json()['task_id']
                planned=await client.post(f'/api/agent/tasks/{task}/plans',headers=headers,json={
                    'goal':'test','steps':[{'name':'a','role':'data_worker'}]})
                self.assertEqual(planned.status_code,200,planned.text)
                approved=await client.post(f'/api/agent/tasks/{task}/approve',headers=headers,json={'plan_version':1})
                self.assertEqual(approved.status_code,200)
                roles=await client.get('/api/agent/workers')
                self.assertEqual(len(roles.json()),6)
                client.cookies.set('soilmate_session','session-two-token-123456789012345')
                denied=await client.post(f'/api/agent/tasks/{task}/cancel',headers={'X-CSRF-Token':'csrf-2'})
                self.assertEqual(denied.status_code,404)
                client.cookies.set('soilmate_session','session-one-token-123456789012345')
                cancelled=await client.post(f'/api/agent/tasks/{task}/cancel',headers=headers)
                self.assertEqual(cancelled.status_code,200)
        asyncio.run(scenario())
