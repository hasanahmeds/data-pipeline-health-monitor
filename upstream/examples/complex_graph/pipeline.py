"""Complex pipeline with multiple entry points and cross-calls"""


def utility_compute(n=50):
    """Utility: basic computation"""
    result = 0
    for i in range(n):
        result += (i**2 + i) % 10000
    return result


def utility_validate(data, n=30):
    """Utility: validation logic"""
    total = 0
    for i in range(n):
        total += (data + i) % 100
    return total > 0


def module_loader(count=5):
    """Module: loader - calls utility_compute"""
    results = []
    for i in range(count):
        val = utility_compute(n=50)
        results.append(val)
    return sum(results)


def module_processor(data, count=5):
    """Module: processor - calls utility_compute and utility_validate"""
    total = 0
    for i in range(count):
        computed = utility_compute(n=40)
        if utility_validate(computed):
            total += computed
    return total


def module_aggregator(count=3):
    """Module: aggregator - calls both loader and processor"""
    results = []
    for i in range(count):
        loaded = module_loader(count=5)
        processed = module_processor(loaded, count=4)
        results.append(loaded + processed)
    return sum(results)


def run_complex_pipeline():
    """Execute complex pipeline with multiple paths"""
    print("Starting complex graph pipeline...")

    direct = utility_compute(n=60)
    print(f"  Direct compute: {direct}")

    loaded = module_loader(count=5)
    print(f"  Loaded data: {loaded}")

    processed = module_processor(loaded, count=5)
    print(f"  Processed data: {processed}")

    aggregated = module_aggregator(count=3)
    print(f"  Aggregated result: {aggregated}")

    return direct + loaded + processed + aggregated
