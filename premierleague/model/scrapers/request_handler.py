import random, asyncio, aiohttp, signal, time, logging
from threading import Lock

logger = logging.getLogger(__name__)

class RequestHandler:
    _instance = None
    _lock = Lock()

    USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36",

    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",

    # Firefox on Ubuntu
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",

    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Mobile Safari/537.36",

    # Safari on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",

    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36 Edg/123.0.2420.65",

    # Brave on macOS (Brave uses the Chrome engine, but identifies itself differently)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36 Brave/123.1.59.120"
]

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                logger.debug("Creating a new instance of RequestHandler", extra={"tags": ["singleton", "init"]})
                cls._instance = super(RequestHandler, cls).__new__(cls)
                cls._instance._is_configured = False
        return cls._instance

    @classmethod
    def reset(cls):
        logger.info("Resetting RequestHandler singleton instance", extra={"tags": ["reset"]})
        cls._instance = None

    async def configure(self):
        current_loop = asyncio.get_running_loop()
        logger.debug("Starting configure()", extra={"tags": ["configure"]})

        if not self._is_configured or self._scheduler_loop != current_loop:
            if hasattr(self, '_scheduler_task'):
                try:
                    logger.info("Reconfiguring session: closing previous session and cancelling task", extra={"tags": ["configure"]})
                    await self.session.close()
                    self._scheduler_task.cancel()
                    await self._scheduler_task
                except asyncio.CancelledError:
                    logger.warning("Scheduler task cancelled during reconfiguration", extra={"tags": ["configure"]})

            self.queue = asyncio.Queue()
            self.session = aiohttp.ClientSession()
            self._batch_size = random.randint(3, 5)
            logger.debug(f"Batch size set to {self._batch_size}", extra={"tags": ["configure"]})
            self._register_shutdown_hooks()
            self._scheduler_task = asyncio.create_task(self._scheduler())
            self._scheduler_loop = current_loop
            self._is_configured = True
            self._shutdown_started = False

            logger.info("RequestHandler configured successfully", extra={"tags": ["configure"]})

    def _register_shutdown_hooks(self):
        loop = asyncio.get_running_loop()

        def on_shutdown():
            logger.info("Shutdown signal received", extra={"tags": ["shutdown"]})
            asyncio.create_task(self.shutdown())

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, on_shutdown)
            except NotImplementedError:
                logger.warning(f"Signal {sig} not supported on this OS", extra={"tags": ["shutdown", "signal"]})
                def sync_shutdown(*_):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.shutdown())
                    except RuntimeError:
                        logger.warning("Loop already closed; forcing shutdown", extra={"tags": ["shutdown"]})
                        asyncio.run(self.shutdown())
                signal.signal(sig, sync_shutdown)

    async def _scheduler(self):
        logger.info("Scheduler started", extra={"tags": ["scheduler"]})
        while True:
            batch = []
            for _ in range(self._batch_size):
                try:
                    coro = await asyncio.wait_for(self.queue.get(), timeout=1)
                    task = asyncio.create_task(coro)
                    batch.append(task)
                    logger.debug("Task added to batch", extra={"tags": ["scheduler"]})
                except asyncio.TimeoutError:
                    break

            if batch:
                logger.debug(f"Executing batch of size {len(batch)}", extra={"tags": ["scheduler"]})
                await asyncio.gather(*batch)
                self._batch_size = random.randint(3, 5)
                delay = random.randint(5, 10)
                logger.info(f"Batch complete. Sleeping for {delay}s", extra={"tags": ["scheduler"]})
                await asyncio.sleep(delay)

    async def get(self, url, raw=False):
        if not self._is_configured:
            raise RuntimeError("RequestHandler not configured yet. Call 'await handler.configure()' first.")

        user_agent = random.choice(self.USER_AGENTS)
        headers = {"User-Agent": user_agent}
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async def fetch():
            start = time.time()
            try:
                async with self.session.get(url, headers=headers) as response:
                    duration = round(time.time() - start, 3)
                    status_code = response.status
                    result = await response.read() if raw else await response.text()    
                    logger.info(
                        f"GET request successful - status: {status_code}",
                        extra={
                            "tags": ["network", "http", "get"],
                            "duration": duration,
                            "status_code": status_code,
                            "url": url,
                            "agent": user_agent,
                        },
                    )
                    future.set_result(result)
                    
            except Exception as e:
                duration = round(time.time() - start, 3)
                logger.error(
                    f"GET request failed for {url}",
                    exc_info=True,
                    extra={
                        "tags": ["network", "http", "get"],
                        "error": str(e),
                        "url": url,
                        "agent": user_agent,
                        "duration": duration,
                    },
                )
                future.set_exception(e)

        self.queue.put_nowait(fetch())
        logger.debug(f"GET request queued: {url}", extra={"tags": ["network", "http"]})
        return await future

    async def shutdown(self):
        if getattr(self, "_shutdown_started", False):
            return
        self._shutdown_started = True

        logger.info("Initiating shutdown...", extra={"tags": ["shutdown"]})
        if hasattr(self, "_scheduler_task"):
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                logger.debug("Scheduler task cancelled", extra={"tags": ["shutdown"]})

        if hasattr(self, 'session') and self.session and not self.session.closed:
            await self.session.close()
            logger.info("Session closed", extra={"tags": ["shutdown"]})


