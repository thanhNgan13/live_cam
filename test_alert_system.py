"""
Test Alert Manager - Script để test thuật toán cảnh báo
"""

from alert_manager import AlertManager, DetectionEvent, AlertRule
import time


def test_duration_based_alert():
    """Test alert dựa trên duration (Phone)"""
    print("\n" + "=" * 70)
    print("🧪 TEST 1: Duration-Based Alert (Phone)")
    print("=" * 70)
    
    # Tạo rule phone với duration nhỏ để test
    rules = [
        AlertRule(
            class_name="phone",
            alert_type="duration",
            min_duration=2.0,
            max_gap=1.0,
            cooldown=5.0,
            priority=1,
            message="⚠️ TEST: Phone detected for 2+ seconds!"
        )
    ]
    
    manager = AlertManager(rules=rules)
    
    # Simulate detections
    print("\n📱 Simulating phone detections...")
    
    # Detection 1: t=0
    detections = [(100, 100, 200, 200, 0.9, "phone")]
    alerts = manager.process_detections(detections)
    print(f"t=0.0s: Phone detected | Alerts: {len(alerts)}")
    time.sleep(0.5)
    
    # Detection 2: t=0.5
    alerts = manager.process_detections(detections)
    print(f"t=0.5s: Phone detected | Alerts: {len(alerts)}")
    time.sleep(0.5)
    
    # Detection 3: t=1.0
    alerts = manager.process_detections(detections)
    print(f"t=1.0s: Phone detected | Alerts: {len(alerts)}")
    time.sleep(0.5)
    
    # Detection 4: t=1.5
    alerts = manager.process_detections(detections)
    print(f"t=1.5s: Phone detected | Alerts: {len(alerts)}")
    time.sleep(0.5)
    
    # Detection 5: t=2.0 - Should trigger alert!
    alerts = manager.process_detections(detections)
    print(f"t=2.0s: Phone detected | Alerts: {len(alerts)}")
    
    if alerts:
        print(f"\n✅ SUCCESS: Alert triggered!")
        print(f"   Message: {alerts[0].message}")
        print(f"   Duration: {alerts[0].metadata.get('duration')}s")
    else:
        print("\n❌ FAILED: No alert triggered")
    
    # Test cooldown
    print("\n⏱️  Testing cooldown...")
    time.sleep(1)
    alerts = manager.process_detections(detections)
    print(f"t=3.0s: Phone detected | Alerts: {len(alerts)}")
    print(f"   Expected: 0 (cooldown active)")
    
    # Stats
    stats = manager.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total alerts: {stats['total_alerts']}")


def test_frequency_based_alert():
    """Test alert dựa trên frequency (Yawn)"""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Frequency-Based Alert (Yawn)")
    print("=" * 70)
    
    rules = [
        AlertRule(
            class_name="yawn",
            alert_type="frequency",
            max_count=3,  # Giảm xuống 3 để test nhanh
            time_window=10.0,
            cooldown=5.0,
            priority=2,
            message="⚠️ TEST: Yawned 3 times in 10 seconds!"
        )
    ]
    
    manager = AlertManager(rules=rules)
    
    print("\n🥱 Simulating yawn detections...")
    
    detections = [(100, 100, 200, 200, 0.9, "yawn")]
    
    # Yawn 1
    alerts = manager.process_detections(detections)
    print(f"Yawn #1 | Alerts: {len(alerts)}")
    time.sleep(2)
    
    # Yawn 2
    alerts = manager.process_detections(detections)
    print(f"Yawn #2 | Alerts: {len(alerts)}")
    time.sleep(2)
    
    # Yawn 3 - Should trigger alert!
    alerts = manager.process_detections(detections)
    print(f"Yawn #3 | Alerts: {len(alerts)}")
    
    if alerts:
        print(f"\n✅ SUCCESS: Alert triggered!")
        print(f"   Message: {alerts[0].message}")
        print(f"   Count: {alerts[0].metadata.get('count')}")
    else:
        print("\n❌ FAILED: No alert triggered")
    
    stats = manager.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total alerts: {stats['total_alerts']}")


