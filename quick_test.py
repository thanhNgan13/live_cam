"""
Quick Test - Kiểm tra nhanh alert system
Không cần loguru, dùng print thay thế
"""

import sys
import os

# Thử import và test
try:
    print("\n" + "="*70)
    print("🧪 QUICK TEST - Alert System")
    print("="*70)
    
    # Test 1: Check imports
    print("\n1. Checking imports...")
    try:
        import cv2
        print("   ✅ opencv-python (cv2) - OK")
    except:
        print("   ❌ opencv-python not found")
        
    try:
        import numpy as np
        print("   ✅ numpy - OK")
    except:
        print("   ❌ numpy not found")
        
    try:
        from ultralytics import YOLO
        print("   ✅ ultralytics (YOLO) - OK")
    except:
        print("   ❌ ultralytics not found")
        
    try:
        import flask
        print("   ✅ flask - OK")
    except:
        print("   ❌ flask not found")
        
    try:
        from loguru import logger
        print("   ✅ loguru - OK")
    except:
        print("   ⚠️  loguru not found (optional)")
    
    # Test 2: Check model
    print("\n2. Checking YOLO model...")
    model_path = "./models/yolo_based/customized_yolo11s.pt"
    if os.path.exists(model_path):
        print(f"   ✅ Model found: {model_path}")
        try:
            model = YOLO(model_path)
            print(f"   ✅ Model loaded successfully")
            print(f"   Classes: {list(model.names.values())}")
        except Exception as e:
            print(f"   ❌ Failed to load model: {e}")
    else:
        print(f"   ❌ Model not found: {model_path}")
    
    # Test 3: Check alert_manager
    print("\n3. Checking alert_manager.py...")
    try:
        # Thử import với fallback cho loguru
        import alert_manager
        print("   ✅ alert_manager.py imported")
        
        # Test tạo AlertManager
        from alert_manager import AlertManager
        mgr = AlertManager()
        print(f"   ✅ AlertManager created with {len(mgr.rules)} rules")
        
        # In ra rules
        print("\n   📋 Alert Rules:")
        for rule in mgr.rules:
            print(f"      - {rule.class_name}: {rule.alert_type}")
            print(f"        Message: {rule.message}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Test simple detection
    print("\n4. Testing simple alert detection...")
    try:
        from alert_manager import AlertManager
        import time
        
        mgr = AlertManager()
        
        # Simulate phone detections
        print("\n   📱 Simulating phone usage (1.5s threshold)...")
        detections = [(100, 100, 200, 200, 0.9, "phone")]
        
        for i in range(5):
            alerts = mgr.process_detections(detections)
            print(f"      t={i*0.3:.1f}s | Alerts: {len(alerts)}")
            if alerts:
                print(f"      ✅ ALERT: {alerts[0].message}")
                break
            time.sleep(0.3)
        
        if not alerts:
            print("      ⚠️  No alert triggered (might need more time)")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ QUICK TEST COMPLETED")
    print("="*70)
    print("\n💡 Next steps:")
    print("   1. If all checks pass: python admin_app.py")
    print("   2. Open browser: http://localhost:5002/yolo-test")
    print("   3. Select driver and click 'Bắt đầu Detection'")
    print("\n")
    
except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
