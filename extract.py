import pandas as pd
import argparse
import re

def strip_suffix(url):
    """Remove numeric suffixes (e.g., -0, -1) from URLs."""
    return re.sub(r'-\d+$', '', url)

def process_jmeter_results(input_file, output_file):
    # Load the JTL file into a DataFrame
    columns_to_read = ['label', 'elapsed', 'responseCode', 'success']  # Relevant columns
    df = pd.read_csv(input_file, usecols=columns_to_read)

    # Clean up the 'label' column by removing numeric suffixes
    df['clean_label'] = df['label'].apply(strip_suffix)

    # Add an 'error' column (True if success is False)
    df['error'] = ~df['success']

    # Preserve the first appearance order of each unique URL
    df['first_seen_order'] = df.groupby('clean_label').cumcount() == 0
    first_appearance = df.loc[df['first_seen_order'], ['clean_label']].reset_index()

    # Group by the cleaned label
    summary = df.groupby('clean_label').agg(
        avg_response_time=('elapsed', lambda x: x.mean() / 1000),  # Convert to seconds
        min_response_time=('elapsed', lambda x: x.min() / 1000),  # Convert to seconds
        max_response_time=('elapsed', lambda x: x.max() / 1000),  # Convert to seconds
        error_percentage=('error', lambda x: (x.sum() / len(x)) * 100),
        total_samples=('elapsed', 'count')
    ).reset_index()

    # Merge with the first appearance order to preserve the original sequence
    summary = pd.merge(first_appearance, summary, left_on='clean_label', right_on='clean_label')
    summary.drop(columns='index', inplace=True)  # Drop unnecessary index column if it exists

    # Rename columns for clarity
    summary.columns = ['URL Path', 'Avg Response Time (s)', 'Min Response Time (s)',
                       'Max Response Time (s)', 'Error %', 'Total Samples']

    # Save the result to a CSV
    summary.to_csv(output_file, index=False)

    print(f"Summary report saved to {output_file}")
    print(summary)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process JMeter .jtl results into a summary report.")
    parser.add_argument("input_file", help="Path to the JMeter .jtl input file")
    parser.add_argument("output_file", help="Path to the output CSV file for the summary report")

    args = parser.parse_args()

    # Process the input and generate the report
    process_jmeter_results(args.input_file, args.output_file)
