#!/usr/bin/env python3

# Simple test script for Dotc spawn functionality
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotc.dotc import Dotc

def test_dotc_spawn():
    print("Testing Dotc spawn functionality...")
    
    # Test data
    data = {
        'a': 1,
        'b': {
            'c': 3,
            'd': [4, 5, 6]
        }
    }
    
    print(f"Test data: {data}")
    
    # Test 1: Normal instantiation (should return just the instance)
    print("\n--- Test 1: Normal instantiation ---")
    d1 = Dotc(data)
    print(f"d1 = Dotc(data)")
    print(f"Type: {type(d1)}")
    print(f"d1.a = {d1.a}")
    print(f"d1.b.c = {d1.b.c}")
    
    # Test 2: Instantiation with both data and _pathget (should return tuple)
    print("\n--- Test 2: Instantiation with data and _pathget ---")
    try:
        result = Dotc(data, _pathget='b.c')
        print(f"result = Dotc(data, _pathget='b.c')")
        print(f"Type: {type(result)}")
        if isinstance(result, tuple):
            d2, value = result
            print(f"d2 type: {type(d2)}")
            print(f"value: {value}")
            print(f"d2.a = {d2.a}")
        else:
            print(f"Unexpected result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Using spawn method
    print("\n--- Test 3: Using spawn method ---")
    d3 = Dotc(data)
    d3_instance, d3_result = d3.spawn('b.d.0')
    print(f"d3_instance, d3_result = d3.spawn('b.d.0')")
    print(f"d3_instance type: {type(d3_instance)}")
    print(f"d3_result: {d3_result}")
    print(f"d3_instance is d3: {d3_instance is d3}")
    
    # Test 4: Using create_with_result factory method
    print("\n--- Test 4: Using create_with_result factory method ---")
    d4_instance, d4_result = Dotc.create_with_result(data, 'b.d.1')
    print(f"d4_instance, d4_result = Dotc.create_with_result(data, 'b.d.1')")
    print(f"d4_instance type: {type(d4_instance)}")
    print(f"d4_result: {d4_result}")
    print(f"d4_instance.a = {d4_instance.a}")

if __name__ == "__main__":
    test_dotc_spawn()
