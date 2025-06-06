import pytest, random, asyncio
# import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call
from model.scrapers.request_handler import PlaywrightRequestHandler, signal

@pytest.fixture(autouse=True)
def reset_singleton():
    PlaywrightRequestHandler.reset()
    yield
    PlaywrightRequestHandler.reset()


@pytest.mark.asyncio
async def test_singleton_behavior():
    instance1 = PlaywrightRequestHandler()
    instance2 = PlaywrightRequestHandler()
    assert instance1 is instance2, "PlaywrightRequestHandler is not a singleton"


@pytest.mark.asyncio
async def test_configure_sets_is_configured():
    handler = PlaywrightRequestHandler()
    
    await handler.configure()
    assert handler._is_configured is True, "Handler was not marked as configured"


@pytest.mark.asyncio
async def test_configure_sets_required_attributes():
    handler = PlaywrightRequestHandler()
    
    await handler.configure()
    
    assert hasattr(handler, "queue"), "Queue not initialized"
    assert isinstance(handler.queue, asyncio.Queue), "Queue is not an instance of asyncio.Queue"
    
    assert hasattr(handler, "_schedular_task"), "Scheduler task not created"
    assert hasattr(handler, "_batch_size"), "_batch_size not initialized"
    assert 3 <= handler._batch_size <= 5, "_batch_size not in expected range"

    assert hasattr(handler, "_shutdown_started"), "_shutdown_started not set"
    assert handler._shutdown_started is False, "_shutdown_started should initially be False"

# ======================= Test goto() method =============================
            
@pytest.mark.asyncio
async def test_goto_raises_error_if_not_configured():
    handler = PlaywrightRequestHandler()
    handler._is_configured = False

    page = AsyncMock()
    with pytest.raises(RuntimeError, match="not configured yet"):
        await handler.goto(page, "http://example.com")


@pytest.mark.asyncio
async def test_goto_adds_task_and_executes_it():
    handler = PlaywrightRequestHandler()
    await handler.configure()
    handler._schedular_task.cancel()

    page = AsyncMock()
    page.goto = AsyncMock()

    # Run `goto()` in background since it waits on a future
    task = asyncio.create_task(handler.goto(page, "http://example.com"))

    # Manually execute the coroutine inside the queue
    coroutine = await handler.queue.get()  # This is a coroutine
    await coroutine  # Execute it (calls page.goto and sets future)

    await task  # Ensure final await resolves

    page.goto.assert_awaited_once_with("http://example.com")


@pytest.mark.asyncio
async def test_goto_waits_until_page_load_completes():
    handler = PlaywrightRequestHandler()    
    await handler.configure()
    handler._schedular_task.cancel()

    page = AsyncMock()

    signal = asyncio.Event()

    async def fake_goto(url):
        await signal.wait()  # Pause until we say so
        return None

    page.goto.side_effect = fake_goto

    # Start `goto()` in background (will hang until signal is set)
    task = asyncio.create_task(handler.goto(page, "http://example.com"))

    # Pop and run the coroutine from the queue
    coro = await handler.queue.get()
    run_task = asyncio.create_task(coro)

    await asyncio.sleep(0.1)  # Make sure it's blocked

    # At this point, `task` shouldn't be done
    assert not task.done()

    signal.set()  # Allow `page.goto()` to finish
    await run_task
    await task

    assert task.done()
    page.goto.assert_awaited_once_with("http://example.com")

# =================== Test _scheduler() method ====================

@pytest.mark.asyncio
async def test_scheduler_processes_batch_and_sleeps():
    handler = PlaywrightRequestHandler()
    await handler.configure()
    handler._batch_size = 3
    handler._schedular_task.cancel()

    executed = []

    def mock_task_maker(index):
        async def task():
            executed.append(index)
        return task

    # Add 3 mock coroutines to the queue
    for i in range(3):
        coro = mock_task_maker(i)
        handler.queue.put_nowait(coro())

    # Patch batch size and delay to fixed values
    with patch("random.randint", side_effect=[3, 5]), \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        # Run scheduler in a background task and cancel after one cycle
        try:
            await asyncio.wait_for(handler._scheduler(), timeout=0.1)
        except:
            pass

        # Validate task execution
        assert set(executed) == {0, 1, 2}
        assert mock_sleep.call_args_list[-1] == call(5)

@pytest.mark.asyncio
async def test_scheduler_handles_timeout_gracefully():
    handler = PlaywrightRequestHandler()
    await handler.configure()

    with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError), \
     patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
     patch("random.randint", return_value=3):

        scheduler_task = asyncio.create_task(handler._scheduler())
        await asyncio.sleep(0.1)
        if scheduler_task.done():
            potential_exc = scheduler_task.exception()
            if potential_exc and isinstance(potential_exc, asyncio.TimeoutError):
                pytest.fail()
        scheduler_task.cancel()

        # Verify it handled the timeout gracefully and tried to sleep briefly
        mock_sleep.assert_called()

