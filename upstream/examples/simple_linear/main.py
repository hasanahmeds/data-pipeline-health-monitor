"""
Simple Linear Pipeline Example

Run with: python main.py

This example demonstrates a basic sequential pipeline:
A -> B -> C -> D

Each stage processes data and passes it to the next stage.
"""

from pipeline import run_linear_pipeline

from pipelinescope import profile_pipeline


def main():
    """Main entry point"""
    print("=" * 60)
    print("Simple Linear Pipeline - PipelineScope Example")
    print("=" * 60)

    for iteration in range(10):
        print(f"\nIteration {iteration + 1}/10")
        run_linear_pipeline(iterations=100)

    print("\n" + "=" * 60)
    print("Pipeline execution complete!")
    print("Check .pipelinescope_output/ for profiling results")
    print("=" * 60)


if __name__ == "__main__":
    profile_pipeline.start()
    main()
