"""
Quick test để verify frequency-based alert đã fix
"""

from alert_manager import AlertManager, DetectionEvent
import time

def test_yawn_frequency():
    """Test yawn frequency với gap detection"""
    print("\n" + "=" * 70)
    print("TEST: Yawn Frequency (should need 5 DISTINCT yawns)")
    print("=" * 70)
    
    manager = AlertManager()
    detections_yawn = [(100, 100, 200, 200, 0.9, "yawn")]
    
    print("\nSimulating yawn detections with gaps...")
    
    # Yawn 1 (continuous for 2s)
    print("\n1. Yawn #1 starts (continuous detection)...")
    for i in range(4):  # 4 detections trong 2s
        alerts = manager.process_detections(detections_yawn)
        print(f"   Detection at t={i*0.5}s | Alerts: {len(alerts)}")
        time.sleep(0.5)
    
    # Gap 2 giây
    print("\n   [2 second gap - no detection]")
    time.sleep(2)
    
    # Yawn 2
    print("\n2. Yawn #2 (should be counted as 2nd yawn)")
    alerts = manager.process_detections(detections_yawn)
    print(f"   Alerts: {len(alerts)}")
    time.sleep(1)
    
    # Yawn 3
    print("\n3. Yawn #3")
    alerts = manager.process_detections(detections_yawn)
    print(f"   Alerts: {len(alerts)}")
    time.sleep(1)
    
    # Yawn 4
    print("\n4. Yawn #4")
    alerts = manager.process_detections(detections_yawn)
    print(f"   Alerts: {len(alerts)}")
    time.sleep(1)
    
    # Yawn 5 - Should trigger alert!
    print("\n5. Yawn #5 (should trigger ALERT!)")
    alerts = manager.process_detections(detections_yawn)
    print(f"   Alerts: {len(alerts)}")
    
    if alerts:
        print(f"\n✅ SUCCESS! Alert triggered at 5th yawn")
        print(f"   Message: {alerts[0].message}")
        print(f"   Count: {alerts[0].metadata.get('count')}")
    else:
        print("\n❌ FAILED! No alert triggered")
    
    # Stats
    stats = manager.get_statistics()
    print(f"\n📊 Final Stats:")
    print(f"   Total alerts: {stats['total_alerts']}")


def test_phone_duration():
    """Test phone duration"""
    print("\n" + "=" * 70)
    print("TEST: Phone Duration (should need 1.5s continuous)")
    print("=" * 70)
    
    manager = AlertManager()
    detections_phone = [(100, 100, 200, 200, 0.9, "phone")]
    
    print("\nSimulating phone usage...")
    
    for i in range(5):
        alerts = manager.process_detections(detections_phone)
        duration = i * 0.5
        print(f"t={duration}s | Phone detected | Alerts: {len(alerts)}")
        
        if alerts:
            print(f"\n✅ Alert triggered at {duration}s")
            print(f"   Message: {alerts[0].message}")
            break
        
        time.sleep(0.5)
    
    if not alerts:
        print("\n❌ No alert triggered")


if __name__ == "__main__":
    test_yawn_frequency()
    print("\n" + "=" * 70 + "\n")
    test_phone_duration()
    print("\n" + "=" * 70)
