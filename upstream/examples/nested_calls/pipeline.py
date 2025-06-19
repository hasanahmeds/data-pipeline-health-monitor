"""Nested pipeline: A calls B 10 times, B calls C 5 times"""


def helper_c(n=50):
    """Helper function C: innermost operation"""
    result = 0
    for i in range(n):
        result += (i * i) % 10000
    return result


def processor_b(n=10):
    """Processor B: calls C multiple times"""
    results = []
    for i in range(n):
        res = helper_c(n=50)
        results.append(res)
    return sum(results)


def orchestrator_a(cycles=10):
    """Orchestrator A: calls B multiple times"""
    results = []
    for i in range(cycles):
        res = processor_b(n=10)
        results.append(res)
    return sum(results)


def run_nested_pipeline(cycles=10):
    """Execute nested pipeline"""
    print(f"Starting nested pipeline with {cycles} cycles...")
    print(f"  A calls B {cycles} times")
    print("  B calls C 10 times per call")
    print(f"  Total C calls: {cycles * 10}")

    result = orchestrator_a(cycles=cycles)
    print(f"  Final result: {result}")

    return result
