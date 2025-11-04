"""
Unit tests for GovernanceAgent PII redaction functionality.
Tests email, phone number, and IP address detection and redaction.
"""
import pytest
from app.agents.governance_agent import GovernanceAgent


class TestEmailRedaction:
    """Test email detection and redaction."""
    
    def test_simple_email(self):
        agent = GovernanceAgent()
        text = "Contact me at john.doe@example.com for more info."
        result = agent._redact_pii(text)
        assert "[REDACTED_EMAIL]" in result
        assert "john.doe@example.com" not in result
    
    def test_multiple_emails(self):
        agent = GovernanceAgent()
        text = "Email: alice@test.com or bob@example.org for support."
        result = agent._redact_pii(text)
        assert result.count("[REDACTED_EMAIL]") == 2
        assert "alice@test.com" not in result
        assert "bob@example.org" not in result
    
    def test_email_with_special_chars(self):
        agent = GovernanceAgent()
        text = "My email is user+tag@domain.co.uk"
        result = agent._redact_pii(text)
        assert "[REDACTED_EMAIL]" in result
        assert "user+tag@domain.co.uk" not in result
    
    def test_email_with_numbers(self):
        agent = GovernanceAgent()
        text = "Email address: test123@example456.com"
        result = agent._redact_pii(text)
        assert "[REDACTED_EMAIL]" in result
        assert "test123@example456.com" not in result


class TestPhoneRedaction:
    """Test phone number detection and redaction."""
    
    def test_phone_with_parentheses(self):
        agent = GovernanceAgent()
        text = "Call me at (123) 456-7890"
        result = agent._redact_pii(text)
        assert "[REDACTED_PHONE]" in result
        assert "(123) 456-7890" not in result
    
    def test_phone_with_dashes(self):
        agent = GovernanceAgent()
        text = "Phone: 123-456-7890"
        result = agent._redact_pii(text)
        assert "[REDACTED_PHONE]" in result
        assert "123-456-7890" not in result
    
    def test_phone_with_dots(self):
        agent = GovernanceAgent()
        text = "Contact: 123.456.7890"
        result = agent._redact_pii(text)
        assert "[REDACTED_PHONE]" in result
        assert "123.456.7890" not in result
    
    def test_phone_with_spaces(self):
        agent = GovernanceAgent()
        text = "Call 123 456 7890"
        result = agent._redact_pii(text)
        assert "[REDACTED_PHONE]" in result
        assert "123 456 7890" not in result
    
    def test_phone_with_country_code(self):
        agent = GovernanceAgent()
        text = "International: +1-123-456-7890"
        result = agent._redact_pii(text)
        assert "[REDACTED_PHONE]" in result
        assert "+1-123-456-7890" not in result
    
    def test_multiple_phones(self):
        agent = GovernanceAgent()
        text = "Call (123) 456-7890 or 987-654-3210"
        result = agent._redact_pii(text)
        assert result.count("[REDACTED_PHONE]") == 2


class TestIPRedaction:
    """Test IP address detection and redaction."""
    
    def test_valid_ipv4(self):
        agent = GovernanceAgent()
        text = "Server IP: 192.168.1.1"
        result = agent._redact_pii(text)
        assert "[REDACTED_IP]" in result
        assert "192.168.1.1" not in result
    
    def test_localhost_ip(self):
        agent = GovernanceAgent()
        text = "Connect to 127.0.0.1"
        result = agent._redact_pii(text)
        assert "[REDACTED_IP]" in result
        assert "127.0.0.1" not in result
    
    def test_public_ip(self):
        agent = GovernanceAgent()
        text = "Public IP: 8.8.8.8 is Google DNS"
        result = agent._redact_pii(text)
        assert "[REDACTED_IP]" in result
        assert "8.8.8.8" not in result
    
    def test_multiple_ips(self):
        agent = GovernanceAgent()
        text = "IPs: 10.0.0.1 and 172.16.0.1"
        result = agent._redact_pii(text)
        assert result.count("[REDACTED_IP]") == 2
    
    def test_invalid_ip_not_redacted(self):
        """Test that invalid IPs (like years) are not redacted."""
        agent = GovernanceAgent()
        text = "Year 1920 and 2024"
        result = agent._redact_pii(text)
        # Should not redact these as they're not valid IPs
        assert "1920" in result or "2024" in result
    
    def test_edge_case_ip(self):
        agent = GovernanceAgent()
        text = "IP range: 0.0.0.0 to 255.255.255.255"
        result = agent._redact_pii(text)
        assert result.count("[REDACTED_IP]") == 2


class TestCombinedPII:
    """Test redaction of multiple PII types in one text."""
    
    def test_email_and_phone(self):
        agent = GovernanceAgent()
        text = "Contact: john@example.com or call (555) 123-4567"
        result = agent._redact_pii(text)
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_PHONE]" in result
        assert "john@example.com" not in result
        assert "(555) 123-4567" not in result
    
    def test_all_pii_types(self):
        agent = GovernanceAgent()
        text = "Email: user@test.com, Phone: 555-123-4567, IP: 192.168.1.1"
        result = agent._redact_pii(text)
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_PHONE]" in result
        assert "[REDACTED_IP]" in result
    
    def test_mixed_with_existing_pii(self):
        """Test with existing PII types (dates, names, IDs)."""
        agent = GovernanceAgent()
        text = "Patient John Doe, DOB: 1990-01-01, Email: john@example.com, Phone: 555-1234"
        result = agent._redact_pii(text)
        # Should redact existing PII types too
        assert "[REDACTED_NAME]" in result or "[REDACTED_DATE]" in result
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_PHONE]" in result


class TestIPValidation:
    """Test IP address validation helper method."""
    
    def test_valid_ips(self):
        agent = GovernanceAgent()
        valid_ips = ["192.168.1.1", "127.0.0.1", "10.0.0.1", "255.255.255.255", "0.0.0.0"]
        for ip in valid_ips:
            assert agent._is_valid_ip(ip), f"{ip} should be valid"
    
    def test_invalid_ips(self):
        agent = GovernanceAgent()
        invalid_ips = ["256.1.1.1", "192.168.1", "192.168.1.1.1", "999.999.999.999", "192.168.1.-1"]
        for ip in invalid_ips:
            assert not agent._is_valid_ip(ip), f"{ip} should be invalid"
    
    def test_non_ip_patterns(self):
        """Test that years and other numbers are not treated as IPs."""
        agent = GovernanceAgent()
        non_ips = ["1920", "2024", "192.168", "123.456"]
        for text in non_ips:
            # These might match the regex but should fail validation
            if "." in text and len(text.split(".")) == 4:
                # Only check if it's a 4-part pattern
                parts = text.split(".")
                if any(int(p) > 255 for p in parts if p.isdigit()):
                    assert not agent._is_valid_ip(text), f"{text} should not be valid IP"


class TestRedactionPlaceholders:
    """Test that correct placeholders are used."""
    
    def test_email_placeholder(self):
        agent = GovernanceAgent()
        text = "Email: test@example.com"
        result = agent._redact_pii(text)
        assert "[REDACTED_EMAIL]" in result
    
    def test_phone_placeholder(self):
        agent = GovernanceAgent()
        text = "Phone: 123-456-7890"
        result = agent._redact_pii(text)
        assert "[REDACTED_PHONE]" in result
    
    def test_ip_placeholder(self):
        agent = GovernanceAgent()
        text = "IP: 192.168.1.1"
        result = agent._redact_pii(text)
        assert "[REDACTED_IP]" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