def test_gap_interruption():
    """Test gap interruption trong duration-based"""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: Gap Interruption (Sleepy Eye with Natural)")
    print("=" * 70)
    
    rules = [
        AlertRule(
            class_name="sleepy_eye",
            alert_type="duration",
            min_duration=3.0,
            max_gap=2.0,  # Allow 2s gap for "natural"
            cooldown=5.0,
            priority=1,
            message="🚨 TEST: Sleepy eye for 3+ seconds!"
        )
    ]
    
    manager = AlertManager(rules=rules)
    
    print("\n😴 Simulating sleepy eye with natural interruption...")
    
    detections_sleepy = [(100, 100, 200, 200, 0.9, "sleepy_eye")]
    detections_natural = [(100, 100, 200, 200, 0.9, "natural")]
    
    # Sleepy 0-1s
    alerts = manager.process_detections(detections_sleepy)
    print(f"t=0.0s: Sleepy detected | Alerts: {len(alerts)}")
    time.sleep(1)
    
    # Sleepy 1-2s
    alerts = manager.process_detections(detections_sleepy)
    print(f"t=1.0s: Sleepy detected | Alerts: {len(alerts)}")
    time.sleep(0.5)
    
    # Natural 2-2.5s (gap < 2s, should not reset)
    alerts = manager.process_detections(detections_natural)
    print(f"t=2.0s: Natural detected (gap interruption) | Alerts: {len(alerts)}")
    time.sleep(0.5)
    
    # Sleepy 2.5-3.5s
    alerts = manager.process_detections(detections_sleepy)
    print(f"t=2.5s: Sleepy detected again | Alerts: {len(alerts)}")
    time.sleep(1)
    
    # Sleepy 3.5s - Should trigger alert!
    alerts = manager.process_detections(detections_sleepy)
    print(f"t=3.5s: Sleepy detected | Alerts: {len(alerts)}")
    
    if alerts:
        print(f"\n✅ SUCCESS: Alert triggered despite natural interruption!")
        print(f"   Message: {alerts[0].message}")
        print(f"   Duration: {alerts[0].metadata.get('duration')}s")
    else:
        print("\n❌ FAILED: No alert triggered")


def test_large_gap_reset():
    """Test reset khi gap quá lớn"""
    print("\n" + "=" * 70)
    print("🧪 TEST 4: Large Gap Reset")
    print("=" * 70)
    
    rules = [
        AlertRule(
            class_name="phone",
            alert_type="duration",
            min_duration=2.0,
            max_gap=1.0,
            cooldown=5.0,
            priority=1,
            message="⚠️ TEST: Phone for 2+ seconds!"
        )
    ]
    
    manager = AlertManager(rules=rules)
    
    print("\n📱 Simulating phone with large gap...")
    
    detections = [(100, 100, 200, 200, 0.9, "phone")]
    
    # Phone 0-1s
    alerts = manager.process_detections(detections)
    print(f"t=0.0s: Phone detected | Alerts: {len(alerts)}")
    time.sleep(1)
    
    # Phone 1s
    alerts = manager.process_detections(detections)
    print(f"t=1.0s: Phone detected | Alerts: {len(alerts)}")
    
    # Large gap 2.5s (> max_gap 1.0s, should reset)
    print(f"t=1.0-3.5s: No detection (gap = 2.5s > max_gap)")
    time.sleep(2.5)
    
    # Phone 3.5s (counter should reset)
    alerts = manager.process_detections(detections)
    print(f"t=3.5s: Phone detected (after reset) | Alerts: {len(alerts)}")
    time.sleep(1)
    
    # Phone 4.5s (only 1s duration, not enough)
    alerts = manager.process_detections(detections)
    print(f"t=4.5s: Phone detected | Alerts: {len(alerts)}")
    
    if len(alerts) == 0:
        print(f"\n✅ SUCCESS: Counter reset correctly after large gap!")
    else:
        print("\n❌ FAILED: Alert triggered when it shouldn't")


def run_all_tests():
    """Chạy tất cả tests"""
    print("\n" + "=" * 70)
    print("🚀 ALERT MANAGER TEST SUITE")
    print("=" * 70)
    
    test_duration_based_alert()
    test_frequency_based_alert()
    test_gap_interruption()
    test_large_gap_reset()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
