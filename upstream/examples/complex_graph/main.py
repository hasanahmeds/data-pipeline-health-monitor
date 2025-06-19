"""
Complex Graph Pipeline Example

Run with: python main.py

This example demonstrates a complex call graph with:
- Multiple entry points
- Cross-module calls
- Utility functions used by multiple modules
- Different call depths

Shows bottleneck identification across complex call patterns.
"""

from pipeline import run_complex_pipeline

from pipelinescope import profile_pipeline


def main():
    """Main entry point"""
    print("=" * 60)
    print("Complex Graph Pipeline - PipelineScope Example")
    print("=" * 60)

    for iteration in range(8):
        print(f"\nIteration {iteration + 1}/8")
        run_complex_pipeline()

    print("\n" + "=" * 60)
    print("Pipeline execution complete!")
    print("Check .pipelinescope_output/ for profiling results")
    print("=" * 60)


if __name__ == "__main__":
    profile_pipeline.start()
    main()
