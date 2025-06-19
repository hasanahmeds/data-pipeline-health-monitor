"""
Nested Calls Pipeline Example

Run with: python main.py

This example demonstrates nested function calls:
- A (entry) calls B 10 times
- Each B calls C 10 times
- Total C calls: 100

Shows call graph and identifies which functions are called most frequently.
"""

from pipeline import run_nested_pipeline

from pipelinescope import profile_pipeline


def main():
    """Main entry point"""
    print("=" * 60)
    print("Nested Calls Pipeline - PipelineScope Example")
    print("=" * 60)

    for iteration in range(5):
        print(f"\nIteration {iteration + 1}/5")
        run_nested_pipeline(cycles=10)

    print("\n" + "=" * 60)
    print("Pipeline execution complete!")
    print("Check .pipelinescope_output/ for profiling results")
    print("=" * 60)


if __name__ == "__main__":
    profile_pipeline.start()
    main()
