"""Simple linear pipeline: A -> B -> C -> D"""


def stage_a(n=100):
    """Stage A: Initial processing"""
    result = 0
    for i in range(n):
        result += i**2
    return result


def stage_b(data, n=100):
    """Stage B: Transform data"""
    result = data
    for i in range(n):
        result += i * 2
    return result


def stage_c(data, n=100):
    """Stage C: Aggregate"""
    result = data
    for i in range(n):
        result = (result + i) % 1000000
    return result


def stage_d(data, n=100):
    """Stage D: Final processing"""
    result = data
    for i in range(n):
        if i % 2 == 0:
            result += i
    return result


def run_linear_pipeline(iterations=100):
    """Execute linear pipeline: A -> B -> C -> D"""
    print(f"Starting linear pipeline with {iterations} iterations...")

    data = stage_a(iterations)
    print(f"  Stage A complete: {data}")

    data = stage_b(data, iterations)
    print(f"  Stage B complete: {data}")

    data = stage_c(data, iterations)
    print(f"  Stage C complete: {data}")

    data = stage_d(data, iterations)
    print(f"  Stage D complete: {data}")

    return data
