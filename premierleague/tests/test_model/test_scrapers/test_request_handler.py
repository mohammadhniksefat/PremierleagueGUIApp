import pytest
import signal
import asyncio
import concurrent.futures
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from premierleague.model.scrapers.request_handler import RequestHandler

# Fixture to reset singleton before each test
@pytest.fixture(autouse=True)
def reset_singleton():
    RequestHandler.reset()
    yield
    RequestHandler.reset()

# Test 1: Basic Singleton Behavior
def test_singleton_basic():
    h1 = RequestHandler()
    h2 = RequestHandler()
    assert h1 is h2, "Multiple instances were created instead of a singleton"

# Test 2: Thread Safety in Singleton
def create_instance():
    return RequestHandler()

def test_singleton_thread_safety():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        instances = list(executor.map(lambda _: create_instance(), range(10)))
    first_instance = instances[0]
    assert all(inst is first_instance for inst in instances), "Thread safety failed: Multiple instances created"

# Test 3: Singleton Behavior in Async Contexts
async def get_instance():
    return RequestHandler()

@pytest.mark.asyncio
async def test_singleton_async():
    instances = await asyncio.gather(*[get_instance() for _ in range(10)])
    first = instances[0]
    assert all(inst is first for inst in instances), "Singleton failed across async contexts"

# ===================== Test configure() method behavior =====================
    
@pytest.mark.asyncio
async def test_configure_initializes_attributes():
    with patch("premierleague.model.scrapers.request_handler.aiohttp.ClientSession", return_value=MagicMock()) as mock_session:
        handler = RequestHandler()
        await handler.configure()

        assert handler._is_configured is True
        assert isinstance(handler.queue, asyncio.Queue)
        assert handler.session is mock_session.return_value
        assert isinstance(handler._batch_size, int)
        assert 3 <= handler._batch_size <= 5
        assert isinstance(handler._scheduler_task, asyncio.Task)
        assert not handler._scheduler_task.done()

@pytest.mark.asyncio
async def test_configure_does_not_reconfigure_on_second_call():
    with patch("premierleague.model.scrapers.request_handler.aiohttp.ClientSession", return_value=MagicMock()) as mock_session:
        handler = RequestHandler()
        await handler.configure()

        # Save references to verify no change
        session = handler.session
        queue = handler.queue
        scheduler_task = handler._scheduler_task
        _batch_size = handler._batch_size

        await handler.configure()  # Call again

        # Assert all values are the same (no reconfiguration)
        assert handler.session is session
        assert handler.queue is queue
        assert handler._scheduler_task is scheduler_task
        assert handler._batch_size == _batch_size

@pytest.mark.asyncio
async def test_configure_only_runs_once_even_with_multiple_calls():
    with patch("premierleague.model.scrapers.request_handler.aiohttp.ClientSession", return_value=MagicMock()) as mock_session:
        handler = RequestHandler()

        await asyncio.gather(handler.configure(), handler.configure(), handler.configure())
        assert handler._is_configured is True
        assert isinstance(handler.queue, asyncio.Queue)
        assert handler.session is mock_session.return_value

# ====================== Test _register_shutdown_hooks() method ======================
        
def test_register_shutdown_hooks_posix():
    handler = RequestHandler()
    mock_loop = MagicMock()

    with patch("premierleague.model.scrapers.request_handler.asyncio.get_running_loop", return_value=mock_loop):
        handler._register_shutdown_hooks()

        assert mock_loop.add_signal_handler.call_count == 2
        mock_loop.add_signal_handler.assert_any_call(signal.SIGINT, ANY)
        mock_loop.add_signal_handler.assert_any_call(signal.SIGTERM, ANY)

def test_register_shutdown_hooks_windows_fallback():
    handler = RequestHandler()
    mock_loop = MagicMock()
    shutdown_patch = patch.object(handler, "shutdown", return_value=MagicMock())
    
    with (
        patch("premierleague.model.scrapers.request_handler.asyncio.get_running_loop", return_value=mock_loop),
        patch.object(mock_loop, "add_signal_handler", side_effect=NotImplementedError),
        patch("premierleague.model.scrapers.request_handler.signal.signal") as mock_signal,
        shutdown_patch,
    ):
        handler._register_shutdown_hooks()

        # Fallback registered handlers using signal.signal
        assert mock_signal.call_count == 2
        mock_signal.assert_any_call(signal.SIGINT, ANY)
        mock_signal.assert_any_call(signal.SIGTERM, ANY)

