import resource

def calculate_performance(start_time, end_time, cpu_percent, memory_usage):
    # Calculate execution time
    execution_time = end_time - start_time

    # Calculate average CPU and memory usage
    avg_cpu_percent = sum(cpu_percent) / len(cpu_percent)
    avg_memory_usage = sum(memory_usage) / len(memory_usage)

    # Calculate resource usage
    usage = resource.getrusage(resource.RUSAGE_SELF)

    print("Execution Time:", execution_time, "seconds")
    print("Average CPU Usage:", avg_cpu_percent, "%")
    print("Average Memory Usage:", avg_memory_usage, "%")
    print("User CPU Time:", usage.ru_utime, "seconds")
    print("System CPU Time:", usage.ru_stime, "seconds")
    print("Max Resident Set Size:", usage.ru_maxrss, "bytes")