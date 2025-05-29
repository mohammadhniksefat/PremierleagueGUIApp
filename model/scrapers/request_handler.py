import random, asyncio, aiohttp, signal
from threading import Lock


class RequestHandler:
    _instance = None
    _lock = Lock()

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...", #FIXME
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
        "Mozilla/5.0 (X11; Linux x86_64)...",
        # Add more real User-Agent strings here
    ]

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RequestHandler, cls).__new__(cls)
                cls._instance._is_configured = False

        return cls._instance

    async def configure(self):
        if not self._is_configured:
            self.batch_size = random.randint(3, 5)
            self.queue = asyncio.Queue()
            self.session = aiohttp.ClientSession()
            self._scheduler_task  = asyncio.create_task(self._scheduler())
            self._register_shutdown_hooks()
            self._is_configured = True
            self._shutdown_started = False

    def _register_shutdown_hooks(self):
        loop = asyncio.get_running_loop()

        def on_shutdown():
            asyncio.create_task(self.shutdown())

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, on_shutdown)
            except NotImplementedError:
                # On Windows, signal handlers may not work as expected
                def sync_shutdown(*_):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.shutdown())
                    except RuntimeError:
                        # Event loop might already be closed
                        asyncio.run(self.shutdown())
                        
                signal.signal(sig, sync_shutdown)

    async def _scheduler(self):
        while True:
            batch = []
            for _ in range(self.batch_size):
                try:
                    coro = await asyncio.wait_for(self.queue.get(), timeout=1)
                    task = asyncio.create_task(coro())
                    batch.append(task)
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.1)
                    break

            if batch:
                await asyncio.gather(*batch, return_exceptions=True)
                self.batch_size = random.randint(3, 5)
                delay = random.randint(5, 10)
                await asyncio.sleep(delay)

    async def get(self, url, raw=False):
        if not self._is_configured:
            raise RuntimeError("RequestHandler not configured yet. Call 'await handler.configure()' first.")
        
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }

        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async def fetch():
            try:
                async with self.session.get(url, headers=headers) as response:
                    result = await response.read() if raw else await response.text()
                    future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            
        self.queue.put_nowait(fetch)
        return await future

    async def shutdown(self):
        if getattr(self, "_shutdown_started", False):
            return
        self._shutdown_started = True

        print("Shutting down...")
        if hasattr(self, "_scheduler_task"):
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        if hasattr(self, 'session') and self.session and not self.session.closed:
            await self.session.close()


class PlaywrightRequestHandler:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PlaywrightRequestHandler, cls).__new__(cls)
                cls._instance._is_configured = False
        return cls._instance
            
    async def configure(self):
        if not self._is_configured:
            self.batch_size = random.randint(3, 5)
            self.queue = asyncio.Queue()
            self._schedular_task = asyncio.create_task(self._scheduler())
            self._register_shutdown_hooks()
            self._is_configured = True

    def _register_shutdown_hooks(self):
        loop = asyncio.get_running_loop()

        def on_shutdown():
            asyncio.create_task(self.shutdown())

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, on_shutdown)
            except NotImplementedError:
                # On Windows, signal handlers may not work as expected

                def sync_shutdown(*_):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.shutdown)
                    except RuntimeError:
                        # Event loop might already be closed
                        asyncio.run(self.shutdown())
                signal.signal(sig, sync_shutdown)

    async def _scheduler(self):
        while True:
            batch = []
            for _ in range(self.batch_size):
                try:
                    coro = await asyncio.wait_for(asyncio.shield(self.queue.get()), timeout=1)
                    batch.append(asyncio.create_task(coro()))
                except asyncio.TimeoutError:
                    await asyncio.sleep(0.1)
                    break  # No more tasks for now

            if batch:
                await asyncio.gather(*batch)
                self.batch_size = random.randint(3, 5)
                delay = random.randint(5, 10)
                await asyncio.sleep(delay)

    async def goto(self, page, url):
        if not self._is_configured:
            raise RuntimeError("PlaywrightRequestHandler not configured yet. Call 'await handler.configure()' first.")
        
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async def coroutine():
            await asyncio.wait_for(page.goto(url), timeout=30)
            future.set_result(None)
        
        self.queue.put_nowait(coroutine())
        return await future

    async def shutdown(self):
        if getattr(self, "_shutdown_started", False):
            return
        self._shutdown_started = True

        print("Shutting down...")
        if hasattr(self, "_scheduler_task"):
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
