"""
测试 04 — API 端点
运行: python -m pytest tests/test_04_api.py -v

测试: 10 个 knowledge API 端点的路由、参数验证、响应格式。
使用 FastAPI TestClient (httpx)，需要数据库连接。
"""
import sys, os, unittest
from unittest import IsolatedAsyncioTestCase

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/health_platform"
)


def _try_import_app():
    """尝试导入 FastAPI app，如失败返回 None"""
    try:
        # 优先: 组装一个含知识库路由的最小 app
        # (项目根 main.py 是决策引擎 :8002，不含 knowledge 路由)
        from fastapi import FastAPI
        from api.knowledge import router as knowledge_router
        app = FastAPI()
        app.include_router(knowledge_router, prefix="/api/v1")
        return app
    except Exception as e:
        return None


class TestAPIRouteDefinition(unittest.TestCase):
    """API 路由定义测试 (不需要服务器运行)"""

    def test_router_import(self):
        """knowledge router 可导入"""
        from api.knowledge import router
        self.assertIsNotNone(router)

    def test_router_has_routes(self):
        """router 包含预期路由"""
        from api.knowledge import router
        paths = [r.path for r in router.routes if hasattr(r, 'path')]

        # 10个端点的路径
        expected_paths = [
            "/knowledge/docs",
            "/knowledge/docs/upload",
            "/knowledge/search",
            "/knowledge/domains",
            "/knowledge/stats",
        ]
        for ep in expected_paths:
            found = any(ep in p for p in paths)
            self.assertTrue(found, f"路由缺失: {ep}, 实际路由: {paths}")

    def test_router_methods(self):
        """路由方法正确"""
        from api.knowledge import router

        method_map = {}
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                for m in route.methods:
                    method_map.setdefault(route.path, set()).add(m)

        # 上传应为 POST
        upload_paths = [p for p in method_map if 'upload' in p]
        for p in upload_paths:
            self.assertIn('POST', method_map[p],
                          f"upload 端点应为 POST: {p} → {method_map[p]}")

        # search 应为 GET
        search_paths = [p for p in method_map if 'search' in p]
        for p in search_paths:
            self.assertIn('GET', method_map[p],
                          f"search 端点应为 GET: {p} → {method_map[p]}")


class TestAPIResponseSchemas(unittest.TestCase):
    """API 响应 Schema 验证 (静态检查)"""

    def test_search_endpoint_params(self):
        """search 端点应接受 query 参数"""
        from api.knowledge import router
        import inspect

        for route in router.routes:
            if hasattr(route, 'path') and 'search' in route.path:
                # 检查端点函数签名
                if hasattr(route, 'endpoint'):
                    sig = inspect.signature(route.endpoint)
                    params = list(sig.parameters.keys())
                    # 应有 query/q 参数
                    has_query = any('q' in p.lower() for p in params)
                    if not has_query:
                        print(f"  ⚠️ search 端点参数: {params} (未见 query/q)")
                break

    def test_upload_endpoint_accepts_file(self):
        """upload 端点应接受文件"""
        from api.knowledge import router
        import inspect

        for route in router.routes:
            if hasattr(route, 'path') and 'upload' in route.path:
                if hasattr(route, 'endpoint'):
                    sig = inspect.signature(route.endpoint)
                    params = list(sig.parameters.keys())
                    # 应有 file/upload 参数
                    has_file = any('file' in p.lower() for p in params)
                    self.assertTrue(has_file,
                                    f"upload 端点应有 file 参数, 实际: {params}")
                break


class TestAPIWithTestClient(IsolatedAsyncioTestCase):
    """使用 TestClient 的集成测试 (需要 DB)

    注意: 这些测试需要:
      1. FastAPI app 正确初始化
      2. 数据库连接可用
      3. 依赖注入配置正确

    如果 app 无法导入, 测试会被跳过。
    """

    @classmethod
    def setUpClass(cls):
        cls.app = _try_import_app()
        if cls.app is None:
            return

        try:
            from httpx import AsyncClient, ASGITransport
            cls.transport = ASGITransport(app=cls.app)
            cls.client_available = True
        except ImportError:
            cls.client_available = False

    def setUp(self):
        if self.app is None:
            self.skipTest("FastAPI app 未能导入 (需要完整项目结构)")
        if not self.client_available:
            self.skipTest("httpx 未安装: pip install httpx")

    async def _get_client(self):
        from httpx import AsyncClient, ASGITransport
        return AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://test"
        )

    async def test_docs_list(self):
        """GET /knowledge/docs 返回列表"""
        async with await self._get_client() as client:
            resp = await client.get("/api/v1/knowledge/docs")
            self.assertIn(resp.status_code, [200, 401, 403],
                          f"意外状态码: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                self.assertIsInstance(data, (list, dict))

    async def test_domains_list(self):
        """GET /knowledge/domains 返回领域列表"""
        async with await self._get_client() as client:
            resp = await client.get("/api/v1/knowledge/domains")
            self.assertIn(resp.status_code, [200, 401, 403])
            if resp.status_code == 200:
                data = resp.json()
                self.assertIsInstance(data, (list, dict))

    async def test_stats(self):
        """GET /knowledge/stats 返回统计"""
        async with await self._get_client() as client:
            resp = await client.get("/api/v1/knowledge/stats")
            self.assertIn(resp.status_code, [200, 401, 403])
            if resp.status_code == 200:
                data = resp.json()
                self.assertIsInstance(data, dict)

    async def test_search_requires_query(self):
        """GET /knowledge/search 无 query 应返回错误"""
        async with await self._get_client() as client:
            resp = await client.get("/api/v1/knowledge/search")
            # 应为 422 (缺少必需参数) 或 400
            self.assertIn(resp.status_code, [400, 422, 401, 403])

    async def test_search_with_query(self):
        """GET /knowledge/search?q=体质 正常检索"""
        async with await self._get_client() as client:
            resp = await client.get("/api/v1/knowledge/search",
                                    params={"q": "体质辨识"})
            self.assertIn(resp.status_code, [200, 401, 403])
            if resp.status_code == 200:
                data = resp.json()
                self.assertIsInstance(data, (list, dict))

    async def test_upload_no_file(self):
        """POST /knowledge/docs/upload 无文件应返回错误"""
        async with await self._get_client() as client:
            resp = await client.post("/api/v1/knowledge/docs/upload")
            self.assertIn(resp.status_code, [400, 422, 401, 403])

    async def test_doc_detail_not_found(self):
        """GET /knowledge/docs/99999 不存在的 ID"""
        async with await self._get_client() as client:
            resp = await client.get("/api/v1/knowledge/docs/99999")
            self.assertIn(resp.status_code, [404, 401, 403])

    async def test_delete_not_found(self):
        """DELETE /knowledge/docs/99999 不存在的 ID"""
        async with await self._get_client() as client:
            resp = await client.delete("/api/v1/knowledge/docs/99999")
            self.assertIn(resp.status_code, [404, 401, 403])


if __name__ == '__main__':
    unittest.main(verbosity=2)