def test_shutdown_fallback_uses_asyncio_run_on_runtime_error():
    handler = RequestHandler()

    loop = asyncio.new_event_loop()

    # patch get_running_loop to return loop normally, but we'll patch it again later for fallback
    with patch("premierleague.model.scrapers.request_handler.asyncio.get_running_loop", return_value=loop), \
         patch.object(loop, "add_signal_handler", side_effect=NotImplementedError), \
         patch("premierleague.model.scrapers.request_handler.signal.signal") as mock_signal, \
         patch("premierleague.model.scrapers.request_handler.asyncio.run") as mock_run, \
         patch.object(handler, "shutdown", new=AsyncMock()):

        handler._register_shutdown_hooks()

        # The fallback registered functions are sync_shutdown handlers set by signal.signal
        # Now get_running_loop patchedinside sync_shutdown to raise RuntimeError
        with patch("premierleague.model.scrapers.request_handler.asyncio.get_running_loop", side_effect=RuntimeError):
            # Call the fallback signal handlers to trigger the RuntimeError and fallback to asyncio.run
            for call_args in mock_signal.call_args_list:
                signal_handler_func = call_args[0][1]
                signal_handler_func()  # This calls sync_shutdown, triggering your test scenario

        # Assert asyncio.run was called twice (once per signal)
        assert mock_run.call_count == 2

@pytest.mark.asyncio
async def test_shutdown_normal_behavior():
    handler = RequestHandler()
    handler._shutdown_started = False

    # Mock scheduler task
    handler._scheduler_task = asyncio.create_task(AsyncMock()())
    handler._scheduler_task.cancel = MagicMock()

    # Mock session
    handler.session = AsyncMock()
    handler.session.closed = False

    await handler.shutdown()

    assert handler._shutdown_started is True
    handler._scheduler_task.cancel.assert_called_once()
    handler.session.close.assert_called_once()

@pytest.mark.asyncio
async def test_shutdown_skips_if_already_shutdown():
    handler = RequestHandler()
    handler._shutdown_started = True

    # Should skip all logic if already started
    handler._scheduler_task = AsyncMock()
    handler.session = AsyncMock()

    await handler.shutdown()

    handler._scheduler_task.cancel.assert_not_called()
    handler.session.close.assert_not_called()

@pytest.mark.asyncio
async def test_shutdown_handles_cancelled_error():
    handler = RequestHandler()
    handler._shutdown_started = False

    task = asyncio.create_task(AsyncMock()())
    task.cancel = MagicMock()
    async def raise_cancelled():
        raise asyncio.CancelledError()
    task.__await__ = lambda _: raise_cancelled().__await__()

    handler._scheduler_task = task
    handler.session = AsyncMock()
    handler.session.closed = False

    await handler.shutdown()  # Should not raise

@pytest.mark.asyncio
async def test_shutdown_skips_if_scheduler_task_missing():
    handler = RequestHandler()
    handler._shutdown_started = False
    handler.session = AsyncMock()
    handler.session.closed = False

    # _scheduler_task attribute is missing intentionally! 

    await handler.shutdown()

    handler.session.close.assert_called_once()

@pytest.mark.asyncio
async def test_shutdown_skips_if_session_already_closed():
    handler = RequestHandler()
    handler._shutdown_started = False
    handler._scheduler_task = asyncio.create_task(AsyncMock()())
    handler._scheduler_task.cancel = MagicMock()
    handler.session = AsyncMock()
    handler.session.closed = True

    await handler.shutdown()

    handler.session.close.assert_not_called()

@pytest.mark.asyncio
async def test_shutdown_skips_if_session_missing():
    handler = RequestHandler()
    handler._shutdown_started = False
    handler._scheduler_task = asyncio.create_task(AsyncMock()())
    handler._scheduler_task.cancel = MagicMock()

    # session attribute is missed intentionally!

    await handler.shutdown()  # Should not raise

# ======================== Test _schedular() method behavior ========================
    
@pytest.mark.asyncio
async def test_scheduler_processes_batch_correctly():
    handler = RequestHandler()
    handler.queue = asyncio.Queue()
    handler._batch_size = 3

    indexes = []
    async def mock_task(index):
        indexes.append(index)

    mock_coros = [mock_task(index) for index in range(3)]

    for coro in mock_coros:
        # These return a coroutine when called
        await handler.queue.put(coro)

    with patch("premierleague.model.scrapers.request_handler.random.randint", side_effect=[3, 6]), \
         patch("premierleague.model.scrapers.request_handler.asyncio.sleep", new=AsyncMock()) as mock_sleep, \
         patch("premierleague.model.scrapers.request_handler.asyncio.gather", new=AsyncMock()) as mock_gather:

        # Run only 1 iteration using timeout to exit loop
        async def limited_scheduler():
            await asyncio.wait_for(handler._scheduler(), timeout=0.5)

        with pytest.raises(asyncio.TimeoutError):
            await limited_scheduler()

        assert mock_gather.called
        assert mock_gather.call_count == 1
        assert set(indexes) == {0, 1, 2}
        assert mock_sleep.call_args_list[-1][0][0] == 6  # final delay sleep


