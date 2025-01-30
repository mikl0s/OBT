from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from ..schemas.benchmark import BenchmarkResult


class BenchmarkStorage:
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.db = mongo_client.obt
        self._collection: AsyncIOMotorCollection = self.db.benchmark_results

    async def save_result(self, result: BenchmarkResult) -> str:
        """Save a benchmark result to the database."""
        doc = result.dict()
        await self._collection.insert_one(doc)
        return result.id

    async def get_result(self, result_id: str) -> Optional[BenchmarkResult]:
        """Retrieve a specific benchmark result."""
        doc = await self._collection.find_one({"id": result_id})
        return BenchmarkResult(**doc) if doc else None

    async def get_results_for_model(self, model_name: str) -> List[BenchmarkResult]:
        """Get all benchmark results for a specific model."""
        cursor = self._collection.find({"config.model_name": model_name})
        results = []
        async for doc in cursor:
            results.append(BenchmarkResult(**doc))
        return results

    async def get_results_for_client(self, client_id: str) -> List[BenchmarkResult]:
        """Get all benchmark results for a specific client."""
        cursor = self._collection.find({"client_id": client_id})
        results = []
        async for doc in cursor:
            results.append(BenchmarkResult(**doc))
        return results

    async def get_results_for_model_and_client(
        self, model_name: str, client_id: str
    ) -> List[BenchmarkResult]:
        """Get all benchmark results for a specific model and client."""
        cursor = self._collection.find(
            {"config.model_name": model_name, "client_id": client_id}
        )
        results = []
        async for doc in cursor:
            results.append(BenchmarkResult(**doc))
        return results

    async def get_latest_results(self, limit: int = 10) -> List[BenchmarkResult]:
        """Get the most recent benchmark results."""
        cursor = self._collection.find().sort("start_time", -1).limit(limit)
        results = []
        async for doc in cursor:
            results.append(BenchmarkResult(**doc))
        return results

    async def delete_result(self, result_id: str) -> bool:
        """Delete a specific benchmark result."""
        result = await self._collection.delete_one({"id": result_id})
        return result.deleted_count > 0

    async def get_results_in_timeframe(
        self, start_time: datetime, end_time: datetime
    ) -> List[BenchmarkResult]:
        """Get benchmark results within a specific timeframe."""
        cursor = self._collection.find(
            {"start_time": {"$gte": start_time, "$lte": end_time}}
        ).sort("start_time", -1)
        results = []
        async for doc in cursor:
            results.append(BenchmarkResult(**doc))
        return results
