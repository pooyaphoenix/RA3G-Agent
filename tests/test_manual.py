"""
Manual test script for GovernanceAgent PII redaction.
Run this with: python tests/test_manual.py
"""
from app.agents.governance_agent import GovernanceAgent

def test_redactions():
    """Manual test of PII redaction."""
    agent = GovernanceAgent()
    
    test_cases = [
        ("Email: john@example.com", "[REDACTED_EMAIL]"),
        ("Phone: (123) 456-7890", "[REDACTED_PHONE]"),
        ("IP: 192.168.1.1", "[REDACTED_IP]"),
        ("Contact: user@test.com or call 555-123-4567", "[REDACTED_EMAIL]", "[REDACTED_PHONE]"),
        ("Email: test@example.com, Phone: 123-456-7890, IP: 10.0.0.1", "[REDACTED_EMAIL]", "[REDACTED_PHONE]", "[REDACTED_IP]"),
    ]
    
    print("Testing PII Redaction\n" + "="*50)
    
    for i, test in enumerate(test_cases, 1):
        text = test[0]
        expected_placeholders = test[1:]
        result = agent._redact_pii(text)
        
        print(f"\nTest {i}:")
        print(f"  Input:  {text}")
        print(f"  Output: {result}")
        
        all_found = True
        for placeholder in expected_placeholders:
            if placeholder in result:
                print(f"  ✓ Found {placeholder}")
            else:
                print(f"  ✗ Missing {placeholder}")
                all_found = False
        
        if all_found:
            print(f"  Status: PASS")
        else:
            print(f"  Status: FAIL")
    
    print("\n" + "="*50)
    print("Test completed!")

if __name__ == "__main__":
    test_redactions()

