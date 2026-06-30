import sys
sys.path.append(".")

from agents.agent_04_normalization import (
    normalize_phone, normalize_date, normalize_skill
)

def test_phone():
    assert normalize_phone("9876543210")       == "+919876543210"
    assert normalize_phone("+91-9876543210")   == "+919876543210"
    assert normalize_phone("+1-800-555-0100")  == "+18005550100"
    assert normalize_phone("")                  is None
    assert normalize_phone("123")               is None
    print("✅ Phone normalization passed")

def test_date():
    assert normalize_date("Jan 2024")    == "2024-01"
    assert normalize_date("2024-03-15")  == "2024-03"
    assert normalize_date("03/2022")     == "2022-03"
    assert normalize_date("2025")        == "2025-01"
    assert normalize_date("")            is None
    print("✅ Date normalization passed")

def test_skill():
    assert normalize_skill("ml")         == "Machine Learning"
    assert normalize_skill("JS")         == "JavaScript"
    assert normalize_skill("py")         == "Python"
    assert normalize_skill("k8s")        == "Kubernetes"
    assert normalize_skill("UnknownLib") == "Unknownlib"
    assert normalize_skill("rest apis")  == "REST APIs"
    assert normalize_skill("VSCode")     == "VS Code"
    assert normalize_skill("OpenCL")     == "OpenCL"
    assert normalize_skill("cuda")       == "CUDA"
    assert normalize_skill("hibernate")  == "JPA/Hibernate"
    print("✅ Skill normalization passed")

if __name__ == "__main__":
    test_phone()
    test_date()
    test_skill()
    print("\n✅ All tests passed")