@pytest.mark.asyncio
async def test_scheduler_random_batch_and_delay_every_cycle():
    
    handler = PlaywrightRequestHandler()
    handler._is_configured = True
    handler._batch_size = 5
    handler.queue = asyncio.Queue()

    for _ in range(5):
        handler.queue.put_nowait(AsyncMock()())

    with patch("model.scrapers.request_handler.random.randint", side_effect=[4, 7, 3, 6]), \
         patch("model.scrapers.request_handler.asyncio.sleep", new_callable=AsyncMock), \
         patch("model.scrapers.request_handler.asyncio.gather", wraps=asyncio.gather, new_callable=AsyncMock):

        scheduler_task = asyncio.create_task(handler._scheduler())

        try:
            await asyncio.wait_for(scheduler_task, timeout=0.05)
        except asyncio.TimeoutError:
            pass

        # Check randint was used for batch size and delay
        # Every cycle calls randint twice: once for batch size, once for delay
        # So we expect randint to be called multiple times
        
        assert handler._batch_size in [3, 4]

# ================= Test shutdown() method behavior ==================

@pytest.mark.asyncio
async def test_shutdown_cancels_scheduler_and_sets_flag():
    handler = PlaywrightRequestHandler()
    await handler.configure()

    # fake_task = AsyncMock()
    # fake_task.cancel = AsyncMock()
    # fake_task.__await__ = lambda x: (_ for _ in ()).throw(asyncio.CancelledError())

    fake_task = asyncio.create_task(AsyncMock()())

    handler._scheduler_task = fake_task

    await handler.shutdown()

    # fake_task.cancel.assert_called_once()
    with pytest.raises(asyncio.CancelledError):
        await handler._scheduler_task

    assert handler._shutdown_started is True


@pytest.mark.asyncio
async def test_shutdown_is_idempotent():
    handler = PlaywrightRequestHandler()
    await handler.configure()

    fake_task = asyncio.create_task(AsyncMock()())

    handler._scheduler_task = fake_task

    # First call
    await handler.shutdown()

    # Second call should do nothing
    await handler.shutdown()

    # Still only one cancel call
    with pytest.raises(asyncio.CancelledError):
        await handler._scheduler_task


@pytest.mark.asyncio
async def test_shutdown_handles_cancelled_error_gracefully():
    handler = PlaywrightRequestHandler()
    await handler.configure()

    handler._scheduler_task = asyncio.create_task(AsyncMock()())
    handler._scheduler_task.cancel()

    try:
        await handler.shutdown()
    except asyncio.CancelledError:
        pytest.fail("shutdown() should not propagate CancelledError")


# =================== Test _register_shutdown_hooks() method ==================
        
@pytest.mark.asyncio
async def test_register_shutdown_hooks_adds_signal_handlers():
    handler = PlaywrightRequestHandler()

    mock_loop = MagicMock()
    mock_loop.add_signal_handler = MagicMock()
    
    with patch("asyncio.get_running_loop", return_value=mock_loop):
        handler._register_shutdown_hooks()

    # Should attempt to register handlers for SIGINT and SIGTERM
    assert mock_loop.add_signal_handler.call_count == 2
    assert {call.args[0] for call in mock_loop.add_signal_handler.call_args_list} == {signal.SIGINT, signal.SIGTERM}


@pytest.mark.asyncio
async def test_register_shutdown_hooks_fallback_on_not_implemented():
    handler = PlaywrightRequestHandler()

    mock_loop = MagicMock()
    mock_loop.add_signal_handler.side_effect = NotImplementedError()

    with patch("asyncio.get_running_loop", return_value=mock_loop), \
         patch("signal.signal") as mock_signal:

        handler._register_shutdown_hooks()

        # signal.signal should be used as fallback
        assert mock_signal.call_count == 2
        assert {call.args[0] for call in mock_signal.call_args_list} == {signal.SIGINT, signal.SIGTERM}


@pytest.mark.asyncio
async def test_on_shutdown_creates_shutdown_task():
    handler = PlaywrightRequestHandler()
    handler.shutdown = AsyncMock()

    mock_loop = MagicMock()
    mock_loop.add_signal_handler = MagicMock()

    with patch("model.scrapers.request_handler.asyncio.get_running_loop", return_value=mock_loop), \
         patch("model.scrapers.request_handler.asyncio.create_task") as mock_create_task:

        handler._register_shutdown_hooks()

        # Call the handler that was registered (the actual callback)
        shutdown_callback = mock_loop.add_signal_handler.call_args[0][1]
        shutdown_callback()

        mock_create_task.assert_called_once()
        created_coroutine = mock_create_task.call_args[0][0]
        assert asyncio.iscoroutine(created_coroutine)
        assert created_coroutine.cr_code is handler.shutdown().cr_code


@pytest.mark.asyncio
async def test_sync_shutdown_fallback_runs_shutdown_directly():
    handler = PlaywrightRequestHandler()
    handler.shutdown = AsyncMock()

    mock_loop = MagicMock()
    mock_loop.add_signal_handler = MagicMock(side_effect=NotImplementedError)

    # Simulate RuntimeError (loop closed)
    with patch("asyncio.get_running_loop", side_effect=[mock_loop, RuntimeError]), \
         patch("asyncio.run") as mock_run, \
         patch("signal.signal") as mock_signal:

        handler._register_shutdown_hooks()

        # Extract fallback signal handler
        call_args = mock_signal.call_args_list[0]
        sync_shutdown_fn = call_args[0][1]

        # Call the fallback
        sync_shutdown_fn()

        mock_run.assert_called_once()
        coroutine = mock_run.call_args[0][0]
        assert coroutine.cr_code == handler.shutdown().cr_code
