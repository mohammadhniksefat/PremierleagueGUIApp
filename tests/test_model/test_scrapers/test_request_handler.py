import pytest
import signal
import asyncio
import concurrent.futures
from unittest.mock import patch, MagicMock, AsyncMock, call, ANY
from model.scrapers.request_handler import RequestHandler

# Fixture to reset singleton before each test
@pytest.fixture(autouse=True)
def reset_singleton():
    RequestHandler._instance = None
    yield
    RequestHandler._instance = None

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
    with patch("model.scrapers.request_handler.aiohttp.ClientSession", return_value=MagicMock()) as mock_session:
        handler = RequestHandler()
        await handler.configure()

        assert handler._is_configured is True
        assert isinstance(handler.queue, asyncio.Queue)
        assert handler.session is mock_session.return_value
        assert isinstance(handler.batch_size, int)
        assert 3 <= handler.batch_size <= 5
        assert isinstance(handler._scheduler_task, asyncio.Task)
        assert not handler._scheduler_task.done()

@pytest.mark.asyncio
async def test_configure_does_not_reconfigure_on_second_call():
    with patch("model.scrapers.request_handler.aiohttp.ClientSession", return_value=MagicMock()) as mock_session:
        handler = RequestHandler()
        await handler.configure()

        # Save references to verify no change
        session = handler.session
        queue = handler.queue
        scheduler_task = handler._scheduler_task
        batch_size = handler.batch_size

        await handler.configure()  # Call again

        # Assert all values are the same (no reconfiguration)
        assert handler.session is session
        assert handler.queue is queue
        assert handler._scheduler_task is scheduler_task
        assert handler.batch_size == batch_size

@pytest.mark.asyncio
async def test_configure_only_runs_once_even_with_multiple_calls():
    with patch("model.scrapers.request_handler.aiohttp.ClientSession", return_value=MagicMock()) as mock_session:
        handler = RequestHandler()

        await asyncio.gather(handler.configure(), handler.configure(), handler.configure())
        assert handler._is_configured is True
        assert isinstance(handler.queue, asyncio.Queue)
        assert handler.session is mock_session.return_value

# ====================== Test _register_shutdown_hooks() method ======================
        
def test_register_shutdown_hooks_posix():
    handler = RequestHandler()
    mock_loop = MagicMock()

    with patch("model.scrapers.request_handler.asyncio.get_running_loop", return_value=mock_loop):
        handler._register_shutdown_hooks()

        assert mock_loop.add_signal_handler.call_count == 2
        mock_loop.add_signal_handler.assert_any_call(signal.SIGINT, ANY)
        mock_loop.add_signal_handler.assert_any_call(signal.SIGTERM, ANY)

def test_register_shutdown_hooks_windows_fallback():
    handler = RequestHandler()
    mock_loop = MagicMock()
    shutdown_patch = patch.object(handler, "shutdown", return_value=MagicMock())
    
    with (
        patch("model.scrapers.request_handler.asyncio.get_running_loop", return_value=mock_loop),
        patch.object(mock_loop, "add_signal_handler", side_effect=NotImplementedError),
        patch("model.scrapers.request_handler.signal.signal") as mock_signal,
        shutdown_patch,
    ):
        handler._register_shutdown_hooks()

        # Fallback registered handlers using signal.signal
        assert mock_signal.call_count == 2
        mock_signal.assert_any_call(signal.SIGINT, ANY)
        mock_signal.assert_any_call(signal.SIGTERM, ANY)

def test_shutdown_fallback_uses_asyncio_run_on_runtime_error():
    handler = RequestHandler()

    with (
        patch("model.scrapers.request_handler.asyncio.get_running_loop", side_effect=RuntimeError),
        patch("model.scrapers.request_handler.signal.signal") as mock_signal,
        patch("model.scrapers.request_handler.asyncio.run") as mock_run,
        patch.object(handler, "shutdown", return_value=MagicMock()),
    ):
        handler._register_shutdown_hooks()

        # Simulate signal being triggered
        for call_args in mock_signal.call_args_list:
            signal_func = call_args[0][1]
            signal_func()

        assert mock_run.call_count == 2  # once for each signal

@pytest.mark.asyncio
async def test_shutdown_normal_behavior():
    handler = RequestHandler()
    handler._shutdown_started = False

    # Mock scheduler task
    handler._scheduler_task = AsyncMock()
    handler._scheduler_task.cancel = MagicMock()

    # Mock session
    handler.session = AsyncMock()
    handler.session.closed = False

    await handler.shutdown()

    assert handler._shutdown_started is True
    handler._scheduler_task.cancel.assert_called_once()
    handler._scheduler_task.__await__()  # ensures it was awaited
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

    task = AsyncMock()
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

    delattr(handler, '_scheduler_task')  # Simulate it's missing
    await handler.shutdown()

    handler.session.close.assert_called_once()

