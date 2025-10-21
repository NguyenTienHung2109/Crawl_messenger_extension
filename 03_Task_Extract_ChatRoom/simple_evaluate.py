#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple evaluation - so sánh solution với ground truth
"""

import pandas as pd

def evaluate_solution(solution_file, gt_file="ground_truth_2digit.csv"):
    """Đánh giá độ chính xác của solution"""
    
    # Load files
    solution_df = pd.read_csv(solution_file, encoding='utf-8-sig')
    gt_df = pd.read_csv(gt_file, encoding='utf-8-sig')
    
    print("DANH GIA KET QUA")
    print("=" * 40)
    print(f"Solution: {len(solution_df)} deals")
    print(f"Ground truth: {len(gt_df)} deals")
    
    # Exact matches
    exact_matches = 0
    
    for _, gt_row in gt_df.iterrows():
        # Tìm exact match trong solution
        matches = solution_df[
            (solution_df['Buy_side'] == gt_row['Buy_side']) &
            (solution_df['Sell_side'] == gt_row['Sell_side']) &
            (solution_df['Amount'] == gt_row['Amount']) &
            (solution_df['Actual_price_2digit'] == gt_row['Actual_price_2digit'])
        ]
        
        if len(matches) > 0:
            exact_matches += 1
    
    accuracy = exact_matches / len(gt_df) * 100
    
    print(f"\nKET QUA:")
    print(f"Exact matches: {exact_matches}/{len(gt_df)}")
    print(f"Do chinh xac: {accuracy:.1f}%")
    
    return accuracy, exact_matches

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        solution_file = sys.argv[1]
    else:
        solution_file = "solution_step_results.csv"
    
    evaluate_solution(solution_file)