class PlaywrightRequestHandler:
    _instance = None
    _lock = Lock()

    @classmethod
    def reset(cls):
        logger.info("Resetting PlaywrightRequestHandler instance", extra={"tags": ["reset"]})
        cls._instance = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                logger.debug("Creating a new instance of PlaywrightRequestHandler", extra={"tags": ["singleton", "init"]})
                cls._instance = super(PlaywrightRequestHandler, cls).__new__(cls)
                cls._instance._is_configured = False
        return cls._instance

    async def configure(self):
        if not self._is_configured:
            logger.info("Configuring PlaywrightRequestHandler", extra={"tags": ["configure"]})
            self._batch_size = random.randint(3, 5)
            self.queue = asyncio.Queue()
            self._schedular_task = asyncio.create_task(self._scheduler())
            self._register_shutdown_hooks()
            self._shutdown_started = False
            self._is_configured = True
            logger.info("PlaywrightRequestHandler configured", extra={"tags": ["configure"]})

    def _register_shutdown_hooks(self):
        loop = asyncio.get_running_loop()

        def on_shutdown():
            logger.info("Shutdown signal received", extra={"tags": ["shutdown"]})
            asyncio.create_task(self.shutdown())

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, on_shutdown)
            except NotImplementedError:
                logger.warning(f"Signal {sig} not supported", extra={"tags": ["shutdown", "signal"]})
                def sync_shutdown(*_):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.shutdown())
                    except RuntimeError:
                        logger.warning("Loop closed; using run() for shutdown", extra={"tags": ["shutdown"]})
                        asyncio.run(self.shutdown())
                signal.signal(sig, sync_shutdown)

    async def _scheduler(self):
        logger.info("Playwright scheduler started", extra={"tags": ["scheduler"]})
        while True:
            batch = []
            for _ in range(self._batch_size):
                try:
                    coro = await asyncio.wait_for(asyncio.shield(self.queue.get()), timeout=1)
                    batch.append(asyncio.create_task(coro))
                    logger.debug("Playwright task added to batch", extra={"tags": ["scheduler"]})
                except asyncio.TimeoutError:
                    logger.debug("Playwright task queue timeout", extra={"tags": ["scheduler"]})
                    await asyncio.sleep(0.1)
                    break

            if batch:
                await asyncio.gather(*batch)
                self._batch_size = random.randint(3, 5)
                delay = random.randint(5, 10)
                logger.info(f"Batch done. Sleeping {delay}s", extra={"tags": ["scheduler"]})
                await asyncio.sleep(delay)

    async def goto(self, page, url):
        if not self._is_configured:
            raise RuntimeError("PlaywrightRequestHandler not configured yet. Call 'await handler.configure()' first.")

        loop = asyncio.get_running_loop()
        future = loop.create_future()

        async def coroutine():
            try:
                logger.info(f"Navigating to {url}", extra={"tags": ["goto", "network"]})
                await asyncio.wait_for(page.goto(url), 
                                       timeout=30)
                logger.info(f"Navigation to {url} succeeded", extra={"tags": ["goto", "network"]})
                future.set_result(None)
            except Exception as e:
                logger.error(
                    f"Failed to navigate to {url}",
                    exc_info=True,
                    extra={
                        "tags": ["goto", "network"],
                        "url": url,
                        "error": str(e),
                    },
                )
                future.set_exception(e)

        self.queue.put_nowait(coroutine())
        return await future

    async def shutdown(self):
        if getattr(self, "_shutdown_started", False):
            return
        self._shutdown_started = True
        logger.info("Shutting down PlaywrightRequestHandler...", extra={"tags": ["shutdown"]})

        if hasattr(self, "_scheduler_task"):
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                logger.debug("Playwright scheduler task cancelled", extra={"tags": ["shutdown"]})
