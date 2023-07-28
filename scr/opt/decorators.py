import time
import resource
from functools import wraps


def time_counter(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Start time
        func(*args, **kwargs)
        end_time = time.time()
        # Calculate execution time
        execution_time = end_time - start_time
        print("Execution Time:", execution_time, "seconds")
    return wrapper


def performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cpu_percent = []
        memory_usage = []

        # Run the decorated function and collect CPU and memory usage data
        result = func(*args, **kwargs)

        # Unpack the performance data from the decorated function's result
        if isinstance(result, tuple) and len(result) == 2:
            cpu_percent, memory_usage = result

        # Calculate performance metrics
        avg_cpu_percent = sum(cpu_percent) / len(cpu_percent)
        avg_memory_usage = sum(memory_usage) / len(memory_usage)
        usage = resource.getrusage(resource.RUSAGE_SELF)

        # Print performance metrics
        print("Average CPU Usage:", avg_cpu_percent, "%")
        print("Average Memory Usage:", avg_memory_usage, "%")
        print("User CPU Time:", usage.ru_utime, "seconds")
        print("System CPU Time:", usage.ru_stime, "seconds")
        print("Max Resident Set Size:", usage.ru_maxrss, "bytes")

        # Return the result of the decorated function
        return result
    return wrapper
