from functools import wraps

class InputValidator:
    
    @staticmethod
    def check_not_none(func):

        @wraps(func)
        def new_func(*args, **kwargs):
            
            if any(arg is None for arg in args):
                info_logger.warning(f'input arguments of {func.__name__} is None')
                raise ValueError('input arguments must not be None')
            for key, value in kwargs.items():
                if value is None:
                    raise ValueError(f'"{key}" argument must not be None')
            
            return func(*args, **kwargs)

        return new_func
    

class OutputChecker:
    @staticmethod
    def check_not_none(func):
        
        @wraps(func)
        def new_func(*args, **kwargs):
            result = func(*args, **kwargs)

            if result is None:
                raise ValueError(f"output of {func.__name__} must not be None")
            return result
        
        return new_func

    @staticmethod            
    def check_not_falsy(func):

        @wraps(func)
        def new_func(*args, **kwargs):
            result = func(*args, **kwargs)

            if not result:
                raise ValueError(f'invalid output for {func.__name__} method')

        return new_func