@pytest.mark.asyncio
async def test_shutdown_skips_if_session_already_closed():
    handler = RequestHandler()
    handler._shutdown_started = False
    handler._scheduler_task = AsyncMock()
    handler._scheduler_task.cancel = MagicMock()
    handler.session = AsyncMock()
    handler.session.closed = True

    await handler.shutdown()

    handler.session.close.assert_not_called()

@pytest.mark.asyncio
async def test_shutdown_skips_if_session_missing():
    handler = RequestHandler()
    handler._shutdown_started = False
    handler._scheduler_task = AsyncMock()
    handler._scheduler_task.cancel = MagicMock()

    delattr(handler, 'session')
    await handler.shutdown()  # Should not raise

# ======================== Test _schedular() method behavior ========================
    
@pytest.mark.asyncio
async def test_scheduler_processes_batch_correctly():
    handler = RequestHandler()
    handler.queue = asyncio.Queue()
    handler.batch_size = 3

    mock_coros = [AsyncMock() for _ in range(3)]
    for coro in mock_coros:
        # These return a coroutine when called
        await handler.queue.put(lambda coro=coro: coro)

    with patch("model.scrapers.request_handler.random.randint", side_effect=[3, 6]), \
         patch("model.scrapers.request_handler.asyncio.sleep", new=AsyncMock()) as mock_sleep, \
         patch("model.scrapers.request_handler.asyncio.gather", new=AsyncMock()) as mock_gather:
        
        # Run only 1 iteration using timeout to exit loop
        async def limited_scheduler():
            await asyncio.wait_for(handler._scheduler(), timeout=0.5)

        with pytest.raises(asyncio.TimeoutError):
            await limited_scheduler()

        assert mock_gather.called
        assert mock_gather.call_count == 1
        assert mock_sleep.call_args_list[-1][0][0] == 6  # final delay sleep

@pytest.mark.asyncio
async def test_scheduler_handles_timeout_and_sleeps():
    handler = RequestHandler()
    handler.queue = asyncio.Queue()
    handler.batch_size = 3

    # Queue is empty, so wait_for will timeout
    with patch("model.scrapers.request_handler.asyncio.sleep", new=AsyncMock()) as mock_sleep, \
         patch("model.scrapers.request_handler.random.randint", return_value=3):

        async def limited_scheduler():
            await asyncio.wait_for(handler._scheduler(), timeout=0.5)

        with pytest.raises(asyncio.TimeoutError):
            await limited_scheduler()

        mock_sleep.assert_any_call(0.1)

@pytest.mark.asyncio
async def test_scheduler_cancellation():
    handler = RequestHandler()
    handler.queue = asyncio.Queue()
    handler.batch_size = 2

    await handler.queue.put(lambda: AsyncMock())

    with patch("model.scrapers.request_handler.asyncio.gather", new=AsyncMock()), \
         patch("model.scrapers.request_handler.asyncio.sleep", new=AsyncMock()):
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
async def test_get_returns_text_response():
    handler = RequestHandler()
    await handler.configure()

    mock_response = AsyncMock()
    mock_response.text.return_value = "mock page"
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    handler.session = mock_session

    # Trigger the request manually
    result_future = asyncio.create_task(handler.get("http://example.com"))
    fetch = await handler.queue.get()
    await fetch()  # Manually run the coroutine

    assert await result_future == "mock page"

@pytest.mark.asyncio
async def test_get_returns_raw_response():
    handler = RequestHandler()
    await handler.configure()

    mock_response = AsyncMock()
    mock_response.read.return_value = b"binary content"
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    handler.session = mock_session

    result_future = asyncio.create_task(handler.get("http://example.com", raw=True))
    fetch = await handler.queue.get()
    await fetch()

    assert await result_future == b"binary content"

@pytest.mark.asyncio
async def test_get_sets_exception_on_failure():
    handler = RequestHandler()
    await handler.configure()

    mock_session = AsyncMock()
    mock_session.get.side_effect = Exception("Network error")
    handler.session = mock_session

    result_future = asyncio.create_task(handler.get("http://example.com"))
    fetch = await handler.queue.get()
    await fetch()

    with pytest.raises(Exception) as exc:
        await result_future
    assert "Network error" in str(exc.value)

@pytest.mark.asyncio
async def test_multiple_concurrent_get_requests():
    handler = RequestHandler()
    await handler.configure()

    mock_response = AsyncMock()
    mock_response.text.return_value = "OK"
    mock_session = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    handler.session = mock_session

    urls = [f"http://example.com/{i}" for i in range(5)]
    tasks = [asyncio.create_task(handler.get(url)) for url in urls]

    fetches = [await handler.queue.get() for _ in range(5)]
    for fetch in fetches:
        await fetch()

    results = await asyncio.gather(*tasks)
    assert results == ["OK"] * 5