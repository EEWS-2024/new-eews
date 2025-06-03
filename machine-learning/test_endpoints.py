#!/usr/bin/env python3
"""
Script for testing ML service endpoints
"""
import requests
import json
import numpy as np
from datetime import datetime

# Base URL of the ML service
BASE_URL = "http://127.0.0.1:5001/"

def generate_sample_data(length=382):
    """Generate sample seismic data for testing"""
    # Simulate seismic data with adjustable length
    # Default 382 for custom model, 600+ for PhaseNet
    t = np.linspace(0, 2*np.pi, length) 
    
    # Create 3 sinusoidal signals with different frequencies
    trace1 = np.sin(2*t) * 500 + 500  # BHZ
    trace2 = np.sin(3*t) * 400 + 800  # BHN  
    trace3 = np.sin(4*t) * 300 + 1500 # BHE

    # Combine the three traces into a list of lists
    sample_data = []
    for i in range(length):
        sample_data.append([
            int(trace1[i]),
            int(trace2[i]), 
            int(trace3[i])
        ])
    
    # Ensure we have exactly `length` data points
    assert len(sample_data) == length, f"Expected {length} data points, got {len(sample_data)}"
    
    # Ensure each data point has 3 channels
    for i, point in enumerate(sample_data):
        assert len(point) == 3, f"Data point {i} should have 3 channels, got {len(point)}"
        
    return sample_data
    

def test_predict_endpoint():
    """Test /predict endpoint with custom model"""
    print("=" * 50)
    print("Testing /predict endpoint (custom model)")
    print("=" * 50)
    
    sample_data = generate_sample_data()
    
    payload = {
        "x": sample_data,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "station_code": "TEST01",
        "model_type": "custom"  # Explicitly specify custom model
    }

    # Create a preview of the payload without printing all data
    preview_payload = payload.copy()
    preview_payload["x"] = (
        payload["x"][:1] +
        ["..."] +
        payload["x"][-1:]
    )

    print("Preview Payload:")
    print(json.dumps(preview_payload, indent=4))

    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()

            print("=" * 50)
            print("Prediction Result:")
            print(json.dumps(result, indent=4))
            print("=" * 50)

            print("Success!")
            print(f"Station: {result.get('station_code')}")
            print(f"P Wave Detected: {result.get('p_arr')}")
            print(f"P Wave Time: {result.get('p_arr_time')}")
            print(f"S Wave Detected: {result.get('s_arr')}")
            print(f"S Wave Time: {result.get('s_arr_time')}")
            print(f"New P Event: {result.get('new_p_event')}")
            print(f"New S Event: {result.get('new_s_event')}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")


def test_predict_stats_endpoint():
    """Test /predict/stats endpoint (custom model only)"""
    print("\n" + "=" * 50)
    print("Testing /predict/stats endpoint (custom model only)")
    print("=" * 50)
    
    # Generate simple sample data for stats
    sample_data = generate_sample_data()
    
    payload = {
        "x": sample_data,
        "station_code": "TEST01"
        # No model_type needed - stats only works with custom model
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/stats",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Station: {result.get('station_code')}")
            print(f"Magnitude: {result.get('magnitude'):.2f}")
            print(f"Distance: {result.get('distance'):.2f} km")
            print(f"Depth: {result.get('depth'):.2f} km")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

def test_predict_phasenet_endpoint():
    """Test /predict endpoint with PhaseNet model"""
    print("\n" + "=" * 50)
    print("Testing /predict endpoint (PhaseNet model)")
    print("=" * 50)
    
    # PhaseNet requires at least 600 data points
    sample_data = generate_sample_data(length=600)
    print(f"Generated {len(sample_data)} data points for PhaseNet (minimum 600 required)")
    
    payload = {
        "x": sample_data,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "station_code": "TEST01",
        "model_type": "phasenet"  # Specify PhaseNet model
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",  # Same endpoint, different model_type
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()

            print("=" * 50)
            print("Prediction Result:")
            print(json.dumps(result, indent=4))
            print("=" * 50)

            print("Success!")
            print(f"Station: {result.get('station_code')}")
            print(f"Model Type: {result.get('model_type')}")
            print(f"P Wave Detected: {result.get('p_arr')}")
            print(f"P Wave Time: {result.get('p_arr_time')}")
            print(f"P Wave Index: {result.get('p_arr_index')}")
            print(f"S Wave Detected: {result.get('s_arr')}")
            print(f"S Wave Time: {result.get('s_arr_time')}")
            print(f"S Wave Index: {result.get('s_arr_index')}")
            
            picks = result.get('picks', [])
            if picks:
                print(f"Raw PhaseNet picks: {len(picks)} picks found")
                for pick in picks[:3]:  # Show first 3 picks
                    print(f"  - {pick.get('phase_type')} at index {pick.get('phase_index')} (prob: {pick.get('phase_score')})")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

def test_predict_phasenet_short_data():
    """Test /predict endpoint with PhaseNet model and short data (should fail)"""
    print("\n" + "=" * 50)
    print("Testing /predict endpoint (PhaseNet model) with short data (should fail)")
    print("=" * 50)
    
    # Data is too short (only 382 points, need at least 600)
    sample_data = generate_sample_data(length=382)
    print(f"Generated {len(sample_data)} data points (less than 600 minimum)")
    
    payload = {
        "x": sample_data,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "station_code": "TEST01",
        "model_type": "phasenet"  # Specify PhaseNet model
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",  # Same endpoint, different model_type
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('model_type') == 'phasenet_error':
                print("Expected error handled correctly!")
                print(f"Error message: {result.get('error')}")
            else:
                print("Unexpected success - should have failed with short data")
                print(json.dumps(result, indent=2))
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

def test_service_health():
    """Check if the service is running"""
    print("=" * 50)
    print("Testing service health")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"Service status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Service is not running or cannot be accessed")
        print("Make sure the ML service is running at http://localhost:5001")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def test_predict_default_model():
    """Test /predict endpoint without model_type (should default to custom)"""
    print("\n" + "=" * 50)
    print("Testing /predict endpoint (default model - should be custom)")
    print("=" * 50)
    
    sample_data = generate_sample_data()
    
    payload = {
        "x": sample_data,
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "station_code": "TEST01"
        # No model_type specified - should default to custom
    }

    print("Payload (no model_type specified):")
    print(json.dumps({
        "x": "...",
        "start_time": payload["start_time"],
        "station_code": payload["station_code"]
    }, indent=4))

    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Station: {result.get('station_code')}")
            print(f"P Wave Detected: {result.get('p_arr')}")
            print(f"S Wave Detected: {result.get('s_arr')}")
            
            # Verify it's using custom model (no p_arr_index/s_arr_index)
            if 'p_arr_index' not in result and 's_arr_index' not in result:
                print("✓ Correctly defaulted to custom model (no index fields)")
            else:
                print("⚠ Unexpected: seems to be using PhaseNet model")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {e}")

def main():
    print("Testing ML Service Endpoints")
    print(f"Target: {BASE_URL}")
    
    if not test_service_health():
        return
    
    # Test custom model
    print("Testing custom model")
    test_predict_endpoint()
    test_predict_stats_endpoint()
    
    # Test PhaseNet model
    print("Testing PhaseNet model")
    test_predict_phasenet_endpoint()
    test_predict_phasenet_short_data()
    
    # Test default model
    print("Testing default model")
    test_predict_default_model()
    
    print("\n" + "=" * 50)
    print("Testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