@pytest.mark.asyncio
async def test_scheduler_handles_timeout_and_sleeps():
    handler = RequestHandler()
    handler.queue = asyncio.Queue()
    handler._batch_size = 3

    with patch("premierleague.model.scrapers.request_handler.asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
         patch("premierleague.model.scrapers.request_handler.random.randint", return_value=3), \
         patch("premierleague.model.scrapers.request_handler.asyncio.wait_for", side_effect=asyncio.TimeoutError):

        # Run _scheduler in background and let it hit the timeout path
        task = asyncio.create_task(handler._scheduler())

        # Give the event loop a chance to run the scheduler and hit sleep
        await asyncio.sleep(0.1)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        mock_sleep.assert_any_call(0.1)

@pytest.mark.asyncio
async def test_scheduler_cancellation():
    handler = RequestHandler()
    handler.queue = asyncio.Queue()
    handler._batch_size = 2

    await handler.queue.put(lambda: AsyncMock())

    with patch("premierleague.model.scrapers.request_handler.asyncio.gather", new=AsyncMock()), \
         patch("premierleague.model.scrapers.request_handler.asyncio.sleep", new=AsyncMock()):
        task = asyncio.create_task(handler._scheduler())
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

# ========================== Test get() method behavior ==========================

@pytest.mark.asyncio
async def test_get_raises_before_configure():
    handler = RequestHandler()
    with pytest.raises(RuntimeError):
        await handler.get("http://example.com")

@pytest.mark.asyncio
class MockResponse:
    def __init__(self, data):
        self._data = data

    async def text(self):
        return self._data

    async def read(self):
        return self._data

class MockContextManager:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

@pytest.mark.asyncio
async def test_get_returns_text_response():
    handler = RequestHandler()
    await handler.configure()

    mock_response = MockResponse("mock page")

    mock_session = MagicMock()
    mock_session.get.return_value = MockContextManager(mock_response)
    handler.session = mock_session

    # Trigger the request manually
    result_future = asyncio.create_task(handler.get("http://example.com"))
    fetch = await handler.queue.get()
    await fetch  # Manually run the coroutine

    assert await result_future == "mock page"

@pytest.mark.asyncio
async def test_get_returns_raw_response():
    handler = RequestHandler()
    await handler.configure()
    handler._scheduler_task.cancel()

    mock_response = MockResponse(b"binary content")
    mock_session = MagicMock()
    mock_session.get.return_value = MockContextManager(mock_response)
    handler.session = mock_session

    result_future = asyncio.create_task(handler.get("http://example.com", raw=True))
    fetch = await handler.queue.get()
    await fetch

    assert await result_future == b"binary content"

# ---- Test: exception handling ----

class FailingContextManager:
    async def __aenter__(self):
        raise Exception("Network error")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

@pytest.mark.asyncio
async def test_get_sets_exception_on_failure():
    handler = RequestHandler()
    await handler.configure()
    handler._scheduler_task.cancel()

    mock_session = MagicMock()
    mock_session.get.return_value = FailingContextManager()
    handler.session = mock_session

    result_future = asyncio.create_task(handler.get("http://example.com"))
    fetch = await handler.queue.get()
    await fetch

    with pytest.raises(Exception) as exc:
        await result_future
    assert "Network error" in str(exc.value)

# ---- Test: multiple concurrent requests ----

@pytest.mark.asyncio
async def test_multiple_concurrent_get_requests():
    handler = RequestHandler()
    await handler.configure()
    handler._scheduler_task.cancel()

    mock_response = MockResponse("OK")
    mock_session = MagicMock()
    mock_session.get.return_value = MockContextManager(mock_response)
    handler.session = mock_session

    urls = [f"http://example.com/{i}" for i in range(5)]
    tasks = [asyncio.create_task(handler.get(url)) for url in urls]

    fetches = [await handler.queue.get() for _ in range(5)]
    for fetch in fetches:
        await fetch

    results = await asyncio.gather(*tasks)
    assert results == ["OK"] * 5